"""
Append-only log writer for VeriChain.

Writes decision records to .vlog files with:
- Binary format for efficiency
- Append-only semantics
- Segment-based organization
- Crash recovery support
"""

import os
import struct
import fcntl
from typing import Optional
from pathlib import Path
from datetime import datetime


class LogWriter:
    """
    Writes decision records to append-only .vlog files.
    
    File format:
    [4 bytes: record length]
    [32 bytes: packet hash (SHA3-256)]
    [8 bytes: timestamp (Unix microseconds)]
    [32 bytes: key_id (padded)]
    [36 bytes: decision_id (UUID)]
    
    Total: 112 bytes per record
    """
    
    RECORD_SIZE = 112
    SEGMENT_SIZE = 10000  # Records per segment
    
    def __init__(self, log_dir: str = "./ledger"):
        """
        Initialize log writer.
        
        Args:
            log_dir: Directory for log files
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self.current_segment: Optional[str] = None
        self.current_file = None
        self.record_count = 0
    
    def _get_segment_name(self) -> str:
        """Generate segment filename based on current timestamp."""
        timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
        return f"seg-{timestamp}.vlog"
    
    def _open_segment(self):
        """Open a new segment file."""
        if self.current_file:
            self.current_file.close()
        
        self.current_segment = self._get_segment_name()
        segment_path = self.log_dir / self.current_segment
        
        # Open in append+binary mode
        self.current_file = open(segment_path, 'ab')
        
        # Lock file for exclusive access
        fcntl.flock(self.current_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        
        self.record_count = 0
    
    def append(
        self,
        decision_id: str,
        packet_hash: str,
        timestamp: str,
        key_id: str
    ):
        """
        Append a record to the log.
        
        Args:
            decision_id: UUID of decision
            packet_hash: SHA3-256 hash of packet (hex string)
            timestamp: ISO 8601 timestamp
            key_id: Key identifier
        """
        # Open new segment if needed
        if self.current_file is None or self.record_count >= self.SEGMENT_SIZE:
            self._open_segment()
        
        # Convert timestamp to Unix microseconds
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        timestamp_us = int(dt.timestamp() * 1_000_000)
        
        # Convert hash from hex to bytes
        hash_bytes = bytes.fromhex(packet_hash)
        
        # Pad key_id to 32 bytes
        key_id_bytes = key_id.encode('utf-8')[:32].ljust(32, b'\x00')
        
        # Convert decision_id to bytes
        decision_id_bytes = decision_id.encode('utf-8')[:36].ljust(36, b'\x00')
        
        # Pack record
        record = struct.pack(
            '<I32sQ32s36s',
            self.RECORD_SIZE,  # Record length
            hash_bytes,         # Packet hash
            timestamp_us,       # Timestamp
            key_id_bytes,       # Key ID
            decision_id_bytes   # Decision ID
        )
        
        # Write and flush immediately (durability)
        self.current_file.write(record)
        self.current_file.flush()
        os.fsync(self.current_file.fileno())
        
        self.record_count += 1
    
    def close(self):
        """Close current segment."""
        if self.current_file:
            fcntl.flock(self.current_file.fileno(), fcntl.LOCK_UN)
            self.current_file.close()
            self.current_file = None
    
    def __del__(self):
        """Cleanup on deletion."""
        self.close()


class LogReader:
    """
    Reads records from .vlog files.
    
    Used for verification and auditing.
    """
    
    def __init__(self, log_dir: str = "./ledger"):
        """
        Initialize log reader.
        
        Args:
            log_dir: Directory containing log files
        """
        self.log_dir = Path(log_dir)
    
    def read_segment(self, segment_name: str):
        """
        Read all records from a segment.
        
        Args:
            segment_name: Segment filename
            
        Yields:
            Dictionary with record data
        """
        segment_path = self.log_dir / segment_name
        
        with open(segment_path, 'rb') as f:
            while True:
                # Read record
                data = f.read(LogWriter.RECORD_SIZE)
                if len(data) < LogWriter.RECORD_SIZE:
                    break
                
                # Unpack
                record_len, hash_bytes, timestamp_us, key_id_bytes, decision_id_bytes = struct.unpack(
                    '<I32sQ32s36s',
                    data
                )
                
                # Convert to readable format
                yield {
                    'decision_id': decision_id_bytes.rstrip(b'\x00').decode('utf-8'),
                    'packet_hash': hash_bytes.hex(),
                    'timestamp_us': timestamp_us,
                    'key_id': key_id_bytes.rstrip(b'\x00').decode('utf-8')
                }
    
    def list_segments(self):
        """
        List all segment files.
        
        Returns:
            List of segment filenames
        """
        return sorted([f.name for f in self.log_dir.glob('seg-*.vlog')])
    
    def verify_segment_integrity(self, segment_name: str) -> bool:
        """
        Verify that a segment file is not corrupted.
        
        Args:
            segment_name: Segment filename
            
        Returns:
            True if segment is valid
        """
        segment_path = self.log_dir / segment_name
        
        try:
            file_size = segment_path.stat().st_size
            
            # File size must be multiple of record size
            if file_size % LogWriter.RECORD_SIZE != 0:
                return False
            
            # Try to read all records
            for _ in self.read_segment(segment_name):
                pass
            
            return True
            
        except Exception:
            return False

"""
Sealed Ledger Writer for VeriChain.

Implements tamper-proof segment sealing with:
- Segment checksum
- Cryptographic signature of segment
- Signed timestamp
- Integrity verification

Each .vlog segment is sealed upon completion, making any
modification detectable.
"""

import os
import struct
import fcntl
import hashlib
import json
from typing import Optional, Dict, Any, List
from pathlib import Path
from datetime import datetime, timezone

from .signer import ECDSASigner


class SealedSegment:
    """
    Represents a sealed ledger segment with integrity protection.
    """
    
    def __init__(self, segment_id: str, checksum: str, signature: bytes, 
                 timestamp: str, record_count: int, signer_key_id: str):
        self.segment_id = segment_id
        self.checksum = checksum
        self.signature = signature
        self.timestamp = timestamp
        self.record_count = record_count
        self.signer_key_id = signer_key_id
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'segment_id': self.segment_id,
            'checksum': self.checksum,
            'signature': self.signature.hex(),
            'timestamp': self.timestamp,
            'record_count': self.record_count,
            'signer_key_id': self.signer_key_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """Create from dictionary."""
        return cls(
            segment_id=data['segment_id'],
            checksum=data['checksum'],
            signature=bytes.fromhex(data['signature']),
            timestamp=data['timestamp'],
            record_count=data['record_count'],
            signer_key_id=data['signer_key_id']
        )


class SealedLogWriter:
    """
    Writes decision records to sealed, tamper-proof .vlog segments.
    
    Each segment is sealed with:
    1. SHA3-256 checksum of all records
    2. ECDSA signature of checksum
    3. Cryptographically signed timestamp
    4. Seal metadata file (.seal)
    """
    
    RECORD_SIZE = 112
    SEGMENT_SIZE = 10000  # Records per segment
    
    def __init__(self, log_dir: str = "./ledger", signer: Optional[ECDSASigner] = None):
        """
        Initialize sealed log writer.
        
        Args:
            log_dir: Directory for log files
            signer: Signer for segment sealing (required for production)
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self.signer = signer
        if not signer:
            # Create default signer for development
            self.signer = ECDSASigner('ledger-seal-key')
        
        self.current_segment: Optional[str] = None
        self.current_file = None
        self.record_count = 0
        self.segment_data = bytearray()  # Buffer for checksum calculation
    
    def _get_segment_name(self) -> str:
        """Generate segment filename based on current timestamp."""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        return f"seg-{timestamp}.vlog"
    
    def _open_segment(self):
        """Open a new segment file."""
        if self.current_file:
            self._seal_segment()
            self.current_file.close()
        
        self.current_segment = self._get_segment_name()
        segment_path = self.log_dir / self.current_segment
        
        # Open in append+binary mode
        self.current_file = open(segment_path, 'ab')
        
        # Lock file for exclusive access
        fcntl.flock(self.current_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        
        self.record_count = 0
        self.segment_data = bytearray()
    
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
        
        # Add to segment buffer for checksum
        self.segment_data.extend(record)
        
        # Write and flush immediately (durability)
        self.current_file.write(record)
        self.current_file.flush()
        os.fsync(self.current_file.fileno())
        
        self.record_count += 1
    
    def _seal_segment(self):
        """
        Seal current segment with cryptographic signature.
        
        Creates a .seal file containing:
        - Segment checksum (SHA3-256)
        - Signature of checksum
        - Timestamp
        - Record count
        """
        if not self.current_segment or self.record_count == 0:
            return
        
        # Calculate checksum of entire segment
        checksum = hashlib.sha3_256(self.segment_data).hexdigest()
        
        # Get current timestamp
        seal_timestamp = datetime.now(timezone.utc).isoformat() + 'Z'
        
        # Create seal data
        seal_data = {
            'segment_id': self.current_segment,
            'checksum': checksum,
            'timestamp': seal_timestamp,
            'record_count': self.record_count,
            'signer_key_id': self.signer.get_key_id()
        }
        
        # Sign the checksum
        seal_bytes = json.dumps(seal_data, sort_keys=True).encode('utf-8')
        signature = self.signer.sign(seal_bytes)
        
        # Create sealed segment
        sealed = SealedSegment(
            segment_id=self.current_segment,
            checksum=checksum,
            signature=signature,
            timestamp=seal_timestamp,
            record_count=self.record_count,
            signer_key_id=self.signer.get_key_id()
        )
        
        # Save seal file
        seal_path = self.log_dir / f"{self.current_segment}.seal"
        with open(seal_path, 'w') as f:
            json.dump(sealed.to_dict(), f, indent=2)
        
        print(f"✅ Segment sealed: {self.current_segment}")
        print(f"   Checksum: {checksum[:32]}...")
        print(f"   Records: {self.record_count}")
    
    def close(self):
        """Close current segment and seal it."""
        if self.current_file:
            self._seal_segment()
            fcntl.flock(self.current_file.fileno(), fcntl.LOCK_UN)
            self.current_file.close()
            self.current_file = None
    
    def __del__(self):
        """Cleanup on deletion."""
        self.close()


class SealedLogVerifier:
    """
    Verifies integrity of sealed ledger segments.
    """
    
    def __init__(self, log_dir: str = "./ledger"):
        """
        Initialize verifier.
        
        Args:
            log_dir: Directory containing log files
        """
        self.log_dir = Path(log_dir)
    
    def verify_segment(self, segment_name: str, signer: Optional[ECDSASigner] = None) -> Dict[str, Any]:
        """
        Verify integrity of a sealed segment.
        
        Args:
            segment_name: Segment filename
            signer: Signer for verification (must match seal signer)
            
        Returns:
            Verification report
        """
        report = {
            'valid': False,
            'segment': segment_name,
            'errors': [],
            'details': {}
        }
        
        segment_path = self.log_dir / segment_name
        seal_path = self.log_dir / f"{segment_name}.seal"
        
        # Check files exist
        if not segment_path.exists():
            report['errors'].append(f"Segment file not found: {segment_name}")
            return report
        
        if not seal_path.exists():
            report['errors'].append(f"Seal file not found: {segment_name}.seal")
            return report
        
        try:
            # Load seal
            with open(seal_path, 'r') as f:
                seal_data = json.load(f)
            
            sealed = SealedSegment.from_dict(seal_data)
            
            # Read segment data
            with open(segment_path, 'rb') as f:
                segment_data = f.read()
            
            # Calculate checksum
            calculated_checksum = hashlib.sha3_256(segment_data).hexdigest()
            
            # Verify checksum
            if calculated_checksum != sealed.checksum:
                report['errors'].append("Checksum mismatch - segment has been tampered!")
                report['details']['expected_checksum'] = sealed.checksum
                report['details']['calculated_checksum'] = calculated_checksum
                return report
            
            # Verify signature
            if signer:
                seal_bytes = json.dumps({
                    'segment_id': sealed.segment_id,
                    'checksum': sealed.checksum,
                    'timestamp': sealed.timestamp,
                    'record_count': sealed.record_count,
                    'signer_key_id': sealed.signer_key_id
                }, sort_keys=True).encode('utf-8')
                
                if not signer.verify(seal_bytes, sealed.signature):
                    report['errors'].append("Signature verification failed")
                    return report
            
            # All checks passed
            report['valid'] = True
            report['details'] = {
                'checksum': sealed.checksum,
                'timestamp': sealed.timestamp,
                'record_count': sealed.record_count,
                'signer_key_id': sealed.signer_key_id
            }
            
        except Exception as e:
            report['errors'].append(f"Verification error: {str(e)}")
        
        return report
    
    def verify_all_segments(self) -> List[Dict[str, Any]]:
        """
        Verify all sealed segments in ledger.
        
        Returns:
            List of verification reports
        """
        reports = []
        
        for segment_file in sorted(self.log_dir.glob("seg-*.vlog")):
            report = self.verify_segment(segment_file.name)
            reports.append(report)
        
        return reports
    
    def detect_tampering(self) -> List[str]:
        """
        Detect any tampered segments.
        
        Returns:
            List of tampered segment names
        """
        tampered = []
        
        reports = self.verify_all_segments()
        for report in reports:
            if not report['valid']:
                tampered.append(report['segment'])
        
        return tampered


if __name__ == '__main__':
    # Test sealed ledger
    print("Testing Sealed Ledger...")
    
    signer = ECDSASigner('test-seal-key')
    writer = SealedLogWriter('./test_sealed_ledger', signer)
    
    # Write test records
    for i in range(5):
        writer.append(
            decision_id=f'test-{i:03d}',
            packet_hash='a' * 64,
            timestamp='2025-10-18T09:00:00Z',
            key_id='test-key'
        )
    
    writer.close()
    
    # Verify
    verifier = SealedLogVerifier('./test_sealed_ledger')
    reports = verifier.verify_all_segments()
    
    for report in reports:
        if report['valid']:
            print(f"✅ {report['segment']}: VALID")
        else:
            print(f"❌ {report['segment']}: INVALID")
            for error in report['errors']:
                print(f"   - {error}")

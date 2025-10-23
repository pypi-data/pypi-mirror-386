"""
Packet packager - creates .vchain containers for legal-grade evidence.

A .vchain container is a ZIP file containing:
- packet.json (canonical proof packet)
- packet.sig (signature of packet)
- explanation.txt (optional human-readable explanation)
- explanation.sig (signature of explanation)
- manifest.json (metadata and hashes)
- anchor_receipt.json (Merkle proof, added later by sealer)
"""

import os
import json
import zipfile
import base64
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime

from .canonicalization import canonicalize_packet, canonicalize_to_string
from .hasher import sha3_hash
from .signer import Signer


class PacketPackager:
    """
    Creates forensic-grade .vchain containers.
    
    These containers can be used as legal evidence and verified offline.
    """
    
    def __init__(self, output_dir: str = "./packets"):
        """
        Initialize packager.
        
        Args:
            output_dir: Directory for .vchain files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def create_container(
        self,
        packet: Dict[str, Any],
        signature: bytes,
        signer: Signer,
        explanation_text: Optional[str] = None,
        anchor_receipt: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create a .vchain container.
        
        Args:
            packet: Proof packet dictionary
            signature: Signature bytes
            signer: Signer instance (for public key)
            explanation_text: Optional human-readable explanation
            anchor_receipt: Optional Merkle anchor receipt (added by sealer)
            
        Returns:
            Path to created .vchain file
        """
        decision_id = packet['decision_id']
        container_name = f"{decision_id}.vchain"
        container_path = self.output_dir / container_name
        
        # Canonicalize packet
        canonical_packet = canonicalize_to_string(packet)
        
        # Create ZIP container
        with zipfile.ZipFile(container_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            # 1. Add packet.json
            zf.writestr('packet.json', canonical_packet)
            
            # 2. Add packet.sig
            zf.writestr('packet.sig', base64.b64encode(signature).decode('utf-8'))
            
            # 3. Add public key
            zf.writestr('public_key.pem', signer.get_public_key_pem())
            
            # 4. Add explanation if provided
            if explanation_text:
                zf.writestr('explanation.txt', explanation_text)
                
                # Sign explanation
                exp_sig = signer.sign(explanation_text.encode('utf-8'))
                zf.writestr('explanation.sig', base64.b64encode(exp_sig).decode('utf-8'))
            
            # 5. Add anchor receipt if provided
            if anchor_receipt:
                anchor_json = json.dumps(anchor_receipt, indent=2)
                zf.writestr('anchor_receipt.json', anchor_json)
            
            # 6. Create manifest
            manifest = self._create_manifest(
                packet=packet,
                signature=signature,
                explanation_text=explanation_text,
                anchor_receipt=anchor_receipt,
                signer=signer
            )
            
            manifest_json = json.dumps(manifest, indent=2)
            zf.writestr('manifest.json', manifest_json)
        
        return str(container_path)
    
    def _create_manifest(
        self,
        packet: Dict[str, Any],
        signature: bytes,
        explanation_text: Optional[str],
        anchor_receipt: Optional[Dict[str, Any]],
        signer: Signer
    ) -> Dict[str, Any]:
        """
        Create manifest with metadata and hashes.
        
        Args:
            packet: Proof packet
            signature: Signature bytes
            explanation_text: Optional explanation
            anchor_receipt: Optional anchor receipt
            signer: Signer instance
            
        Returns:
            Manifest dictionary
        """
        canonical_packet = canonicalize_to_string(packet)
        
        manifest = {
            'version': '1.0',
            'created_at': datetime.utcnow().isoformat() + 'Z',
            'decision_id': packet['decision_id'],
            'artifacts': {
                'packet': {
                    'hash': sha3_hash(canonical_packet),
                    'size': len(canonical_packet)
                },
                'signature': {
                    'algorithm': 'ECDSA-SHA256',
                    'key_id': signer.get_key_id(),
                    'hash': sha3_hash(signature)
                }
            },
            'issuer': packet['issuer'],
            'model': packet['model']
        }
        
        # Add explanation metadata if present
        if explanation_text:
            manifest['artifacts']['explanation'] = {
                'hash': sha3_hash(explanation_text),
                'size': len(explanation_text)
            }
        
        # Add anchor metadata if present
        if anchor_receipt:
            manifest['artifacts']['anchor_receipt'] = {
                'merkle_root': anchor_receipt.get('root'),
                'anchor_time': anchor_receipt.get('anchor_time')
            }
        
        return manifest
    
    def verify_container(self, container_path: str) -> Dict[str, Any]:
        """
        Verify integrity of a .vchain container.
        
        Args:
            container_path: Path to .vchain file
            
        Returns:
            Verification report
        """
        report = {
            'valid': False,
            'errors': [],
            'warnings': [],
            'details': {}
        }
        
        try:
            with zipfile.ZipFile(container_path, 'r') as zf:
                # Check required files
                required_files = ['packet.json', 'packet.sig', 'manifest.json']
                for filename in required_files:
                    if filename not in zf.namelist():
                        report['errors'].append(f"Missing required file: {filename}")
                        return report
                
                # Read files
                packet_json = zf.read('packet.json').decode('utf-8')
                signature_b64 = zf.read('packet.sig').decode('utf-8')
                manifest_json = zf.read('manifest.json').decode('utf-8')
                
                # Parse
                packet = json.loads(packet_json)
                signature = base64.b64decode(signature_b64)
                manifest = json.loads(manifest_json)
                
                # Verify packet hash
                packet_hash = sha3_hash(packet_json)
                expected_hash = manifest['artifacts']['packet']['hash']
                
                if packet_hash != expected_hash:
                    report['errors'].append("Packet hash mismatch")
                    return report
                
                # Verify signature hash
                sig_hash = sha3_hash(signature)
                expected_sig_hash = manifest['artifacts']['signature']['hash']
                
                if sig_hash != expected_sig_hash:
                    report['errors'].append("Signature hash mismatch")
                    return report
                
                # Check for explanation
                if 'explanation.txt' in zf.namelist():
                    explanation = zf.read('explanation.txt').decode('utf-8')
                    exp_hash = sha3_hash(explanation)
                    expected_exp_hash = manifest['artifacts']['explanation']['hash']
                    
                    if exp_hash != expected_exp_hash:
                        report['errors'].append("Explanation hash mismatch")
                        return report
                
                # All checks passed
                report['valid'] = True
                report['details'] = {
                    'decision_id': packet['decision_id'],
                    'timestamp': packet['timestamp_utc'],
                    'issuer': packet['issuer'],
                    'model': packet['model'],
                    'key_id': manifest['artifacts']['signature']['key_id']
                }
                
        except Exception as e:
            report['errors'].append(f"Error reading container: {str(e)}")
        
        return report
    
    def extract_packet(self, container_path: str) -> Dict[str, Any]:
        """
        Extract proof packet from container.
        
        Args:
            container_path: Path to .vchain file
            
        Returns:
            Proof packet dictionary
        """
        with zipfile.ZipFile(container_path, 'r') as zf:
            packet_json = zf.read('packet.json').decode('utf-8')
            return json.loads(packet_json)
    
    def add_anchor_receipt(
        self,
        container_path: str,
        anchor_receipt: Dict[str, Any]
    ):
        """
        Add anchor receipt to existing container.
        
        This is called by the sealer after Merkle anchoring.
        
        Args:
            container_path: Path to .vchain file
            anchor_receipt: Anchor receipt dictionary
        """
        # Read existing container
        temp_path = container_path + '.tmp'
        
        with zipfile.ZipFile(container_path, 'r') as zf_in:
            with zipfile.ZipFile(temp_path, 'w', zipfile.ZIP_DEFLATED) as zf_out:
                # Copy all existing files
                for item in zf_in.infolist():
                    data = zf_in.read(item.filename)
                    zf_out.writestr(item, data)
                
                # Add anchor receipt
                anchor_json = json.dumps(anchor_receipt, indent=2)
                zf_out.writestr('anchor_receipt.json', anchor_json)
                
                # Update manifest
                manifest_data = zf_in.read('manifest.json').decode('utf-8')
                manifest = json.loads(manifest_data)
                
                manifest['artifacts']['anchor_receipt'] = {
                    'merkle_root': anchor_receipt.get('root'),
                    'anchor_time': anchor_receipt.get('anchor_time')
                }
                
                manifest_json = json.dumps(manifest, indent=2)
                zf_out.writestr('manifest.json', manifest_json)
        
        # Replace original with updated version
        os.replace(temp_path, container_path)

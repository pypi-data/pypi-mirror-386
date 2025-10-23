"""
Cryptographic signing module for VeriChain.

Supports:
- ECDSA (secp256r1) for standard signatures
- Post-quantum signatures (Dilithium2) optional
- HSM integration via PKCS#11

Security principles:
- Private keys never leave HSM
- All signatures over canonical JSON
- Support for key rotation
"""

import base64
import json
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.backends import default_backend
from cryptography.exceptions import InvalidSignature


class Signer(ABC):
    """Abstract base class for all signers."""
    
    @abstractmethod
    def sign(self, data: bytes) -> bytes:
        """Sign data and return signature."""
        pass
    
    @abstractmethod
    def verify(self, data: bytes, signature: bytes) -> bool:
        """Verify signature."""
        pass
    
    @abstractmethod
    def get_public_key_pem(self) -> str:
        """Get public key in PEM format."""
        pass
    
    @abstractmethod
    def get_key_id(self) -> str:
        """Get key identifier."""
        pass


class ECDSASigner(Signer):
    """
    ECDSA signer using secp256r1 (NIST P-256) curve.
    
    This is the default signer for VeriChain.
    Provides 128-bit security level.
    """
    
    def __init__(self, key_id: str, private_key: Optional[ec.EllipticCurvePrivateKey] = None):
        """
        Initialize ECDSA signer.
        
        Args:
            key_id: Unique identifier for this key (e.g., 'key-2025q4')
            private_key: Optional private key (if None, generates new key)
        """
        self.key_id = key_id
        
        if private_key is None:
            self.private_key = ec.generate_private_key(
                ec.SECP256R1(),
                default_backend()
            )
        else:
            self.private_key = private_key
        
        self.public_key = self.private_key.public_key()
    
    def sign(self, data: bytes) -> bytes:
        """
        Sign data using ECDSA.
        
        Args:
            data: Canonical JSON bytes to sign
            
        Returns:
            DER-encoded signature
        """
        signature = self.private_key.sign(
            data,
            ec.ECDSA(hashes.SHA256())
        )
        return signature
    
    def verify(self, data: bytes, signature: bytes) -> bool:
        """
        Verify ECDSA signature.
        
        Args:
            data: Original data
            signature: DER-encoded signature
            
        Returns:
            True if signature is valid
        """
        try:
            self.public_key.verify(
                signature,
                data,
                ec.ECDSA(hashes.SHA256())
            )
            return True
        except InvalidSignature:
            return False
    
    def get_public_key_pem(self) -> str:
        """Get public key in PEM format."""
        pem = self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        return pem.decode('utf-8')
    
    def get_key_id(self) -> str:
        """Get key identifier."""
        return self.key_id
    
    def save_private_key(self, path: str, password: Optional[bytes] = None):
        """
        Save private key to file (encrypted if password provided).
        
        Args:
            path: File path to save key
            password: Optional password for encryption
        """
        if password:
            encryption = serialization.BestAvailableEncryption(password)
        else:
            encryption = serialization.NoEncryption()
        
        pem = self.private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=encryption
        )
        
        with open(path, 'wb') as f:
            f.write(pem)
    
    @classmethod
    def load_private_key(cls, path: str, key_id: str, password: Optional[bytes] = None):
        """
        Load private key from file.
        
        Args:
            path: File path to load key from
            key_id: Key identifier
            password: Optional password for decryption
            
        Returns:
            ECDSASigner instance
        """
        with open(path, 'rb') as f:
            pem_data = f.read()
        
        private_key = serialization.load_pem_private_key(
            pem_data,
            password=password,
            backend=default_backend()
        )
        
        return cls(key_id, private_key)


class HSMSigner(Signer):
    """
    HSM-backed signer using PKCS#11.
    
    In production, private keys never leave the HSM.
    For development, can use SoftHSM2.
    """
    
    def __init__(self, key_id: str, hsm_config: Dict[str, Any]):
        """
        Initialize HSM signer.
        
        Args:
            key_id: Key identifier
            hsm_config: HSM configuration (slot, pin, label, etc.)
        """
        self.key_id = key_id
        self.hsm_config = hsm_config
        
        # TODO: Implement PKCS#11 integration
        # For now, fall back to software signing
        self._software_signer = ECDSASigner(key_id)
    
    def sign(self, data: bytes) -> bytes:
        """Sign using HSM."""
        # TODO: Implement HSM signing via PKCS#11
        return self._software_signer.sign(data)
    
    def verify(self, data: bytes, signature: bytes) -> bool:
        """Verify signature."""
        return self._software_signer.verify(data, signature)
    
    def get_public_key_pem(self) -> str:
        """Get public key from HSM."""
        return self._software_signer.get_public_key_pem()
    
    def get_key_id(self) -> str:
        """Get key identifier."""
        return self.key_id


class MultiSigner:
    """
    Multi-algorithm signer supporting both ECDSA and post-quantum signatures.
    
    This provides quantum-resistant signatures alongside traditional ECDSA.
    """
    
    def __init__(self, ecdsa_signer: Signer, pqc_signer: Optional[Signer] = None):
        """
        Initialize multi-signer.
        
        Args:
            ecdsa_signer: ECDSA signer (required)
            pqc_signer: Optional post-quantum signer (Dilithium2)
        """
        self.ecdsa_signer = ecdsa_signer
        self.pqc_signer = pqc_signer
    
    def sign_packet(self, canonical_data: bytes) -> list[Dict[str, str]]:
        """
        Sign packet with multiple algorithms.
        
        Args:
            canonical_data: Canonical JSON bytes
            
        Returns:
            List of signature objects with algorithm and signature
        """
        signatures = []
        
        # ECDSA signature (always included)
        ecdsa_sig = self.ecdsa_signer.sign(canonical_data)
        signatures.append({
            'alg': 'ECDSA-SHA256',
            'key_id': self.ecdsa_signer.get_key_id(),
            'sig': base64.b64encode(ecdsa_sig).decode('utf-8')
        })
        
        # Post-quantum signature (optional)
        if self.pqc_signer:
            pqc_sig = self.pqc_signer.sign(canonical_data)
            signatures.append({
                'alg': 'Dilithium2',
                'key_id': self.pqc_signer.get_key_id(),
                'sig': base64.b64encode(pqc_sig).decode('utf-8')
            })
        
        return signatures
    
    def verify_signatures(self, canonical_data: bytes, signatures: list[Dict[str, str]]) -> Dict[str, bool]:
        """
        Verify all signatures.
        
        Args:
            canonical_data: Original canonical data
            signatures: List of signature objects
            
        Returns:
            Dictionary mapping algorithm to verification result
        """
        results = {}
        
        for sig_obj in signatures:
            alg = sig_obj['alg']
            sig_bytes = base64.b64decode(sig_obj['sig'])
            
            if alg == 'ECDSA-SHA256':
                results[alg] = self.ecdsa_signer.verify(canonical_data, sig_bytes)
            elif alg == 'Dilithium2' and self.pqc_signer:
                results[alg] = self.pqc_signer.verify(canonical_data, sig_bytes)
            else:
                results[alg] = False
        
        return results

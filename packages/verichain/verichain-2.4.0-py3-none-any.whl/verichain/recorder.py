"""
Decision recorder - the main interface for capturing AI decisions.

Uses context manager pattern for explicit control and fail-safe behavior.
"""

import uuid
import json
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from contextlib import contextmanager

from .hasher import sha3_hash, hash_input
from .canonicalization import canonicalize_packet, validate_packet_structure
from .signer import Signer, ECDSASigner
from .log_writer import LogWriter
from .packager import PacketPackager


class DecisionRecorder:
    """
    Records AI decisions with cryptographic verification.
    
    This class captures all metadata about a decision and creates
    a verifiable proof packet.
    """
    
    def __init__(
        self,
        issuer: str,
        node: str,
        model_id: str,
        model_version: str,
        signing_key_id: str,
        signer: Optional[Signer] = None,
        log_writer: Optional[LogWriter] = None,
        packager: Optional[PacketPackager] = None
    ):
        """
        Initialize decision recorder.
        
        Args:
            issuer: Entity identifier (e.g., 'bank001')
            node: Node identifier (e.g., 'scoring-node-1')
            model_id: Model identifier (e.g., 'credit_score')
            model_version: Model version (e.g., 'v2.4')
            signing_key_id: Key identifier for signing
            signer: Optional custom signer (creates default if None)
            log_writer: Optional log writer (creates default if None)
            packager: Optional packager (creates default if None)
        """
        self.issuer = issuer
        self.node = node
        self.model_id = model_id
        self.model_version = model_version
        self.signing_key_id = signing_key_id
        
        # Generate unique decision ID
        self.decision_id = str(uuid.uuid4())
        self.timestamp_utc = datetime.now(timezone.utc).isoformat()
        
        # Initialize components
        self.signer = signer or ECDSASigner(signing_key_id)
        self.log_writer = log_writer or LogWriter()
        self.packager = packager or PacketPackager()
        
        # Decision data (to be filled)
        self.input_hash: Optional[str] = None
        self.decision_outcome: Optional[str] = None
        self.risk_score: Optional[int] = None
        self.explanation_hash: Optional[str] = None
        self.explanation_method: Optional[str] = None
        self.explanation_seed: Optional[int] = None
        self.explanation_text: Optional[str] = None
        
        # Error tracking
        self.error: Optional[Exception] = None
    
    def log_input_hash(self, input_hash: str):
        """
        Log hash of input data.
        
        Args:
            input_hash: SHA3-256 hash of input
        """
        self.input_hash = input_hash
    
    def log_input(self, input_data: Any):
        """
        Log input data (will be hashed automatically).
        
        Args:
            input_data: Input data to hash
        """
        self.input_hash = hash_input(input_data)
    
    def log_decision(self, outcome: str, risk_score: int):
        """
        Log decision outcome.
        
        Args:
            outcome: Decision outcome (e.g., 'approve', 'reject')
            risk_score: Risk score (0-100)
        """
        self.decision_outcome = outcome
        self.risk_score = risk_score
    
    def log_explanation(
        self,
        hash: str,
        method: str,
        seed: int,
        text: Optional[str] = None
    ):
        """
        Log explanation metadata.
        
        Args:
            hash: SHA3-256 hash of explanation
            method: Explanation method (e.g., 'SHAP_0.42')
            seed: Random seed for determinism
            text: Optional human-readable explanation text
        """
        self.explanation_hash = hash
        self.explanation_method = method
        self.explanation_seed = seed
        self.explanation_text = text
    
    def _build_packet(self) -> Dict[str, Any]:
        """
        Build proof packet from recorded data.
        
        Returns:
            Proof packet dictionary
        """
        packet = {
            'schema_ver': '1.0',
            'decision_id': self.decision_id,
            'timestamp_utc': self.timestamp_utc,
            'issuer': {
                'entity_id': self.issuer,
                'node_id': self.node
            },
            'model': {
                'id': self.model_id,
                'version': self.model_version
            },
            'input_hash': self.input_hash,
            'decision': {
                'outcome': self.decision_outcome,
                'risk_score': self.risk_score
            },
            'explanation': {
                'hash': self.explanation_hash,
                'method': self.explanation_method,
                'seed': self.explanation_seed,
                'text': self.explanation_text if self.explanation_text else ''
            },
            'signing_key_id': self.signing_key_id
        }
        
        return packet
    
    def sign_and_write(self) -> Optional[str]:
        """
        Sign packet and write to log.
        
        This is the final step that:
        1. Validates packet structure
        2. Canonicalizes packet
        3. Signs with cryptographic key
        4. Writes to append-only log
        5. Creates .vchain container
        
        Returns:
            Path to .vchain container, or None if error
        """
        try:
            # Build packet
            packet = self._build_packet()
            
            # Validate structure
            is_valid, error_msg = validate_packet_structure(packet)
            if not is_valid:
                raise ValueError(f"Invalid packet structure: {error_msg}")
            
            # Canonicalize
            canonical_data = canonicalize_packet(packet)
            
            # Sign
            signature = self.signer.sign(canonical_data)
            
            # Write to log
            self.log_writer.append(
                decision_id=self.decision_id,
                packet_hash=sha3_hash(canonical_data),
                timestamp=self.timestamp_utc,
                key_id=self.signing_key_id
            )
            
            # Create .vchain container
            container_path = self.packager.create_container(
                packet=packet,
                signature=signature,
                signer=self.signer,
                explanation_text=self.explanation_text
            )
            
            return container_path
            
        except Exception as e:
            # Fail-safe: log error but don't block decision
            self.error = e
            print(f"[VeriChain] Error recording decision: {e}")
            # TODO: Queue for retry
            return None
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - auto-sign if no error."""
        if exc_type is None and self.error is None:
            # Only auto-sign if everything went well
            pass
        return False  # Don't suppress exceptions


@contextmanager
def recorder(
    issuer: str,
    node: str,
    model_id: str,
    model_version: str,
    signing_key_id: str,
    **kwargs
):
    """
    Context manager for recording decisions.
    
    Usage:
        with verichain.recorder(
            issuer="bank001",
            node="scoring-node-1",
            model_id="credit_score",
            model_version="v2.4",
            signing_key_id="key-2025q4"
        ) as rec:
            result = model.predict(x)
            rec.log_input(x)
            rec.log_decision(outcome="reject", risk_score=82)
            rec.log_explanation(hash=exp_hash, method="SHAP", seed=42)
            rec.sign_and_write()
    
    Args:
        issuer: Entity identifier
        node: Node identifier
        model_id: Model identifier
        model_version: Model version
        signing_key_id: Key identifier
        **kwargs: Additional arguments for DecisionRecorder
    
    Yields:
        DecisionRecorder instance
    """
    rec = DecisionRecorder(
        issuer=issuer,
        node=node,
        model_id=model_id,
        model_version=model_version,
        signing_key_id=signing_key_id,
        **kwargs
    )
    
    try:
        yield rec
    finally:
        # Cleanup if needed
        pass

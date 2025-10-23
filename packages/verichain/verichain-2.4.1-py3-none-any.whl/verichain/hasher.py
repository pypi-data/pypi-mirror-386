"""
Cryptographic hashing utilities for VeriChain.

Uses SHA3-256 for all hashing operations to ensure:
- Deterministic output
- Collision resistance
- NIST-approved cryptographic strength
"""

import hashlib
import json
from typing import Any, Union


def sha3_hash(data: Union[str, bytes]) -> str:
    """
    Compute SHA3-256 hash of input data.
    
    Args:
        data: String or bytes to hash
        
    Returns:
        Hex-encoded hash string (64 characters)
    """
    if isinstance(data, str):
        data = data.encode('utf-8')
    
    hasher = hashlib.sha3_256()
    hasher.update(data)
    return hasher.hexdigest()


def hash_input(input_data: Any) -> str:
    """
    Hash input data for a decision.
    
    For privacy compliance, we never store raw input data.
    Only the hash is recorded in the proof packet.
    
    Args:
        input_data: Any serializable input data
        
    Returns:
        SHA3-256 hash of the canonical JSON representation
    """
    if isinstance(input_data, (str, bytes)):
        return sha3_hash(input_data)
    
    # For complex objects, serialize to canonical JSON first
    canonical = json.dumps(input_data, sort_keys=True, separators=(',', ':'))
    return sha3_hash(canonical)


def hash_explanation(
    explanation_content: str,
    method: str,
    seed: int
) -> str:
    """
    Hash explanation content deterministically.
    
    Combines explanation text, method, and seed to create a
    deterministic hash that can be verified later.
    
    Args:
        explanation_content: The explanation text or vector
        method: Explanation method (e.g., 'SHAP_0.42')
        seed: Random seed used for explanation generation
        
    Returns:
        SHA3-256 hash of the combined content
    """
    combined = json.dumps({
        'content': explanation_content,
        'method': method,
        'seed': seed
    }, sort_keys=True, separators=(',', ':'))
    
    return sha3_hash(combined)


def verify_hash(data: Union[str, bytes], expected_hash: str) -> bool:
    """
    Verify that data matches expected hash.
    
    Args:
        data: Data to verify
        expected_hash: Expected SHA3-256 hash
        
    Returns:
        True if hash matches, False otherwise
    """
    computed_hash = sha3_hash(data)
    return computed_hash == expected_hash


def hash_file(file_path: str, chunk_size: int = 8192) -> str:
    """
    Hash a file in chunks to handle large files efficiently.
    
    Args:
        file_path: Path to file
        chunk_size: Size of chunks to read (default 8KB)
        
    Returns:
        SHA3-256 hash of file contents
    """
    hasher = hashlib.sha3_256()
    
    with open(file_path, 'rb') as f:
        while chunk := f.read(chunk_size):
            hasher.update(chunk)
    
    return hasher.hexdigest()

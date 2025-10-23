"""
RFC 8785 compliant JSON canonicalization.

This module ensures that JSON packets are serialized deterministically,
which is critical for:
- Consistent cryptographic signatures
- Cross-platform verification
- Legal-grade evidence

Rules:
1. UTF-8 encoding (no BOM)
2. Keys sorted alphabetically
3. No whitespace
4. Consistent number formatting
5. Escape sequences normalized
"""

import json
import canonicaljson
from typing import Dict, Any


def canonicalize_packet(packet: Dict[str, Any]) -> bytes:
    """
    Canonicalize a proof packet according to RFC 8785.
    
    This function ensures that the same packet will always produce
    the same byte sequence, regardless of:
    - Platform (Linux, macOS, Windows)
    - Python version
    - Dictionary key insertion order
    
    Args:
        packet: Proof packet dictionary
        
    Returns:
        Canonical JSON as bytes (UTF-8 encoded)
        
    Example:
        >>> packet = {"decision_id": "123", "timestamp_utc": "2025-10-18T08:32:00Z"}
        >>> canonical = canonicalize_packet(packet)
        >>> # Always produces: b'{"decision_id":"123","timestamp_utc":"2025-10-18T08:32:00Z"}'
    """
    return canonicaljson.encode_canonical_json(packet)


def canonicalize_to_string(packet: Dict[str, Any]) -> str:
    """
    Canonicalize packet and return as string.
    
    Args:
        packet: Proof packet dictionary
        
    Returns:
        Canonical JSON as UTF-8 string
    """
    return canonicalize_packet(packet).decode('utf-8')


def verify_canonicalization(packet: Dict[str, Any]) -> bool:
    """
    Verify that a packet can be canonicalized without errors.
    
    Args:
        packet: Proof packet dictionary
        
    Returns:
        True if canonicalization succeeds, False otherwise
    """
    try:
        canonicalize_packet(packet)
        return True
    except Exception:
        return False


def simple_canonicalize(packet: Dict[str, Any]) -> str:
    """
    Simple canonicalization using standard library.
    
    This is a fallback method that doesn't fully comply with RFC 8785
    but is useful for testing and non-critical operations.
    
    Args:
        packet: Proof packet dictionary
        
    Returns:
        JSON string with sorted keys and no whitespace
    """
    return json.dumps(packet, sort_keys=True, separators=(',', ':'), ensure_ascii=False)


def validate_packet_structure(packet: Dict[str, Any]) -> tuple[bool, str]:
    """
    Validate that a packet has the required structure for canonicalization.
    
    Args:
        packet: Proof packet dictionary
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    required_fields = [
        'schema_ver',
        'decision_id',
        'timestamp_utc',
        'issuer',
        'model',
        'input_hash',
        'decision',
        'explanation',
        'signing_key_id'
    ]
    
    for field in required_fields:
        if field not in packet:
            return False, f"Missing required field: {field}"
    
    # Validate nested structures
    if not isinstance(packet.get('issuer'), dict):
        return False, "Field 'issuer' must be a dictionary"
    
    if 'entity_id' not in packet['issuer'] or 'node_id' not in packet['issuer']:
        return False, "Field 'issuer' must contain 'entity_id' and 'node_id'"
    
    if not isinstance(packet.get('model'), dict):
        return False, "Field 'model' must be a dictionary"
    
    if 'id' not in packet['model'] or 'version' not in packet['model']:
        return False, "Field 'model' must contain 'id' and 'version'"
    
    if not isinstance(packet.get('decision'), dict):
        return False, "Field 'decision' must be a dictionary"
    
    if not isinstance(packet.get('explanation'), dict):
        return False, "Field 'explanation' must be a dictionary"
    
    return True, ""

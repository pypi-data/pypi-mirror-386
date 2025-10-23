"""
VeriChain SDK - Verifiable Decision Ledger for AI

This SDK provides tools for creating cryptographically verifiable audit trails
of AI decisions with legal-grade accountability.

Features:
- Decision recording and certification
- ATHENA: Legal explainability (GDPR Art. 22)
- HELIOS: Auto audit package generation
- ARES: Real-time bias interception (<1ms)
"""

__version__ = "2.4.1"

from .recorder import recorder, DecisionRecorder
from .hasher import sha3_hash, hash_input, hash_explanation
from .canonicalization import canonicalize_packet
from .signer import Signer, HSMSigner
from .packager import PacketPackager
from .ai_integration import DeepSeekClient, get_deepseek_client
from .cloud_client import VeriChainClient
from .athena_client import AthenaClient
from .helios_client import HeliosClient
from .ares_client import AresClient

__all__ = [
    "recorder",
    "DecisionRecorder",
    "sha3_hash",
    "hash_input",
    "hash_explanation",
    "canonicalize_packet",
    "Signer",
    "HSMSigner",
    "PacketPackager",
    "DeepSeekClient",
    "get_deepseek_client",
    "VeriChainClient",
    "AthenaClient",
    "HeliosClient",
    "AresClient",
]

"""
VeriChain Cloud Client
Sends decisions to VeriChain API (cloud or self-hosted)
"""

import requests
from typing import Dict, Any, Optional
import json


class VeriChainClient:
    """
    VeriChain Cloud Client
    
    Usage:
        client = VeriChainClient(
            api_key="vck_live_abc123...",
            endpoint="https://api.verichain.io"
        )
        
        result = client.submit_decision({
            "issuer": "your-system",
            "model_id": "loan_approval",
            "outcome": "approved",
            "risk_score": 35
        })
    """
    
    def __init__(
        self,
        api_key: str,
        endpoint: str = "https://api.verichain.io",
        timeout: int = 30
    ):
        """
        Initialize VeriChain client
        
        Args:
            api_key: Your VeriChain API key (from dashboard)
            endpoint: API endpoint (default: cloud)
            timeout: Request timeout in seconds
        """
        self.api_key = api_key
        self.endpoint = endpoint.rstrip('/')
        self.timeout = timeout
        
        # Validate API key format
        if not api_key.startswith('vck_'):
            raise ValueError("Invalid API key format. Must start with 'vck_'")
    
    def _make_request(
        self,
        method: str,
        path: str,
        data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Make HTTP request to API"""
        url = f"{self.endpoint}{path}"
        
        headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json"
        }
        
        try:
            if method == "GET":
                response = requests.get(url, headers=headers, timeout=self.timeout)
            elif method == "POST":
                response = requests.post(
                    url,
                    headers=headers,
                    json=data,
                    timeout=self.timeout
                )
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                raise ValueError("Invalid API key. Check your credentials.")
            elif e.response.status_code == 403:
                raise ValueError("Access denied. Check your permissions.")
            elif e.response.status_code == 429:
                raise ValueError("Rate limit exceeded. Please slow down.")
            else:
                raise ValueError(f"API error: {e.response.text}")
        except requests.exceptions.Timeout:
            raise ValueError("Request timeout. API may be unavailable.")
        except requests.exceptions.ConnectionError:
            raise ValueError(f"Cannot connect to {self.endpoint}")
    
    def submit_decision(
        self,
        issuer: str,
        model_id: str,
        model_version: str,
        outcome: str,
        risk_score: int,
        input_hash: Optional[str] = None,
        explanation_hash: Optional[str] = None,
        explanation_method: str = "SHAP",
        explanation_seed: int = 42,
        signing_key_id: str = "default",
        node: str = "default",
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Submit a decision to VeriChain
        
        Args:
            issuer: Your system identifier
            model_id: AI model identifier
            model_version: Model version
            outcome: Decision outcome
            risk_score: Risk score (0-100)
            metadata: Additional data (optional)
        
        Returns:
            {
                "success": True,
                "decision_id": "dec-...",
                "bias_score": 0.04,
                "certificate_id": "cert-...",
                "blockchain_anchor": {...}
            }
        """
        # Hash metadata if provided
        if metadata and not input_hash:
            input_hash = self._hash_data(metadata)
        
        if not input_hash:
            input_hash = "0" * 64  # Placeholder
        
        if not explanation_hash:
            explanation_hash = "0" * 64  # Placeholder
        
        data = {
            "issuer": issuer,
            "node": node,
            "model_id": model_id,
            "model_version": model_version,
            "input_hash": input_hash,
            "outcome": outcome,
            "risk_score": risk_score,
            "explanation_hash": explanation_hash,
            "explanation_method": explanation_method,
            "explanation_seed": explanation_seed,
            "signing_key_id": signing_key_id,
            "metadata": metadata  # Add metadata!
        }
        
        result = self._make_request("POST", "/submit_decision", data)
        
        return result
    
    def verify_decision(self, decision_id: str) -> Dict[str, Any]:
        """
        Verify a decision by ID
        
        Returns verification report
        """
        return self._make_request("GET", f"/verify/{decision_id}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get system statistics"""
        return self._make_request("GET", "/stats")
    
    def get_anchors(self, limit: int = 10) -> Dict[str, Any]:
        """Get recent blockchain anchors"""
        return self._make_request("GET", f"/ledger/anchors?limit={limit}")
    
    @staticmethod
    def _hash_data(data: Any) -> str:
        """Hash data for input_hash"""
        import hashlib
        json_str = json.dumps(data, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(json_str.encode()).hexdigest()
    
    @classmethod
    def from_env(cls) -> "VeriChainClient":
        """
        Create client from environment variables
        
        Requires:
            VERICHAIN_API_KEY
            VERICHAIN_ENDPOINT (optional)
        """
        import os
        
        api_key = os.getenv("VERICHAIN_API_KEY")
        if not api_key:
            raise ValueError("VERICHAIN_API_KEY environment variable not set")
        
        endpoint = os.getenv("VERICHAIN_ENDPOINT", "https://api.verichain.io")
        
        return cls(api_key=api_key, endpoint=endpoint)

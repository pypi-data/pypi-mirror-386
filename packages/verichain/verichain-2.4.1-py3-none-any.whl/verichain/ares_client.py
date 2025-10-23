"""
ARES Client - Real-time Interception
Client for VeriChain ARES Real-time Bias Interception
"""

import requests
from typing import Dict, Any, Optional, List


class AresClient:
    """
    Client for ARES Real-time Interception API
    
    Analyzes AI requests for bias in real-time (<1ms)
    """
    
    def __init__(self, api_url: str = "http://localhost:8000", api_key: Optional[str] = None):
        """
        Initialize ARES client
        
        Args:
            api_url: VeriChain API URL
            api_key: API key for authentication (REQUIRED for production)
        """
        self.api_url = api_url.rstrip('/')
        self.api_key = api_key
        self.headers = {'Content-Type': 'application/json'}
        
        if api_key:
            self.headers['Authorization'] = f'Bearer {api_key}'
        else:
            # Warning if no API key provided
            import warnings
            warnings.warn(
                "⚠️  No API key provided. Authentication is REQUIRED for production use. "
                "This will only work on localhost without authentication. "
                "Get your API key at: https://dashboard.verichain.io/settings/api-keys",
                UserWarning,
                stacklevel=2
            )
    
    def analyze(
        self,
        data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyze data for bias in real-time
        
        Args:
            data: Decision data to analyze
            context: Optional context (organization settings, etc.)
            
        Returns:
            Analysis result with bias score and recommended action
        """
        url = f"{self.api_url}/api/ares/analyze"
        
        payload = {'data': data}
        if context:
            payload['context'] = context
        
        response = requests.post(url, json=payload, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def simulate(
        self,
        data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Simulate what would happen if this decision was submitted
        
        Args:
            data: Decision data to simulate
            context: Optional context
            
        Returns:
            Simulation result showing what action would be taken
        """
        url = f"{self.api_url}/api/ares/simulate"
        
        payload = {'data': data}
        if context:
            payload['context'] = context
        
        response = requests.post(url, json=payload, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def test(self, test_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Test analyzer with multiple test cases
        
        Args:
            test_cases: List of test cases to analyze
            
        Returns:
            Test results with statistics
        """
        url = f"{self.api_url}/api/ares/test"
        
        payload = {'test_cases': test_cases}
        
        response = requests.post(url, json=payload, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get interception statistics
        
        Returns:
            Statistics including total intercepted, blocked, warned, allowed
        """
        url = f"{self.api_url}/api/ares/stats"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get ARES status and configuration
        
        Returns:
            Current status including enabled state and auto-block setting
        """
        url = f"{self.api_url}/api/ares/status"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def get_thresholds(self) -> Dict[str, Any]:
        """
        Get bias detection thresholds
        
        Returns:
            Current thresholds and protected attributes
        """
        url = f"{self.api_url}/api/ares/thresholds"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def configure(self, enabled: bool = True, auto_block: bool = True) -> Dict[str, Any]:
        """
        Configure ARES interceptor
        
        Args:
            enabled: Enable/disable ARES
            auto_block: Enable/disable automatic blocking
            
        Returns:
            Configuration confirmation
        """
        url = f"{self.api_url}/api/ares/configure"
        
        payload = {
            'enabled': enabled,
            'auto_block': auto_block
        }
        
        response = requests.post(url, json=payload, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def reset_stats(self) -> Dict[str, Any]:
        """
        Reset interception statistics
        
        Returns:
            Confirmation message
        """
        url = f"{self.api_url}/api/ares/reset-stats"
        response = requests.post(url, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def health_check(self) -> Dict[str, Any]:
        """Check ARES service health"""
        url = f"{self.api_url}/api/ares/health"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()

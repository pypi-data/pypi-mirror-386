"""
ATHENA Client - Legal Explainability
Client for VeriChain ATHENA Legal Explainability Engine
"""

import requests
from typing import Dict, Any, Optional, Literal


class AthenaClient:
    """
    Client for ATHENA Legal Explainability API
    
    Generates GDPR-compliant explanations for AI decisions
    """
    
    def __init__(self, api_url: str = "http://localhost:8000", api_key: Optional[str] = None):
        """
        Initialize ATHENA client
        
        Args:
            api_url: VeriChain API URL
            api_key: API key for authentication (REQUIRED for production)
        """
        self.api_url = api_url.rstrip('/')
        self.api_key = api_key
        self.headers = {}
        
        if api_key:
            self.headers['Authorization'] = f'Bearer {api_key}'
        else:
            import warnings
            warnings.warn(
                "⚠️  No API key provided. Authentication is REQUIRED for production use. "
                "This will only work on localhost without authentication. "
                "Get your API key at: https://dashboard.verichain.io/settings/api-keys",
                UserWarning,
                stacklevel=2
            )
    
    def explain(
        self,
        decision_id: str,
        level: Literal['citizen', 'regulator', 'legal'] = 'citizen',
        format: Literal['json', 'pdf'] = 'json',
        language: str = 'en'
    ) -> Dict[str, Any]:
        """
        Generate explanation for a decision
        
        Args:
            decision_id: ID of the decision to explain
            level: Explanation level (citizen, regulator, legal)
            format: Output format (json or pdf)
            language: Language code (default: en)
            
        Returns:
            Explanation data or PDF bytes
        """
        url = f"{self.api_url}/api/athena/explain/{decision_id}"
        params = {
            'level': level,
            'format': format,
            'language': language
        }
        
        response = requests.get(url, params=params, headers=self.headers)
        response.raise_for_status()
        
        if format == 'pdf':
            return response.content
        else:
            return response.json()
    
    def explain_pdf(
        self,
        decision_id: str,
        level: Literal['citizen', 'regulator', 'legal'] = 'citizen',
        output_path: Optional[str] = None
    ) -> bytes:
        """
        Generate PDF explanation for a decision
        
        Args:
            decision_id: ID of the decision to explain
            level: Explanation level
            output_path: Optional path to save PDF
            
        Returns:
            PDF bytes
        """
        url = f"{self.api_url}/api/athena/explain/{decision_id}/pdf"
        params = {'level': level}
        
        response = requests.get(url, params=params, headers=self.headers)
        response.raise_for_status()
        
        pdf_bytes = response.content
        
        if output_path:
            with open(output_path, 'wb') as f:
                f.write(pdf_bytes)
        
        return pdf_bytes
    
    def health_check(self) -> Dict[str, Any]:
        """Check ATHENA service health"""
        url = f"{self.api_url}/api/athena/health"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()

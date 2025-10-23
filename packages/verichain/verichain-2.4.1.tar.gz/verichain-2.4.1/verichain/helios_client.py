"""
HELIOS Client - Auto Audit Package
Client for VeriChain HELIOS Auto Audit Package Generator
"""

import requests
from typing import Dict, Any, Optional, List, Literal
from datetime import datetime, timedelta


class HeliosClient:
    """
    Client for HELIOS Auto Audit Package API
    
    Generates compliance reports for GDPR, EU AI Act, SOC 2, ISO 27001
    """
    
    def __init__(self, api_url: str = "http://localhost:8000", api_key: Optional[str] = None):
        """
        Initialize HELIOS client
        
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
            import warnings
            warnings.warn(
                "⚠️  No API key provided. Authentication is REQUIRED for production use. "
                "This will only work on localhost without authentication. "
                "Get your API key at: https://dashboard.verichain.io/settings/api-keys",
                UserWarning,
                stacklevel=2
            )
    
    def generate_report(
        self,
        organization_id: str,
        report_type: Literal['gdpr', 'eu_ai_act', 'soc2', 'iso27001'],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        language: str = 'en'
    ) -> Dict[str, Any]:
        """
        Generate a single compliance report
        
        Args:
            organization_id: Organization ID
            report_type: Type of report (gdpr, eu_ai_act, soc2, iso27001)
            start_date: Start date (ISO format, default: 30 days ago)
            end_date: End date (ISO format, default: now)
            language: Language code
            
        Returns:
            Report data
        """
        url = f"{self.api_url}/api/helios/generate"
        
        payload = {
            'organization_id': organization_id,
            'report_type': report_type,
            'language': language
        }
        
        if start_date:
            payload['start_date'] = start_date
        if end_date:
            payload['end_date'] = end_date
        
        response = requests.post(url, json=payload, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def generate_package(
        self,
        organization_id: str,
        include_reports: Optional[List[str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        language: str = 'en'
    ) -> Dict[str, Any]:
        """
        Generate complete audit package with multiple reports
        
        Args:
            organization_id: Organization ID
            include_reports: List of report types to include (default: all)
            start_date: Start date (ISO format)
            end_date: End date (ISO format)
            language: Language code
            
        Returns:
            Complete audit package with all reports
        """
        url = f"{self.api_url}/api/helios/package"
        
        if include_reports is None:
            include_reports = ['gdpr', 'eu_ai_act', 'soc2', 'iso27001']
        
        payload = {
            'organization_id': organization_id,
            'include_reports': include_reports,
            'language': language
        }
        
        if start_date:
            payload['start_date'] = start_date
        if end_date:
            payload['end_date'] = end_date
        
        response = requests.post(url, json=payload, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def get_stats(self, organization_id: str) -> Dict[str, Any]:
        """
        Get audit statistics for an organization
        
        Args:
            organization_id: Organization ID
            
        Returns:
            Statistics including compliance scores and audit readiness
        """
        url = f"{self.api_url}/api/helios/stats/{organization_id}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def list_reports(self) -> Dict[str, Any]:
        """
        List available report types
        
        Returns:
            List of available reports with descriptions
        """
        url = f"{self.api_url}/api/helios/reports"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def health_check(self) -> Dict[str, Any]:
        """Check HELIOS service health"""
        url = f"{self.api_url}/api/helios/health"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()

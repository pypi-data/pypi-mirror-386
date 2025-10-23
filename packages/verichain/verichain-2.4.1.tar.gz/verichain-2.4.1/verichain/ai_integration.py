"""
AI Integration module for VeriChain.

Integrates with DeepSeek API for AI-powered decision explanations
and analysis.
"""

import os
import json
import requests
from typing import Dict, Any, Optional, List
from datetime import datetime


class DeepSeekClient:
    """
    Client for DeepSeek API integration.
    
    Provides AI-powered explanations and analysis for decisions.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        api_url: Optional[str] = None,
        model: Optional[str] = None
    ):
        """
        Initialize DeepSeek client.
        
        Args:
            api_key: DeepSeek API key (or from env DEEPSEEK_API_KEY)
            api_url: API base URL (or from env DEEPSEEK_API_URL)
            model: Model name (or from env DEEPSEEK_MODEL)
        """
        self.api_key = api_key or os.getenv('DEEPSEEK_API_KEY')
        self.api_url = api_url or os.getenv('DEEPSEEK_API_URL', 'https://api.deepseek.com/v1')
        self.model = model or os.getenv('DEEPSEEK_MODEL', 'deepseek-chat')
        
        if not self.api_key:
            raise ValueError("DeepSeek API key is required. Set DEEPSEEK_API_KEY environment variable.")
    
    def generate_explanation(
        self,
        decision: str,
        input_data: Dict[str, Any],
        risk_score: int,
        model_name: str,
        temperature: float = 0.0,
        max_tokens: int = 500
    ) -> Dict[str, Any]:
        """
        Generate AI-powered explanation for a decision.
        
        Args:
            decision: Decision outcome (e.g., 'approve', 'reject')
            input_data: Input data used for decision
            risk_score: Risk score (0-100)
            model_name: Name of the decision model
            temperature: Temperature for generation (0.0 for deterministic)
            max_tokens: Maximum tokens in response
            
        Returns:
            Dictionary with explanation and metadata
        """
        prompt = self._build_explanation_prompt(
            decision, input_data, risk_score, model_name
        )
        
        response = self._call_api(
            prompt=prompt,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return {
            'explanation': response['content'],
            'model': self.model,
            'temperature': temperature,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'tokens_used': response.get('tokens_used', 0)
        }
    
    def analyze_decision_pattern(
        self,
        decisions: List[Dict[str, Any]],
        max_tokens: int = 1000
    ) -> Dict[str, Any]:
        """
        Analyze patterns in multiple decisions.
        
        Args:
            decisions: List of decision dictionaries
            max_tokens: Maximum tokens in response
            
        Returns:
            Analysis results
        """
        prompt = self._build_analysis_prompt(decisions)
        
        response = self._call_api(
            prompt=prompt,
            temperature=0.3,
            max_tokens=max_tokens
        )
        
        return {
            'analysis': response['content'],
            'decisions_analyzed': len(decisions),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
    
    def generate_compliance_report(
        self,
        decision_data: Dict[str, Any],
        regulations: List[str] = None
    ) -> Dict[str, Any]:
        """
        Generate compliance report for a decision.
        
        Args:
            decision_data: Decision data
            regulations: List of regulations to check (e.g., ['GDPR', 'AI Act'])
            
        Returns:
            Compliance report
        """
        if regulations is None:
            regulations = ['GDPR', 'EU AI Act', 'ISO 27001']
        
        prompt = self._build_compliance_prompt(decision_data, regulations)
        
        response = self._call_api(
            prompt=prompt,
            temperature=0.0,
            max_tokens=800
        )
        
        return {
            'compliance_report': response['content'],
            'regulations_checked': regulations,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
    
    def _call_api(
        self,
        prompt: str,
        temperature: float = 0.0,
        max_tokens: int = 500
    ) -> Dict[str, Any]:
        """
        Call DeepSeek API.
        
        Args:
            prompt: Prompt text
            temperature: Temperature for generation
            max_tokens: Maximum tokens
            
        Returns:
            API response
        """
        url = f"{self.api_url}/chat/completions"
        
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'model': self.model,
            'messages': [
                {
                    'role': 'system',
                    'content': 'You are an AI assistant specialized in explaining AI decisions and ensuring regulatory compliance.'
                },
                {
                    'role': 'user',
                    'content': prompt
                }
            ],
            'temperature': temperature,
            'max_tokens': max_tokens
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            return {
                'content': data['choices'][0]['message']['content'],
                'tokens_used': data.get('usage', {}).get('total_tokens', 0)
            }
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"DeepSeek API error: {str(e)}")
    
    def _build_explanation_prompt(
        self,
        decision: str,
        input_data: Dict[str, Any],
        risk_score: int,
        model_name: str
    ) -> str:
        """Build prompt for decision explanation."""
        return f"""Explain the following AI decision in clear, understandable terms:

Decision: {decision.upper()}
Risk Score: {risk_score}/100
Model: {model_name}

Input Data Summary:
{json.dumps(input_data, indent=2)}

Please provide:
1. A clear explanation of why this decision was made
2. Key factors that influenced the decision
3. Risk assessment interpretation
4. Any relevant considerations

Keep the explanation concise, factual, and suitable for audit purposes."""
    
    def _build_analysis_prompt(self, decisions: List[Dict[str, Any]]) -> str:
        """Build prompt for pattern analysis."""
        summary = {
            'total_decisions': len(decisions),
            'outcomes': {},
            'avg_risk_score': 0
        }
        
        total_risk = 0
        for d in decisions:
            outcome = d.get('outcome', 'unknown')
            summary['outcomes'][outcome] = summary['outcomes'].get(outcome, 0) + 1
            total_risk += d.get('risk_score', 0)
        
        summary['avg_risk_score'] = total_risk / len(decisions) if decisions else 0
        
        return f"""Analyze the following decision patterns:

Summary:
{json.dumps(summary, indent=2)}

Please provide:
1. Overall pattern analysis
2. Risk distribution insights
3. Potential anomalies or concerns
4. Recommendations for improvement

Focus on actionable insights."""
    
    def _build_compliance_prompt(
        self,
        decision_data: Dict[str, Any],
        regulations: List[str]
    ) -> str:
        """Build prompt for compliance check."""
        return f"""Review this AI decision for compliance with the following regulations:
{', '.join(regulations)}

Decision Data:
- Outcome: {decision_data.get('outcome')}
- Risk Score: {decision_data.get('risk_score')}
- Model: {decision_data.get('model_id')}
- Timestamp: {decision_data.get('timestamp')}

Please assess:
1. Compliance status for each regulation
2. Any potential compliance issues
3. Required documentation or disclosures
4. Recommendations for full compliance

Provide a clear, structured compliance assessment."""


# Convenience function
def get_deepseek_client() -> DeepSeekClient:
    """
    Get configured DeepSeek client.
    
    Returns:
        DeepSeekClient instance
    """
    return DeepSeekClient()

"""
Azure OpenAI Provider Wrapper

Wraps Azure OpenAI SDK to route through NotionAlpha proxy
Automatically captures transaction IDs for outcome tracking
"""

from typing import Any, Dict, Optional, Tuple
from openai import AzureOpenAI
from openai.types.chat import ChatCompletion

from ..types import ProviderError


class AzureOpenAIProvider:
    """
    Azure OpenAI provider wrapper
    
    Routes requests through NotionAlpha proxy for:
    - Automatic cost tracking (FinOps)
    - Security detection (threats, PII, etc.)
    - Transaction ID capture for outcome linking
    """
    
    def __init__(
        self,
        provider_id: str,
        deployment_name: str,
        org_id: str,
        team_id: str,
        environment: str,
        feature_id: Optional[str],
        proxy_base_url: str,
    ):
        self.provider_id = provider_id
        self.deployment_name = deployment_name
        self.org_id = org_id
        self.team_id = team_id
        self.environment = environment
        self.feature_id = feature_id
        self.proxy_base_url = proxy_base_url
        
        # Initialize Azure OpenAI client with NotionAlpha proxy
        default_headers = {
            'X-Org-ID': org_id,
            'X-Team-ID': team_id,
            'X-Environment': environment,
            'X-Azure-Deployment': deployment_name,
        }
        
        if feature_id:
            default_headers['X-Feature-ID'] = feature_id
        
        self.client = AzureOpenAI(
            azure_endpoint=f'{proxy_base_url}/v1/{provider_id}',
            api_key='dummy-key',  # Not used (credentials stored in NotionAlpha)
            api_version='2025-04-01-preview',
            default_headers=default_headers,
        )
    
    @property
    def chat(self):
        """Access chat completions interface"""
        return ChatCompletions(self.client)


class ChatCompletions:
    """Chat completions interface wrapper"""
    
    def __init__(self, client: AzureOpenAI):
        self.client = client
    
    @property
    def completions(self):
        """Access completions interface"""
        return Completions(self.client)


class Completions:
    """Completions interface wrapper"""
    
    def __init__(self, client: AzureOpenAI):
        self.client = client
    
    def create(self, **kwargs: Any) -> Tuple[ChatCompletion, str]:
        """
        Create chat completion

        Args:
            **kwargs: Arguments to pass to Azure OpenAI chat.completions.create()

        Returns:
            Tuple of (response, transaction_id)

        Raises:
            ProviderError: If request fails

        Example:
            >>> response, transaction_id = clarity.chat.completions.create(
            ...     model='gpt-4o-mini',  # Azure deployment name
            ...     messages=[{'role': 'user', 'content': 'Hello!'}]
            ... )
            >>>
            >>> # Use transactionId for outcome tracking
            >>> clarity.track_outcome(
            ...     transaction_id=transaction_id,
            ...     type='customer_support',
            ...     metadata={'time_saved_minutes': 15}
            ... )
        """
        try:
            # Make request through proxy and get raw response with headers
            raw_response = self.client.chat.completions.with_raw_response.create(**kwargs)

            # Extract transaction ID from NotionAlpha proxy response header
            transaction_id = (
                raw_response.headers.get('X-NotionAlpha-Transaction-Id') or
                raw_response.headers.get('x-notionalpha-transaction-id') or  # lowercase fallback
                'unknown'
            )

            # Parse the actual response object
            response = raw_response.parse()

            return response, transaction_id

        except Exception as e:
            raise ProviderError(f'Azure OpenAI request failed: {str(e)}', details=str(e))


"""
Anthropic Provider Wrapper

Wraps Anthropic SDK to route through NotionAlpha proxy
Automatically captures transaction IDs for outcome tracking
"""

from typing import Any, Dict, Optional, Tuple
from anthropic import Anthropic
from anthropic.types import Message

from ..types import ProviderError


class AnthropicProvider:
    """
    Anthropic provider wrapper
    
    Routes requests through NotionAlpha proxy for:
    - Automatic cost tracking (FinOps)
    - Security detection (threats, PII, etc.)
    - Transaction ID capture for outcome linking
    """
    
    def __init__(
        self,
        provider_id: str,
        org_id: str,
        team_id: str,
        environment: str,
        feature_id: Optional[str],
        proxy_base_url: str,
    ):
        self.provider_id = provider_id
        self.org_id = org_id
        self.team_id = team_id
        self.environment = environment
        self.feature_id = feature_id
        self.proxy_base_url = proxy_base_url
        
        # Initialize Anthropic client with NotionAlpha proxy
        default_headers = {
            'X-Org-ID': org_id,
            'X-Team-ID': team_id,
            'X-Environment': environment,
        }
        
        if feature_id:
            default_headers['X-Feature-ID'] = feature_id
        
        self.client = Anthropic(
            base_url=f'{proxy_base_url}/v1/{provider_id}',
            api_key='dummy-key',  # Not used (credentials stored in NotionAlpha)
            default_headers=default_headers,
        )
    
    @property
    def messages(self):
        """Access messages interface"""
        return Messages(self.client)


class Messages:
    """Messages interface wrapper"""
    
    def __init__(self, client: Anthropic):
        self.client = client
    
    def create(self, **kwargs: Any) -> Tuple[Message, str]:
        """
        Create message

        Args:
            **kwargs: Arguments to pass to Anthropic messages.create()

        Returns:
            Tuple of (response, transaction_id)

        Raises:
            ProviderError: If request fails

        Example:
            >>> response, transaction_id = clarity.messages.create(
            ...     model='claude-3-5-sonnet-20241022',
            ...     max_tokens=1024,
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
            raw_response = self.client.messages.with_raw_response.create(**kwargs)

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
            raise ProviderError(f'Anthropic request failed: {str(e)}', details=str(e))


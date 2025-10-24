"""
Main client interface for the AI SDK
"""

from typing import Optional, Dict, Any, List
from .exceptions import AISDKException
from .core.config import Config
from .core.http_client import HTTPClient
from .providers.base import ProviderFactory, BaseProvider


class AISDKClient:
    """
    Main client interface for the AI SDK

    Provides factory methods for creating configured client instances
    and access to all AI service operations.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: Optional[float] = None,
        provider: str = "openai",
        http_client: Optional[HTTPClient] = None,
        **kwargs,
    ):
        """
        Initialize the AI SDK client

        Args:
            api_key (str, optional): API key for authentication
            base_url (str, optional): Base URL for API requests
            timeout (float, optional): Request timeout in seconds
            provider (str): Provider to use (default: "openai")
            http_client (HTTPClient, optional): Pre-configured HTTP client
            **kwargs: Additional configuration options
        """
        # Create configuration
        self._config = Config(
            api_key=api_key,
            base_url=base_url or "https://api.openai.com/v1",
            timeout=timeout or 30.0,
            additional_options=kwargs,
        )

        # Store provider name
        self._provider_name = provider

        # Store HTTP client
        self._http_client = http_client

        # Initialize provider with HTTP client
        self._provider: BaseProvider = ProviderFactory.create_provider(
            provider, self._config, http_client=self._http_client
        )

    @classmethod
    def builder(cls):
        """
        Create a client builder for fluent configuration

        Returns:
            ClientBuilder: Builder instance for configuring the client
        """
        return ClientBuilder()

    def chat(self):
        """
        Access chat completions functionality

        Returns:
            ChatCompletions: Chat completions interface
        """
        return ChatCompletions(self)

    def completions(self):
        """
        Access text completions functionality

        Returns:
            Completions: Text completions interface
        """
        return Completions(self)

    def embeddings(self):
        """
        Access embeddings functionality

        Returns:
            Embeddings: Embeddings interface
        """
        return Embeddings(self)

    def close(self):
        """
        Close the client and free resources
        """
        if self._provider:
            self._provider.close()
    
    def __enter__(self):
        """
        Context manager entry
        """
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Context manager exit
        """
        self.close()


class ClientBuilder:
    """Builder class for creating configured client instances"""

    def __init__(self):
        self._config = {"provider": "openai"}
        self._http_client = None

    def with_api_key(self, api_key: str):
        """
        Set the API key for authentication

        Args:
            api_key (str): API key

        Returns:
            ClientBuilder: This builder instance
        """
        self._config["api_key"] = api_key
        return self

    def with_base_url(self, base_url: str):
        """
        Set the base URL for API requests

        Args:
            base_url (str): Base URL

        Returns:
            ClientBuilder: This builder instance
        """
        self._config["base_url"] = base_url
        return self

    def with_timeout(self, timeout: float):
        """
        Set the request timeout

        Args:
            timeout (float): Timeout in seconds

        Returns:
            ClientBuilder: This builder instance
        """
        self._config["timeout"] = timeout
        return self

    def with_provider(self, provider: str):
        """
        Set the provider to use

        Args:
            provider (str): Provider name

        Returns:
            ClientBuilder: This builder instance
        """
        self._config["provider"] = provider
        return self

    def with_http_client(self, http_client: HTTPClient):
        """
        Set a pre-configured HTTP client

        Args:
            http_client (HTTPClient): Pre-configured HTTP client

        Returns:
            ClientBuilder: This builder instance
        """
        self._http_client = http_client
        return self

    def build(self):
        """
        Build and return the configured client instance

        Returns:
            AISDKClient: Configured client instance
        """
        return AISDKClient(http_client=self._http_client, **self._config)


class BaseService:
    """Base class for service interfaces"""

    def __init__(self, client: AISDKClient):
        self._client = client


class ChatCompletions(BaseService):
    """Chat completions service interface"""

    def create(
        self,
        system_prompt: Optional[str] = None,
        messages: Optional[List[Dict[str, Any]]] = None,
        **params,
    ):
        """
        Create a chat completion

        Args:
            system_prompt (str, optional): System prompt as separate parameter
            messages (List[Dict[str, Any]], optional): List of messages with new format
            **params: Additional parameters for the chat completion

        Returns:
            Dict[str, Any]: Chat completion response
        """
        # Build parameters from explicit arguments and kwargs
        print("[INSIDE ChatCompletions create function ]")
        request_params = dict(params)

        # Add system_prompt if provided
        if system_prompt is not None:
            request_params["system_prompt"] = system_prompt

        # Add messages if provided
        if messages is not None:
            request_params["messages"] = messages

        return self._client._provider.chat_completions_create(request_params)


class Completions(BaseService):
    """Text completions service interface"""

    def create(self, **params):
        """
        Create a text completion

        Args:
            **params: Parameters for the text completion

        Returns:
            Dict[str, Any]: Text completion response
        """
        return self._client._provider.completions_create(params)


class Embeddings(BaseService):
    """Embeddings service interface"""

    def create(self, **params):
        """
        Create embeddings

        Args:
            **params: Parameters for the embeddings

        Returns:
            Dict[str, Any]: Embeddings response
        """
        return self._client._provider.embeddings_create(params)

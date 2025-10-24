"""
Base classes for AI providers
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union
from ..core.http_client import HTTPClient
from ..core.config import Config
from ..streaming.event_stream import EventStream


class BaseProvider(ABC):
    """
    Abstract base class for all AI providers
    """

    def __init__(self, config: Config, http_client: Optional[HTTPClient] = None):
        """
        Initialize the provider

        Args:
            config (Config): Configuration for the provider
            http_client (HTTPClient, optional): HTTP client instance
        """
        self.config = config

        # If no HTTP client provided, create one with configuration
        if http_client is None:
            self.http_client = HTTPClient(
                base_url=config.base_url,
                api_key=config.api_key,
                timeout=config.timeout,
                max_retries=getattr(config, "max_retries", 3),
                retry_delay=getattr(config, "retry_delay", 1.0),
            )
        else:
            self.http_client = http_client

    @abstractmethod
    def chat_completions_create(
        self, params: Dict[str, Any]
    ) -> Union[Dict[str, Any], "EventStream"]:
        """
        Create a chat completion

        Args:
            params (Dict[str, Any]): Parameters for the chat completion

        Returns:
            Union[Dict[str, Any], EventStream]: Chat completion response or stream

        """
        print("[INSIDE chat_completions_create in base file]")
        pass

    @abstractmethod
    def completions_create(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a text completion

        Args:
            params (Dict[str, Any]): Parameters for the text completion

        Returns:
            Dict[str, Any]: Text completion response
        """
        pass

    @abstractmethod
    def embeddings_create(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create embeddings

        Args:
            params (Dict[str, Any]): Parameters for the embeddings

        Returns:
            Dict[str, Any]: Embeddings response
        """
        pass

    @abstractmethod
    def models_list(self) -> Dict[str, Any]:
        """
        List available models

        Returns:
            Dict[str, Any]: Models list response
        """
        pass

    @abstractmethod
    def models_retrieve(self, model: str) -> Dict[str, Any]:
        """
        Retrieve information about a model

        Args:
            model (str): Model identifier

        Returns:
            Dict[str, Any]: Model information response
        """
        pass

    def close(self):
        """
        Close the provider and free resources
        """
        if hasattr(self.http_client, "close"):
            self.http_client.close()


class ProviderFactory:
    """
    Factory for creating provider instances
    """

    _providers = {}

    @classmethod
    def register_provider(cls, name: str, provider_class):
        """
        Register a provider class

        Args:
            name (str): Provider name
            provider_class: Provider class
        """
        cls._providers[name] = provider_class

    @classmethod
    def create_provider(
        cls,
        name: str,
        config: Config,
        http_client: Optional[HTTPClient] = None,
        **kwargs,
    ) -> BaseProvider:
        """
        Create a provider instance

        Args:
            name (str): Provider name
            config (Config): Configuration for the provider
            http_client (HTTPClient, optional): HTTP client instance
            **kwargs: Additional arguments for provider initialization

        Returns:
            BaseProvider: Provider instance

        Raises:
            ValueError: If provider is not registered
        """
        if name not in cls._providers:
            raise ValueError(f"Provider '{name}' is not registered")

        provider_class = cls._providers[name]
        return provider_class(config, http_client=http_client, **kwargs)

    @classmethod
    def list_providers(cls) -> List[str]:
        """
        List registered providers

        Returns:
            List[str]: List of registered provider names
        """
        return list(cls._providers.keys())

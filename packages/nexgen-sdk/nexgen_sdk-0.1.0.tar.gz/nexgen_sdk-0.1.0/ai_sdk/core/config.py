"""
Configuration management for the AI SDK
"""

import os
from typing import Optional, Any, Dict
from dataclasses import dataclass, field


@dataclass
class Config:
    """
    Configuration class for the AI SDK
    """

    # API configuration
    api_key: Optional[str] = None
    base_url: str = "https://api.openai.com/v1"
    timeout: float = 30.0

    # Request configuration
    max_retries: int = 3
    retry_delay: float = 1.0

    # Provider-specific configuration
    default_model: Optional[str] = None

    # Additional configuration options
    additional_options: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_environment(cls) -> "Config":
        """
        Create configuration from environment variables

        Environment variables:
        - AI_SDK_API_KEY: API key for authentication
        - AI_SDK_BASE_URL: Base URL for API requests
        - AI_SDK_TIMEOUT: Request timeout in seconds

        Returns:
            Config: Configuration instance
        """
        return cls(
            api_key=os.getenv("AI_SDK_API_KEY"),
            base_url=os.getenv("AI_SDK_BASE_URL", "https://api.openai.com/v1"),
            timeout=float(os.getenv("AI_SDK_TIMEOUT", 30.0)),
        )

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "Config":
        """
        Create configuration from dictionary

        Args:
            config_dict (Dict[str, Any]): Configuration dictionary

        Returns:
            Config: Configuration instance
        """
        # Extract known fields
        known_fields = {
            "api_key": config_dict.get("api_key"),
            "base_url": config_dict.get("base_url", "https://api.openai.com/v1"),
            "timeout": float(config_dict.get("timeout", 30.0)),
            "max_retries": int(config_dict.get("max_retries", 3)),
            "retry_delay": float(config_dict.get("retry_delay", 1.0)),
        }

        # Extract additional options
        additional_options = {
            k: v for k, v in config_dict.items() if k not in known_fields
        }

        return cls(additional_options=additional_options, **known_fields)

    def get(self, key: str, default: Optional[Any] = None) -> Any:
        """
        Get configuration value by key

        Args:
            key (str): Configuration key
            default (Any, optional): Default value if key not found

        Returns:
            Any: Configuration value
        """
        if hasattr(self, key):
            return getattr(self, key)
        return self.additional_options.get(key, default)

    def set(self, key: str, value: Any):
        """
        Set configuration value

        Args:
            key (str): Configuration key
            value (Any): Configuration value
        """
        if hasattr(self, key):
            setattr(self, key, value)
        else:
            self.additional_options[key] = value


class ConfigManager:
    """
    Configuration manager for handling multiple configuration sources
    """

    def __init__(self):
        self._configs = []

    def add_config(self, config: Config):
        """
        Add a configuration instance

        Args:
            config (Config): Configuration instance
        """
        self._configs.append(config)

    def get(self, key: str, default: Optional[Any] = None) -> Any:
        """
        Get configuration value, checking configs in order

        Args:
            key (str): Configuration key
            default (Any, optional): Default value if key not found in any config

        Returns:
            Any: Configuration value
        """
        for config in reversed(self._configs):
            value = config.get(key)
            if value is not None:
                return value
        return default

    def set_global(self, key: str, value: Any):
        """
        Set a global configuration value

        Args:
            key (str): Configuration key
            value (Any): Configuration value
        """
        # Create global config if it doesn't exist
        if not self._configs:
            self._configs.append(Config())

        self._configs[0].set(key, value)

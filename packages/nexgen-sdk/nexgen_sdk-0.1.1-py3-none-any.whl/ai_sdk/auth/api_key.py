"""
API key authentication for the AI SDK
"""

import os
from typing import Optional, Dict, Any
from ..exceptions import AuthenticationException


class APIKeyAuth:
    """
    API key authentication handler
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the API key authentication handler

        Args:
            api_key (str, optional): API key for authentication
        """
        self._api_key = api_key or os.getenv("AI_SDK_API_KEY")

        if not self._api_key:
            raise AuthenticationException(
                "No API key provided. Set AI_SDK_API_KEY environment variable "
                "or pass api_key parameter."
            )

    @property
    def api_key(self) -> str:
        """
        Get the API key

        Returns:
            str: API key

        Raises:
            AuthenticationException: If API key is not set
        """
        if not self._api_key:
            raise AuthenticationException("API key not set")
        return self._api_key

    def get_auth_headers(self) -> Dict[str, str]:
        """
        Get authentication headers

        Returns:
            Dict[str, str]: Authentication headers
        """
        return {"Authorization": f"Bearer {self.api_key}"}

    def validate(self) -> bool:
        """
        Validate the API key format (basic validation)

        Returns:
            bool: True if API key format is valid
        """
        if not self._api_key:
            return False

        # Basic validation - check if key is not empty and has reasonable length
        # Note: This doesn't validate if the key is actually valid for API access
        return len(self._api_key.strip()) > 10

    @classmethod
    def from_env(cls, env_var: str = "AI_SDK_API_KEY") -> "APIKeyAuth":
        """
        Create API key authentication from environment variable

        Args:
            env_var (str): Environment variable name

        Returns:
            APIKeyAuth: API key authentication instance
        """
        api_key = os.getenv(env_var)
        return cls(api_key)

    def __str__(self) -> str:
        """
        String representation of the API key (masked for security)

        Returns:
            str: Masked API key representation
        """
        if not self._api_key:
            return "APIKeyAuth(None)"

        # Mask the API key for security
        masked_key = (
            self._api_key[:4] + "*" * (len(self._api_key) - 8) + self._api_key[-4:]
        )
        return f"APIKeyAuth({masked_key})"

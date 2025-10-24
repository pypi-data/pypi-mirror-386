"""
OpenAI provider implementation
"""

from typing import Dict, Any, Optional, Union
from ..core.config import Config
from ..core.http_client import HTTPClient
from .base import BaseProvider
from ..exceptions import AISDKException
from ..streaming.event_stream import EventStream


class OpenAIProvider(BaseProvider):
    """
    OpenAI provider implementation for direct OpenAI API access
    """
    
    def chat_completions_create(self, params: Dict[str, Any]) -> Union[Dict[str, Any], EventStream]:
        """
        Create a chat completion using OpenAI API
        
        Args:
            params (Dict[str, Any]): Parameters for the chat completion
            
        Returns:
            Union[Dict[str, Any], EventStream]: Chat completion response or stream
        """
        # Validate required parameters
        if 'model' not in params:
            raise AISDKException("Missing required parameter: model")
        
        if 'messages' not in params:
            raise AISDKException("Missing required parameter: messages")
        
        try:
            if params.get('stream', False):
                # Handle streaming
                response = self.http_client.post_stream(
                    endpoint="/chat/completions",
                    data=params,
                    retry=False
                )
                return EventStream(response)
            else:
                # Handle regular request
                return self.http_client.post(
                    endpoint="/chat/completions",
                    data=params,
                    retry=True
                )
        except Exception as e:
            if isinstance(e, AISDKException):
                raise
            raise AISDKException(f"OpenAI chat completion failed: {str(e)}", cause=e)
    
    def completions_create(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a text completion using OpenAI API
        
        Args:
            params (Dict[str, Any]): Parameters for the text completion
            
        Returns:
            Dict[str, Any]: Text completion response
        """
        # Validate required parameters
        if 'model' not in params:
            raise AISDKException("Missing required parameter: model")
        
        if 'prompt' not in params:
            raise AISDKException("Missing required parameter: prompt")
        
        try:
            return self.http_client.post(
                endpoint="/completions",
                data=params,
                retry=True
            )
        except Exception as e:
            if isinstance(e, AISDKException):
                raise
            raise AISDKException(f"OpenAI text completion failed: {str(e)}", cause=e)
    
    def embeddings_create(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create embeddings using OpenAI API
        
        Args:
            params (Dict[str, Any]): Parameters for the embeddings
            
        Returns:
            Dict[str, Any]: Embeddings response
        """
        # Validate required parameters
        if 'model' not in params:
            raise AISDKException("Missing required parameter: model")
        
        if 'input' not in params:
            raise AISDKException("Missing required parameter: input")
        
        try:
            return self.http_client.post(
                endpoint="/embeddings",
                data=params,
                retry=True
            )
        except Exception as e:
            if isinstance(e, AISDKException):
                raise
            raise AISDKException(f"OpenAI embeddings failed: {str(e)}", cause=e)
    
    def models_list(self) -> Dict[str, Any]:
        """
        List available models from OpenAI
        
        Returns:
            Dict[str, Any]: Models list response
        """
        try:
            return self.http_client.get(endpoint="/models", retry=True)
        except Exception as e:
            if isinstance(e, AISDKException):
                raise
            raise AISDKException(f"Failed to list OpenAI models: {str(e)}", cause=e)
    
    def models_retrieve(self, model: str) -> Dict[str, Any]:
        """
        Retrieve information about a model from OpenAI
        
        Args:
            model (str): Model identifier
            
        Returns:
            Dict[str, Any]: Model information response
        """
        if not model:
            raise AISDKException("Missing required parameter: model")
        
        try:
            return self.http_client.get(endpoint=f"/models/{model}", retry=True)
        except Exception as e:
            if isinstance(e, AISDKException):
                raise
            raise AISDKException(f"Failed to retrieve OpenAI model '{model}': {str(e)}", cause=e)


# Register the provider
from .base import ProviderFactory
ProviderFactory.register_provider('openai', OpenAIProvider)
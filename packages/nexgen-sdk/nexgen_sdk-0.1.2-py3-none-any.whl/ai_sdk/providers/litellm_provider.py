"""
LiteLLM provider implementation
"""

from typing import Dict, Any, Optional, List, Union, Iterator
from ..core.config import Config
from ..core.http_client import HTTPClient
from .base import BaseProvider
from ..exceptions import AISDKException
from ..streaming.event_stream import EventStream

try:
    import litellm
except ImportError:
    litellm = None


class LiteLLMEventStream:
    """
    Event stream wrapper for LiteLLM streaming responses
    """

    def __init__(self, generator_func):
        """
        Initialize the LiteLLM event stream

        Args:
            generator_func: Generator function that yields chunk data
        """
        self._generator_func = generator_func
        self._closed = False

    def __iter__(self) -> Iterator[Dict[str, Any]]:
        """
        Iterate over streaming events

        Yields:
            Dict[str, Any]: Event data
        """
        if self._closed:
            raise AISDKException("Event stream is closed")

        try:
            for chunk in self._generator_func():
                yield chunk
        except Exception as e:
            raise AISDKException("Error in LiteLLM stream", cause=e)

    def close(self):
        """
        Close the event stream
        """
        self._closed = True

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class LiteLLMProvider(BaseProvider):
    """
    LiteLLM provider implementation that supports multiple model providers
    through the LiteLLM unified interface
    """

    def __init__(self, config: Config, http_client: Optional[HTTPClient] = None):
        """
        Initialize the LiteLLM provider

        Args:
            config (Config): Configuration for the provider
            http_client (HTTPClient, optional): HTTP client instance
        """
        super().__init__(config, http_client)

        if litellm is None:
            raise AISDKException(
                "litellm package is required for LiteLLMProvider. Install with: pip install litellm"
            )

        # Configure LiteLLM settings
        litellm.set_verbose = getattr(config, "litellm_verbose", False)
        litellm.drop_params = getattr(config, "litellm_drop_params", True)

        # Set custom headers if provided
        if hasattr(config, "litellm_headers"):
            litellm.api_header = config.litellm_headers

    def chat_completions_create(
        self, params: Dict[str, Any]
    ) -> Union[Dict[str, Any], EventStream]:
        """
        Create a chat completion using LiteLLM

        Args:
            params (Dict[str, Any]): Parameters for the chat completion

        Returns:
            Union[Dict[str, Any], EventStream]: Chat completion response or stream
        """
        # Validate required parameters
        if "model" not in params:
            raise AISDKException("Missing required parameter: model")

        if "messages" not in params:
            raise AISDKException("Missing required parameter: messages")

        # Prepare LiteLLM completion parameters
        completion_params = {
            "model": params["model"],
            "messages": params["messages"],
            **{k: v for k, v in params.items() if k not in ["model", "messages"]},
        }

        # Add API configuration from config if not in params
        if "api_key" not in completion_params and self.config.api_key:
            completion_params["api_key"] = self.config.api_key

        if "api_base" not in completion_params and self.config.base_url:
            completion_params["api_base"] = self.config.base_url

        try:
            # Check if streaming is requested
            if completion_params.get("stream", False):
                # Create a generator wrapper for LiteLLM streaming
                def lite_llm_stream_generator():
                    try:
                        for chunk in litellm.completion(**completion_params):
                            # Convert LiteLLM chunk to standard format
                            yield {
                                "id": getattr(chunk, "id", None),
                                "object": "chat.completion.chunk",
                                "created": getattr(chunk, "created", None),
                                "model": completion_params["model"],
                                "choices": [
                                    {
                                        "index": getattr(choice, "index", 0),
                                        "delta": {
                                            "role": getattr(
                                                choice.delta, "role", "assistant"
                                            ),
                                            "content": getattr(
                                                choice.delta, "content", ""
                                            ),
                                        },
                                        "finish_reason": getattr(
                                            choice, "finish_reason", None
                                        ),
                                    }
                                    for choice in chunk.choices
                                ],
                            }
                    except Exception as e:
                        raise AISDKException(
                            f"LiteLLM streaming failed: {str(e)}", cause=e
                        )

                # Create EventStream from generator
                return LiteLLMEventStream(lite_llm_stream_generator())
            else:
                # Use LiteLLM for completion
                response = litellm.completion(**completion_params)

                # Convert LiteLLM response to standard format
                return {
                    "id": getattr(response, "id", None),
                    "object": "chat.completion",
                    "created": getattr(response, "created", None),
                    "model": completion_params["model"],
                    "choices": [
                        {
                            "index": getattr(choice, "index", 0),
                            "message": {
                                "role": getattr(choice.message, "role", "assistant"),
                                "content": getattr(choice.message, "content", ""),
                            },
                            "finish_reason": getattr(choice, "finish_reason", None),
                        }
                        for choice in response.choices
                    ],
                    "usage": {
                        "prompt_tokens": (
                            getattr(response.usage, "prompt_tokens", 0)
                            if response.usage
                            else 0
                        ),
                        "completion_tokens": (
                            getattr(response.usage, "completion_tokens", 0)
                            if response.usage
                            else 0
                        ),
                        "total_tokens": (
                            getattr(response.usage, "total_tokens", 0)
                            if response.usage
                            else 0
                        ),
                    },
                }
        except Exception as e:
            raise AISDKException(f"LiteLLM completion failed: {str(e)}", cause=e)

    def completions_create(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a text completion using LiteLLM

        Args:
            params (Dict[str, Any]): Parameters for the text completion

        Returns:
            Dict[str, Any]: Text completion response
        """
        # Validate required parameters
        if "model" not in params:
            raise AISDKException("Missing required parameter: model")

        if "prompt" not in params:
            raise AISDKException("Missing required parameter: prompt")

        # Prepare LiteLLM completion parameters
        completion_params = {
            "model": params["model"],
            "prompt": params["prompt"],
            **{k: v for k, v in params.items() if k not in ["model", "prompt"]},
        }

        # Add API configuration from config if not in params
        if "api_key" not in completion_params and self.config.api_key:
            completion_params["api_key"] = self.config.api_key

        if "api_base" not in completion_params and self.config.base_url:
            completion_params["api_base"] = self.config.base_url

        try:
            # Use LiteLLM for completion
            response = litellm.text_completion(**completion_params)

            # Convert LiteLLM response to standard format
            return {
                "id": getattr(response, "id", None),
                "object": "text_completion",
                "created": getattr(response, "created", None),
                "model": completion_params["model"],
                "choices": [
                    {
                        "index": getattr(choice, "index", 0),
                        "text": getattr(choice, "text", ""),
                        "logprobs": getattr(choice, "logprobs", None),
                        "finish_reason": getattr(choice, "finish_reason", None),
                    }
                    for choice in response.choices
                ],
                "usage": {
                    "prompt_tokens": (
                        getattr(response.usage, "prompt_tokens", 0)
                        if response.usage
                        else 0
                    ),
                    "completion_tokens": (
                        getattr(response.usage, "completion_tokens", 0)
                        if response.usage
                        else 0
                    ),
                    "total_tokens": (
                        getattr(response.usage, "total_tokens", 0)
                        if response.usage
                        else 0
                    ),
                },
            }
        except Exception as e:
            raise AISDKException(f"LiteLLM text completion failed: {str(e)}", cause=e)

    def embeddings_create(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create embeddings using LiteLLM

        Args:
            params (Dict[str, Any]): Parameters for the embeddings

        Returns:
            Dict[str, Any]: Embeddings response
        """
        # Validate required parameters
        if "model" not in params:
            raise AISDKException("Missing required parameter: model")

        if "input" not in params:
            raise AISDKException("Missing required parameter: input")

        # Prepare LiteLLM embedding parameters
        embedding_params = {
            "model": params["model"],
            "input": params["input"],
            **{k: v for k, v in params.items() if k not in ["model", "input"]},
        }

        # Add API configuration from config if not in params
        if "api_key" not in embedding_params and self.config.api_key:
            embedding_params["api_key"] = self.config.api_key

        if "api_base" not in embedding_params and self.config.base_url:
            embedding_params["api_base"] = self.config.base_url

        try:
            # Use LiteLLM for embeddings
            response = litellm.embedding(**embedding_params)

            # Convert LiteLLM response to standard format
            return {
                "object": "list",
                "data": [
                    {
                        "object": "embedding",
                        "embedding": getattr(data, "embedding", []),
                        "index": getattr(data, "index", 0),
                    }
                    for data in response.data
                ],
                "model": embedding_params["model"],
                "usage": {
                    "prompt_tokens": (
                        getattr(response.usage, "prompt_tokens", 0)
                        if response.usage
                        else 0
                    ),
                    "total_tokens": (
                        getattr(response.usage, "total_tokens", 0)
                        if response.usage
                        else 0
                    ),
                },
            }
        except Exception as e:
            raise AISDKException(f"LiteLLM embedding failed: {str(e)}", cause=e)

    def models_list(self) -> Dict[str, Any]:
        """
        List available models from LiteLLM

        Returns:
            Dict[str, Any]: Models list response
        """
        try:
            # Get available models from LiteLLM
            models = litellm.list_models()

            return {
                "object": "list",
                "data": [
                    {
                        "id": model,
                        "object": "model",
                        "created": None,
                        "owned_by": "litellm",
                    }
                    for model in models
                ],
            }
        except Exception as e:
            raise AISDKException(f"Failed to list LiteLLM models: {str(e)}", cause=e)

    def models_retrieve(self, model: str) -> Dict[str, Any]:
        """
        Retrieve information about a model from LiteLLM

        Args:
            model (str): Model identifier

        Returns:
            Dict[str, Any]: Model information response
        """
        if not model:
            raise AISDKException("Missing required parameter: model")

        try:
            # Get available models and find the requested one
            models = litellm.list_models()
            if model not in models:
                raise AISDKException(
                    f"Model '{model}' not found in available LiteLLM models"
                )

            return {
                "id": model,
                "object": "model",
                "created": None,
                "owned_by": "litellm",
            }
        except Exception as e:
            raise AISDKException(
                f"Failed to retrieve LiteLLM model '{model}': {str(e)}", cause=e
            )


# Register the provider
from .base import ProviderFactory

ProviderFactory.register_provider("litellm", LiteLLMProvider)

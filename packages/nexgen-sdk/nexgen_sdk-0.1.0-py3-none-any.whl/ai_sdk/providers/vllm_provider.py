"""
VLLM provider implementation for custom VLLM deployment
"""

from typing import Dict, Any, Optional, List, Union
from ..core.config import Config
from ..core.http_client import HTTPClient
from .base import BaseProvider
from ..exceptions import AISDKException
from ..streaming.event_stream import EventStream
from ..streaming.simple_stream import SimpleEventStream
import time


class VLLMProvider(BaseProvider):
    """
    VLLM provider implementation for connecting to custom VLLM deployments
    """

    def __init__(self, config: Config, http_client: Optional[HTTPClient] = None):
        """
        Initialize the VLLM provider

        Args:
            config (Config): Configuration for the provider
            http_client (HTTPClient, optional): HTTP client instance
        """
        # Set default base URL for VLLM if not provided
        if not config.base_url or config.base_url == "https://api.openai.com/v1":
            config.base_url = "https://backend.v3.codemateai.dev/v2"

        # Create HTTP client with VLLM-specific settings
        if not http_client:
            http_client = HTTPClient(
                base_url=config.base_url,
                api_key=config.api_key,
                timeout=config.timeout,
                max_retries=getattr(config, "max_retries", 3),
                retry_delay=getattr(config, "retry_delay", 1.0),
            )

        super().__init__(config, http_client)

        # Store default model if specified in config
        self.default_model = getattr(config, "default_model", "cora_chat")

    def _validate_tools(self, tools: List[Dict[str, Any]]) -> None:
        """
        Validate tools parameter

        Args:
            tools (List[Dict[str, Any]]): Tools to validate

        Raises:
            AISDKException: If tools are invalid
        """
        if not isinstance(tools, list):
            raise AISDKException("Tools must be a list")

        for i, tool in enumerate(tools):
            if not isinstance(tool, dict):
                raise AISDKException(f"Tool {i} must be a dictionary")

            if "type" not in tool or tool["type"] != "function":
                raise AISDKException(f"Tool {i} must have type 'function'")

            if "function" not in tool:
                raise AISDKException(f"Tool {i} must have a 'function' field")

            function = tool["function"]
            if not isinstance(function, dict):
                raise AISDKException(f"Tool {i} function must be a dictionary")

            if "name" not in function:
                raise AISDKException(f"Tool {i} function must have a 'name'")

            if "parameters" in function:
                parameters = function["parameters"]
                if not isinstance(parameters, dict):
                    raise AISDKException(f"Tool {i} parameters must be a dictionary")

                if parameters.get("type") != "object":
                    raise AISDKException(f"Tool {i} parameters type must be 'object'")

    def _validate_tool_choice(self, tool_choice: Union[str, Dict[str, Any]]) -> None:
        """
        Validate tool_choice parameter

        Args:
            tool_choice (Union[str, Dict[str, Any]]): Tool choice to validate

        Raises:
            AISDKException: If tool_choice is invalid
        """
        valid_choices = ["none", "auto", "required"]

        if isinstance(tool_choice, str):
            if tool_choice not in valid_choices:
                raise AISDKException(
                    f"tool_choice must be one of {valid_choices} or a specific function object"
                )
        elif isinstance(tool_choice, dict):
            if "type" not in tool_choice or tool_choice["type"] != "function":
                raise AISDKException("tool_choice object must have type 'function'")

            if "function" not in tool_choice or "name" not in tool_choice["function"]:
                raise AISDKException("tool_choice object must specify a function name")
        else:
            raise AISDKException("tool_choice must be a string or object")

    def chat_completions_create(
        self, params: Dict[str, Any]
    ) -> Union[Dict[str, Any], EventStream]:
        """
        Create a chat completion using VLLM

        Args:
            params (Dict[str, Any]): Parameters for the chat completion.
                - system_prompt (str, optional): System prompt as separate parameter
                - messages (List[Dict]): Message array (user/assistant messages only when system_prompt is used)
                - model (str): Model identifier
                - stream (bool, optional): Whether to stream response
                - Other OpenAI-compatible parameters

        Returns:
            Union[Dict[str, Any], EventStream]: Chat completion response or stream
        """
        print("[INSIDE chat_completions_create in vllm_provider.py file    ]")
        start_time = time.time()
        # Validate required parameters
        if "model" not in params:
            # Use default model if available
            if self.default_model:
                params["model"] = self.default_model
            else:
                raise AISDKException(
                    "Missing required parameter: model and no default model configured"
                )

        # Handle system_prompt - keep it as separate parameter for API
        system_prompt = params.get("system_prompt", None)

        # Process messages with new format validation
        if "messages" not in params:
            raise AISDKException("Missing required parameter: messages")

        messages = []
        for message in params["messages"]:
            if not isinstance(message, dict):
                raise AISDKException("Each message must be a dictionary")

            if "role" not in message:
                raise AISDKException("Each message must have a 'role' field")

            if "content" not in message:
                raise AISDKException("Each message must have a 'content' field")

            role = message["role"]
            content = message["content"]

            if role == "user":
                # User content should be an object, but no type checking - allow any structure
                if not isinstance(content, dict):
                    raise AISDKException("User message 'content' must be an object")
                # No additional type checking for user content object as requested
                messages.append(message)
            elif role == "assistant":
                # Assistant content must be a string
                if not isinstance(content, str):
                    raise AISDKException("Assistant message 'content' must be a string")
                messages.append(message)
            elif role == "system":
                # Skip system messages if using separate system_prompt parameter
                if not system_prompt:
                    # Only include system messages in messages array if no separate system_prompt
                    if not isinstance(content, str):
                        raise AISDKException(
                            "System message 'content' must be a string"
                        )
                    messages.append(message)
                # If using separate system_prompt, skip system messages in array
            else:
                raise AISDKException(
                    f"Invalid message role: {role}. Must be 'user', 'assistant', or 'system'"
                )

        # Replace the original messages with processed ones
        params["messages"] = messages

        # Validate tools parameter if present
        if "tools" in params:
            self._validate_tools(params["tools"])

        # Validate tool_choice parameter if present
        if "tool_choice" in params:
            self._validate_tool_choice(params["tool_choice"])

        # Use model as-is since API expects formats like "cora_chat", not "openai/cora_chat"

        try:
            # Check if streaming is requested
            if params.get("stream", False):

                print("[INSIDE STREAM TRUE ]")
                elapsed = time.time() - start_time
                print(f"BEFORE calling to v2 llm request  {elapsed:.3f}s\n")
                # Make streaming request to VLLM API
                # Note: streaming requests don't support retry as it would consume the stream
                response = self.http_client.post_stream(
                    endpoint="/v2/chat/completions",
                    data=params,
                    retry=False,  # Don't retry streaming requests
                )
                elapsed = time.time() - start_time
                print(f"AFTER calling to v2 llm request  {elapsed:.3f}s\n")
                print("[INSIDE VLLM PROVIDER STREAM TRUE]")
                print(f"[STREAM RESPOSNE SEND TP EVENT STREAM IS ]", response)
                return EventStream(response)
            else:
                # Make regular request to VLLM API
                response = self.http_client.post(
                    endpoint="/v2/chat/completions", data=params, retry=True
                )

                # Ensure response has the expected structure
                if "choices" not in response:
                    raise AISDKException(
                        "Invalid response from VLLM: missing 'choices' field"
                    )

                return response
        except Exception as e:
            if isinstance(e, AISDKException):
                raise
            raise AISDKException(f"VLLM chat completion failed: {str(e)}", cause=e)

    def completions_create(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a text completion using VLLM

        Args:
            params (Dict[str, Any]): Parameters for the text completion

        Returns:
            Dict[str, Any]: Text completion response
        """
        # Validate required parameters
        if "model" not in params:
            # Use default model if available
            if self.default_model:
                params["model"] = self.default_model
            else:
                raise AISDKException(
                    "Missing required parameter: model and no default model configured"
                )

        if "prompt" not in params:
            raise AISDKException("Missing required parameter: prompt")

        # Use model as-is since API expects formats like "cora_chat", not "openai/cora_chat"

        try:
            # Make request to VLLM API
            response = self.http_client.post(
                endpoint="/v1/completions", data=params, retry=True
            )

            # Ensure response has the expected structure
            if "choices" not in response:
                raise AISDKException(
                    "Invalid response from VLLM: missing 'choices' field"
                )

            return response
        except Exception as e:
            if isinstance(e, AISDKException):
                raise
            raise AISDKException(f"VLLM text completion failed: {str(e)}", cause=e)

    def embeddings_create(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create embeddings using VLLM

        Args:
            params (Dict[str, Any]): Parameters for the embeddings

        Returns:
            Dict[str, Any]: Embeddings response
        """
        # Validate required parameters
        if "model" not in params:
            # Use default model if available
            if self.default_model:
                params["model"] = self.default_model
            else:
                raise AISDKException(
                    "Missing required parameter: model and no default model configured"
                )

        if "input" not in params:
            raise AISDKException("Missing required parameter: input")

        # Use model as-is since API expects formats like "cora_chat", not "openai/cora_chat"

        try:
            # Make request to VLLM API
            response = self.http_client.post(
                endpoint="/v1/embeddings", data=params, retry=True
            )

            # Ensure response has the expected structure
            if "data" not in response:
                raise AISDKException("Invalid response from VLLM: missing 'data' field")

            return response
        except Exception as e:
            if isinstance(e, AISDKException):
                raise
            raise AISDKException(f"VLLM embeddings failed: {str(e)}", cause=e)

    def models_list(self) -> Dict[str, Any]:
        """
        List available models from VLLM

        Returns:
            Dict[str, Any]: Models list response
        """
        try:
            # Make request to VLLM API
            response = self.http_client.get(endpoint="/v1/models", retry=True)

            # Ensure response has the expected structure
            if "data" not in response:
                raise AISDKException("Invalid response from VLLM: missing 'data' field")

            return response
        except Exception as e:
            if isinstance(e, AISDKException):
                raise
            raise AISDKException(f"Failed to list VLLM models: {str(e)}", cause=e)

    def models_retrieve(self, model: str) -> Dict[str, Any]:
        """
        Retrieve information about a model from VLLM

        Args:
            model (str): Model identifier

        Returns:
            Dict[str, Any]: Model information response
        """
        if not model:
            raise AISDKException("Missing required parameter: model")

        # Use model as-is since API expects formats like "cora_chat", not "openai/cora_chat"

        try:
            # Make request to VLLM API
            response = self.http_client.get(endpoint=f"/v1/models/{model}", retry=True)

            return response
        except Exception as e:
            if isinstance(e, AISDKException):
                raise
            raise AISDKException(
                f"Failed to retrieve VLLM model '{model}': {str(e)}", cause=e
            )


# Register the provider
from .base import ProviderFactory

ProviderFactory.register_provider("vllm", VLLMProvider)

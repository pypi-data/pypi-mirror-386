"""
Utility functions for the AI SDK
"""

import json
from typing import Any, Dict, List, Union, Optional
from datetime import datetime


def sanitize_params(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitize parameters by removing None values and converting to appropriate types

    Args:
        params (Dict[str, Any]): Parameters to sanitize

    Returns:
        Dict[str, Any]: Sanitized parameters
    """
    sanitized = {}

    for key, value in params.items():
        if value is not None:
            # Convert datetime objects to ISO format strings
            if isinstance(value, datetime):
                sanitized[key] = value.isoformat()
            # Convert lists to JSON strings if needed
            elif isinstance(value, (list, dict)):
                sanitized[key] = value
            # Convert everything else to string representation
            else:
                sanitized[key] = value

    return sanitized


def merge_dicts(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge two dictionaries, with dict2 values taking precedence

    Args:
        dict1 (Dict[str, Any]): First dictionary
        dict2 (Dict[str, Any]): Second dictionary

    Returns:
        Dict[str, Any]: Merged dictionary
    """
    merged = dict1.copy()
    merged.update(dict2)
    return merged


def json_serialize(obj: Any) -> str:
    """
    Serialize object to JSON string

    Args:
        obj (Any): Object to serialize

    Returns:
        str: JSON serialized string
    """
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))


def json_deserialize(json_str: str) -> Any:
    """
    Deserialize JSON string to object

    Args:
        json_str (str): JSON string to deserialize

    Returns:
        Any: Deserialized object
    """
    return json.loads(json_str)


def validate_model_name(model_name: str) -> bool:
    """
    Validate model name format

    Args:
        model_name (str): Model name to validate

    Returns:
        bool: True if valid, False otherwise
    """
    if not model_name or not isinstance(model_name, str):
        return False

    # Basic validation - model name should not be empty
    # and should not contain whitespace only
    return bool(model_name.strip())


def format_messages(messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """
    Format messages for API consumption

    Args:
        messages (List[Dict[str, str]]): Messages to format

    Returns:
        List[Dict[str, str]]: Formatted messages
    """
    formatted = []

    for message in messages:
        if isinstance(message, dict) and "role" in message and "content" in message:
            formatted.append({"role": message["role"], "content": message["content"]})

    return formatted


def estimate_token_count(text: str) -> int:
    """
    Estimate token count for text (very rough approximation)

    Args:
        text (str): Text to estimate tokens for

    Returns:
        int: Estimated token count
    """
    # Very rough estimation: 1 token ~= 4 characters
    # This is just for basic estimation, not accurate tokenization
    return len(text) // 4


def get_current_timestamp() -> str:
    """
    Get current timestamp in ISO format

    Returns:
        str: Current timestamp
    """
    return datetime.utcnow().isoformat() + "Z"


def is_valid_url(url: str) -> bool:
    """
    Basic URL validation

    Args:
        url (str): URL to validate

    Returns:
        bool: True if valid, False otherwise
    """
    if not url or not isinstance(url, str):
        return False

    url = url.strip()
    return url.startswith(("http://", "https://"))

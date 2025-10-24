"""
AI SDK - A custom Python SDK for interacting with AI models
"""

__title__ = "ai_sdk"
__version__ = "0.1.0"
__build__ = 0
__author__ = "AI SDK Project"
__license__ = "MIT"
__copyright__ = "Copyright 2025 AI SDK Project"

# Import main client
from .client import AISDKClient

# Import exceptions
from .exceptions import AISDKException

__all__ = [
    "AISDKClient",
    "AISDKException",
]

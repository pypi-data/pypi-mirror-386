"""
Error handling framework for the AI SDK
"""

import logging
from typing import Optional, Dict, Any, Callable, Type
from functools import wraps
from ..exceptions import AISDKException


class ErrorHandler:
    """
    Centralized error handling framework
    """

    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize the error handler

        Args:
            logger (logging.Logger, optional): Logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
        self._exception_handlers = {}

    def register_handler(self, exception_type: Type[Exception], handler: Callable):
        """
        Register a handler for a specific exception type

        Args:
            exception_type (Type[Exception]): Exception type
            handler (Callable): Handler function
        """
        self._exception_handlers[exception_type] = handler

    def handle_exception(self, exception: Exception) -> None:
        """
        Handle an exception using registered handlers

        Args:
            exception (Exception): Exception to handle
        """
        # Log the exception
        self.logger.exception("An error occurred: %s", str(exception))

        # Try to find a specific handler
        for exception_type, handler in self._exception_handlers.items():
            if isinstance(exception, exception_type):
                handler(exception)
                return

        # Default handling for AISDKException
        if isinstance(exception, AISDKException):
            self._handle_sdk_exception(exception)
        else:
            # Re-raise unknown exceptions
            raise exception

    def _handle_sdk_exception(self, exception: AISDKException) -> None:
        """
        Handle AISDKException instances

        Args:
            exception (AISDKException): SDK exception to handle
        """
        # Log with context
        if exception.cause:
            self.logger.error(
                "SDK Exception: %s (caused by: %s)",
                exception.message,
                str(exception.cause),
            )
        else:
            self.logger.error("SDK Exception: %s", exception.message)

    def retry_on_exception(
        self,
        exceptions: tuple = (AISDKException,),
        max_attempts: int = 3,
        delay: float = 1.0,
        backoff: float = 2.0,
    ):
        """
        Decorator to retry a function on specific exceptions

        Args:
            exceptions (tuple): Exceptions to retry on
            max_attempts (int): Maximum number of attempts
            delay (float): Initial delay between retries
            backoff (float): Backoff multiplier for delay
        """

        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                last_exception = None
                current_delay = delay

                for attempt in range(max_attempts):
                    try:
                        return func(*args, **kwargs)
                    except exceptions as e:
                        last_exception = e
                        self.logger.warning(
                            "Attempt %d failed: %s. Retrying in %.2f seconds...",
                            attempt + 1,
                            str(e),
                            current_delay,
                        )

                        # Sleep if not the last attempt
                        if attempt < max_attempts - 1:
                            import time

                            time.sleep(current_delay)
                            current_delay *= backoff
                        continue

                # If we get here, all attempts failed
                self.logger.error(
                    "Function %s failed after %d attempts", func.__name__, max_attempts
                )
                raise last_exception

            return wrapper

        return decorator


# Global error handler instance
error_handler = ErrorHandler()


def handle_errors(func):
    """
    Decorator to handle errors in a consistent manner

    Args:
        func (Callable): Function to wrap

    Returns:
        Callable: Wrapped function
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error_handler.handle_exception(e)
            # Re-raise the exception for caller to handle
            raise

    return wrapper


class ErrorContext:
    """
    Context manager for error handling
    """

    def __init__(self, context: str, logger: Optional[logging.Logger] = None):
        """
        Initialize error context

        Args:
            context (str): Context description
            logger (logging.Logger, optional): Logger instance
        """
        self.context = context
        self.logger = logger or logging.getLogger(__name__)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.logger.error(
                "Error in context '%s': %s - %s",
                self.context,
                exc_type.__name__,
                exc_val,
            )
        return False  # Don't suppress the exception


def safe_call(func, *args, default=None, **kwargs):
    """
    Safely call a function, returning a default value on error

    Args:
        func (Callable): Function to call
        *args: Positional arguments
        default (Any): Default value to return on error
        **kwargs: Keyword arguments

    Returns:
        Any: Function result or default value
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        error_handler.handle_exception(e)
        return default


def validate_parameters(params: Dict[str, Any], required: list) -> None:
    """
    Validate that required parameters are present

    Args:
        params (Dict[str, Any]): Parameters to validate
        required (list): List of required parameter names

    Raises:
        AISDKException: If required parameters are missing
    """
    missing = [param for param in required if param not in params]
    if missing:
        raise AISDKException(f"Missing required parameters: {', '.join(missing)}")


def sanitize_response(response: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitize response data to ensure it has expected structure

    Args:
        response (Dict[str, Any]): Raw response data

    Returns:
        Dict[str, Any]: Sanitized response data
    """
    # Ensure response has basic structure
    sanitized = {
        "id": response.get("id", ""),
        "object": response.get("object", ""),
        "created": response.get("created", 0),
        "model": response.get("model", ""),
        "choices": response.get("choices", []),
        "usage": response.get("usage", {}),
    }

    # Add any other fields that might be present
    for key, value in response.items():
        if key not in sanitized:
            sanitized[key] = value

    return sanitized

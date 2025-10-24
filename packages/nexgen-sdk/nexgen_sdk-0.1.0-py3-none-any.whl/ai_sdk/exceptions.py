"""
Custom exception classes for the AI SDK
"""

from typing import Optional


class AISDKException(Exception):
    """
    Base exception class for all AI SDK exceptions
    """

    def __init__(self, message: str, cause: Optional[Exception] = None):
        """
        Initialize the exception

        Args:
            message (str): Exception message
            cause (Exception, optional): Underlying cause of the exception
        """
        super().__init__(message)
        self.message = message
        self.cause = cause


class APIException(AISDKException):
    """
    Base exception for API-related errors
    """

    pass


class BadRequestException(APIException):
    """
    Exception raised for bad request errors (400 status code)
    """

    pass


class AuthenticationException(APIException):
    """
    Exception raised for authentication errors (401 status code)
    """

    pass


class PermissionException(APIException):
    """
    Exception raised for permission errors (403 status code)
    """

    pass


class NotFoundException(APIException):
    """
    Exception raised when a resource is not found (404 status code)
    """

    pass


class RateLimitException(APIException):
    """
    Exception raised when rate limit is exceeded (429 status code)
    """

    pass


class ServerException(APIException):
    """
    Exception raised for server errors (500 status code)
    """

    pass


class NetworkException(AISDKException):
    """
    Base exception for network-related errors
    """

    pass


class TimeoutException(NetworkException):
    """
    Exception raised when a request times out
    """

    pass


class ConnectionException(NetworkException):
    """
    Exception raised for connection-related errors
    """

    pass


class ValidationException(AISDKException):
    """
    Exception raised for data validation errors
    """

    pass

"""
HTTP client wrapper for the AI SDK
"""

import json
import time
import logging
from typing import Optional, Dict, Any, Union, Tuple
from urllib.parse import urljoin
import httpx
from ..exceptions import (
    AISDKException,
    APIException,
    BadRequestException,
    AuthenticationException,
    PermissionException,
    NotFoundException,
    RateLimitException,
    ServerException,
    NetworkException,
    TimeoutException,
    ConnectionException,
)
from .error_handler import error_handler, handle_errors


class HTTPClient:
    """
    HTTP client wrapper for making requests to AI services
    """

    def __init__(
        self,
        base_url: str,
        api_key: Optional[str] = None,
        timeout: float = 30.0,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        http_client: Optional[httpx.Client] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize the HTTP client

        Args:
            base_url (str): Base URL for API requests
            api_key (str, optional): API key for authentication
            timeout (float): Request timeout in seconds
            max_retries (int): Maximum number of retries for failed requests
            retry_delay (float): Delay between retries in seconds
            http_client (httpx.Client, optional): Pre-configured HTTP client
            logger (logging.Logger, optional): Logger instance
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.logger = logger or logging.getLogger(__name__)

        if http_client:
            self._client = http_client
        else:
            self._client = httpx.Client(timeout=timeout)

    def _get_headers(self) -> Dict[str, str]:
        """
        Get default headers for requests

        Returns:
            Dict[str, str]: Default headers
        """
        headers = {"Content-Type": "application/json", "User-Agent": "AI-SDK/0.1.0"}

        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        return headers

    def _handle_response(self, response: httpx.Response) -> Dict[str, Any]:
        """
        Handle HTTP response and convert to appropriate format

        Args:
            response (httpx.Response): HTTP response

        Returns:
            Dict[str, Any]: Parsed response data

        Raises:
            APIException: For API-related errors
        """
        # Check for HTTP errors
        if response.status_code >= 400:
            self._handle_http_error(response)

        # Try to parse JSON response
        try:
            return response.json()
        except json.JSONDecodeError:
            # If JSON parsing fails, return text content
            return {"text": response.text}

    def _handle_http_error(self, response: httpx.Response):
        """
        Handle HTTP error responses

        Args:
            response (httpx.Response): HTTP response with error status

        Raises:
            APIException: Appropriate exception based on status code
        """
        status_code = response.status_code
        error_message = f"HTTP {status_code}"

        # Try to extract error message from response
        try:
            error_data = response.json()
            if "error" in error_data:
                error_obj = error_data["error"]
                if isinstance(error_obj, dict):
                    error_message = error_obj.get("message", error_message)
                    error_type = error_obj.get("type")
                    error_param = error_obj.get("param")
                    error_code = error_obj.get("code")
                else:
                    error_message = str(error_obj)
        except json.JSONDecodeError:
            error_message = response.text or error_message
        except Exception as e:
            # Log the error parsing issue
            self.logger.warning("Failed to parse error response: %s", str(e))
            # If we can't parse the error, use the status code
            pass

        # Map status codes to exceptions
        if status_code == 400:
            raise BadRequestException(error_message)
        elif status_code == 401:
            raise AuthenticationException(error_message)
        elif status_code == 403:
            raise PermissionException(error_message)
        elif status_code == 404:
            raise NotFoundException(error_message)
        elif status_code == 429:
            raise RateLimitException(error_message)
        elif 500 <= status_code < 600:
            raise ServerException(error_message)
        else:
            raise APIException(error_message)

    def _should_retry(self, exception: Exception) -> bool:
        """
        Determine if a request should be retried

        Args:
            exception (Exception): Exception that occurred

        Returns:
            bool: True if request should be retried
        """
        # Don't retry client errors (4xx) except for rate limiting
        if isinstance(
            exception,
            (
                BadRequestException,
                AuthenticationException,
                PermissionException,
                NotFoundException,
            ),
        ):
            return False

        # Retry rate limit errors
        if isinstance(exception, RateLimitException):
            return True

        # Retry server errors and network issues
        if isinstance(
            exception,
            (ServerException, NetworkException, TimeoutException, ConnectionException),
        ):
            return True

        # Retry other SDK exceptions
        if isinstance(exception, AISDKException):
            return True

        # Don't retry other exceptions
        return False

    @handle_errors
    def _retry_request(
        self, method: str, url: str, **kwargs
    ) -> Tuple[httpx.Response, Dict[str, Any]]:
        """
        Make an HTTP request with retry logic

        Args:
            method (str): HTTP method
            url (str): URL to request
            **kwargs: Additional arguments for the request

        Returns:
            Tuple[httpx.Response, Dict[str, Any]]: Response and parsed data

        Raises:
            AISDKException: For request-related errors
        """
        last_exception = None

        for attempt in range(self.max_retries + 1):
            try:
                # Make request
                response = self._client.request(method, url, **kwargs)

                # Handle response
                data = self._handle_response(response)

                return response, data

            except (
                RateLimitException,
                ServerException,
                NetworkException,
                TimeoutException,
                ConnectionException,
                AISDKException,
            ) as e:
                last_exception = e

                # If this is the last attempt, re-raise the exception
                if attempt == self.max_retries:
                    raise

                # If we shouldn't retry, re-raise the exception
                if not self._should_retry(e):
                    raise

                # Log retry attempt
                self.logger.warning(
                    "Request attempt %d failed: %s. Retrying in %.2f seconds...",
                    attempt + 1,
                    str(e),
                    self.retry_delay,
                )

                # Wait before retrying
                if self.retry_delay > 0:
                    time.sleep(self.retry_delay)

            except Exception as e:
                # For unexpected exceptions, wrap and re-raise
                wrapped_exception = AISDKException("Unexpected error occurred", cause=e)
                last_exception = wrapped_exception
                raise wrapped_exception

        # This should never be reached, but just in case
        raise last_exception or AISDKException("Request failed")

    @handle_errors
    def request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        retry: bool = True,
    ) -> Dict[str, Any]:
        """
        Make an HTTP request

        Args:
            method (str): HTTP method (GET, POST, PUT, DELETE, etc.)
            endpoint (str): API endpoint
            data (Dict[str, Any], optional): Request data for POST/PUT
            params (Dict[str, Any], optional): Query parameters
            headers (Dict[str, str], optional): Additional headers
            retry (bool): Whether to retry failed requests

        Returns:
            Dict[str, Any]: Response data

        Raises:
            AISDKException: For request-related errors
        """
        # Construct full URL
        url = urljoin(self.base_url + "/", endpoint.lstrip("/"))

        # Log request
        self.logger.debug("Making %s request to %s", method, url)

        # Merge headers
        request_headers = self._get_headers()
        if headers:
            request_headers.update(headers)

        # Prepare request data
        json_data = json.dumps(data) if data else None

        # Prepare request kwargs
        request_kwargs = {
            "content": json_data,
            "params": params,
            "headers": request_headers,
        }

        if retry:
            # Use retry logic
            _, data = self._retry_request(method, url, **request_kwargs)
            return data
        else:
            # Make single request without retry
            try:
                response = self._client.request(method, url, **request_kwargs)
                return self._handle_response(response)
            except httpx.TimeoutException as e:
                raise TimeoutException("Request timed out", cause=e)
            except httpx.NetworkError as e:
                raise ConnectionException("Network error occurred", cause=e)
            except httpx.RequestError as e:
                raise NetworkException("Request error occurred", cause=e)
            except AISDKException:
                # Re-raise SDK exceptions
                raise
            except Exception as e:
                # Wrap unexpected exceptions
                raise AISDKException("Unexpected error occurred", cause=e)

    @handle_errors
    def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        retry: bool = True,
    ) -> Dict[str, Any]:
        """
        Make a GET request

        Args:
            endpoint (str): API endpoint
            params (Dict[str, Any], optional): Query parameters
            headers (Dict[str, str], optional): Additional headers
            retry (bool): Whether to retry failed requests

        Returns:
            Dict[str, Any]: Response data
        """
        return self.request(
            "GET", endpoint, params=params, headers=headers, retry=retry
        )

    @handle_errors
    def post(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        retry: bool = True,
    ) -> Dict[str, Any]:
        """
        Make a POST request

        Args:
            endpoint (str): API endpoint
            data (Dict[str, Any], optional): Request data
            headers (Dict[str, str], optional): Additional headers
            retry (bool): Whether to retry failed requests

        Returns:
            Dict[str, Any]: Response data
        """
        return self.request("POST", endpoint, data=data, headers=headers, retry=retry)

    def post_stream(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        retry: bool = False,  # Don't retry streaming requests by default
    ) -> httpx.Response:
        """
        Make a streaming POST request with immediate response using httpx streaming

        Args:
            endpoint (str): API endpoint
            data (Dict[str, Any], optional): Request data
            headers (Dict[str, str], optional): Additional headers
            retry (bool): Whether to retry failed requests

        Returns:
            httpx.Response: Streaming response
        """
        # Construct full URL
        url = urljoin(self.base_url + "/", endpoint.lstrip("/"))

        # Log request
        self.logger.debug("Making streaming POST request to %s", url)

        # Merge headers with real-time streaming optimizations
        request_headers = self._get_headers()
        if headers:
            request_headers.update(headers)

        # Add headers for real-time streaming to prevent buffering
        request_headers.update(
            {
                "Cache-Control": "no-cache, no-store",
                "Connection": "keep-alive",
                "Accept": "text/event-stream",
                "X-Accel-Buffering": "no",
            }
        )

        # Prepare request data
        json_data = json.dumps(data) if data else None

        try:
            # Use existing client but with optimized settings for streaming
            # Create streaming client with optimized timeouts for immediate response
            streaming_client = httpx.Client(
                timeout=httpx.Timeout(
                    connect=2.0,  # Very quick connection timeout
                    read=30.0,  # Read timeout for streaming
                    write=2.0,  # Quick write timeout
                    pool=10.0,  # Pool timeout
                ),
                http2=False,  # Force HTTP/1.1 for better streaming compatibility
                verify=True,
                follow_redirects=True,
                limits=httpx.Limits(
                    max_keepalive_connections=1,  # Single connection for streaming
                    max_connections=5,
                    keepalive_expiry=30.0,
                ),
            )

            # Make streaming request using httpx's built-in streaming
            # This is the key fix - use httpx.Client.stream() context manager
            try:
                # Create the streaming context
                stream_context = streaming_client.stream(
                    "POST", url, content=json_data, headers=request_headers
                )

                # Enter the stream context to initiate the request immediately
                response = stream_context.__enter__()

                # Store the context manager for proper cleanup
                response._stream_context = stream_context
                response._streaming_client = streaming_client

                # Add diagnostic logging
                self.logger.debug(
                    "Streaming request initiated - status: %d", response.status_code
                )

                # Add cleanup method that properly closes the stream context
                original_close = getattr(response, "close", None)

                def close_with_stream_cleanup():
                    if (
                        hasattr(response, "_stream_context")
                        and response._stream_context
                    ):
                        try:
                            # Properly exit the stream context
                            response._stream_context.__exit__(None, None, None)
                        except Exception as e:
                            self.logger.warning("Error closing stream context: %s", e)

                    if (
                        hasattr(response, "_streaming_client")
                        and response._streaming_client
                    ):
                        try:
                            response._streaming_client.close()
                        except Exception as e:
                            self.logger.warning("Error closing streaming client: %s", e)

                    if original_close:
                        original_close()

                response.close = close_with_stream_cleanup

                return response

            except Exception as e:
                # Clean up on error
                streaming_client.close()
                raise

        except httpx.TimeoutException as e:
            raise TimeoutException("Streaming request timed out", cause=e)
        except httpx.NetworkError as e:
            raise ConnectionException("Streaming network error occurred", cause=e)
        except httpx.RequestError as e:
            raise NetworkException("Streaming request error occurred", cause=e)
        except AISDKException:
            # Re-raise SDK exceptions
            raise
        except Exception as e:
            # Wrap unexpected exceptions
            raise AISDKException("Unexpected streaming error occurred", cause=e)

    @handle_errors
    def put(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        retry: bool = True,
    ) -> Dict[str, Any]:
        """
        Make a PUT request

        Args:
            endpoint (str): API endpoint
            data (Dict[str, Any], optional): Request data
            headers (Dict[str, str], optional): Additional headers
            retry (bool): Whether to retry failed requests

        Returns:
            Dict[str, Any]: Response data
        """
        return self.request("PUT", endpoint, data=data, headers=headers, retry=retry)

    @handle_errors
    def delete(
        self,
        endpoint: str,
        headers: Optional[Dict[str, str]] = None,
        retry: bool = True,
    ) -> Dict[str, Any]:
        """
        Make a DELETE request

        Args:
            endpoint (str): API endpoint
            headers (Dict[str, str], optional): Additional headers
            retry (bool): Whether to retry failed requests

        Returns:
            Dict[str, Any]: Response data
        """
        return self.request("DELETE", endpoint, headers=headers, retry=retry)

    def close(self):
        """
        Close the HTTP client and free resources
        """
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

"""
Simple streaming implementation that avoids httpx consumption issues
"""

import json
import time
import logging
from typing import Dict, Any, Iterator
import httpx
from ..exceptions import AISDKException, NetworkException

logger = logging.getLogger(__name__)


class SimpleEventStream:
    """
    Simple event stream handler that avoids httpx consumption issues
    """

    # Replace the __init__ method (lines 30-42)
    def __init__(self, response: httpx.Response):
        """
        Initialize the simple event stream handler

        Args:
            response (httpx.Response): HTTP response with streaming content
        """
        self._response = response
        self._closed = False

        # Use larger chunk size for better performance while maintaining real-time processing
        self._iterator = response.iter_bytes(chunk_size=1024)
        self._buffer = b""

    # Replace the __iter__ method (lines 44-135)
    def __iter__(self) -> Iterator[Dict[str, Any]]:
        """
        Iterate over streaming events

        Yields:
            Dict[str, Any]: Event data
        """
        if self._closed:
            raise AISDKException("Event stream is closed")

        logger.info("Starting real-time event stream iteration")
        chunk_count = 0
        start_time = time.time()

        try:
            for chunk in self._iterator:
                chunk_count += 1
                current_time = time.time()
                elapsed = current_time - start_time

                logger.debug(
                    "Processing chunk %d at %.3fs: %s",
                    chunk_count,
                    elapsed,
                    chunk[:100],
                )

                # Add chunk to buffer
                self._buffer += chunk

                # Process complete lines from buffer
                while b"\n" in self._buffer:
                    line, self._buffer = self._buffer.split(b"\n", 1)
                    line = line.decode("utf-8", errors="ignore").strip()

                    if not line:
                        continue

                    # Handle Server-Sent Events format
                    if line.startswith("data: "):
                        data = line[6:]  # Remove 'data: ' prefix

                        # Check for stream end
                        if data.strip() == "[DONE]":
                            logger.info(
                                "Stream ended with [DONE] after %d chunks in %.3fs",
                                chunk_count,
                                elapsed,
                            )
                            return

                        # Parse and yield JSON data
                        try:
                            event = json.loads(data)
                            logger.debug("Yielded event %d: %s", chunk_count, event)
                            yield event
                        except json.JSONDecodeError as e:
                            logger.warning(
                                "Skipping malformed JSON at chunk %d: %s",
                                chunk_count,
                                e,
                            )
                            continue
                    elif (
                        line.startswith("event: ")
                        or line.startswith("id: ")
                        or line.startswith("retry: ")
                    ):
                        # Handle other SSE fields
                        continue

                # No artificial delay needed - real streaming!

        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(
                "Error in event stream after %d chunks in %.3fs", chunk_count, elapsed
            )
            raise AISDKException("Error in event stream", cause=e)

    def close(self):
        """
        Close the event stream and clean up resources
        """
        self._closed = True
        if hasattr(self._response, "close"):
            self._response.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

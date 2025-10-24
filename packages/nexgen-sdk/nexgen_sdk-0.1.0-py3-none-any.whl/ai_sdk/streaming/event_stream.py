"""
Event stream handler for streaming responses
"""

import json
import time
import logging
from typing import Dict, Any, Callable, Optional, Iterator
import httpx
from ..exceptions import AISDKException, NetworkException

logger = logging.getLogger(__name__)


class EventStream:
    """
    Event stream handler for processing streaming responses
    """

    def __init__(self, response: httpx.Response):
        """
        Initialize the event stream handler

        Args:
            response (httpx.Response): HTTP response with streaming content
        """
        self._response = response
        self._closed = False

    def __iter__(self) -> Iterator[Dict[str, Any]]:
        """
        Iterate over streaming events in real-time

        Yields:
            Dict[str, Any]: Event data
        """
        if self._closed:
            raise AISDKException("Event stream is closed")

        logger.info("Starting real-time event stream iteration")
        chunk_count = 0
        start_time = time.time()
        buffer = b""

        try:
            # Use iter_bytes() for better control over chunk processing
            for raw_chunk in self._response.iter_bytes(chunk_size=1024):
                if not raw_chunk:
                    continue

                buffer += raw_chunk

                # Process complete events from buffer in real-time
                while b"\n" in buffer:
                    line, buffer = buffer.split(b"\n", 1)
                    line = line.decode("utf-8", errors="ignore").strip()

                    if not line:
                        continue

                    chunk_count += 1
                    current_time = time.time()
                    elapsed = current_time - start_time

                    logger.debug(
                        "Received chunk %d at %.3fs: %s",
                        chunk_count,
                        elapsed,
                        line[:100],
                    )

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

                        # Parse and yield JSON data immediately for real-time processing
                        try:
                            event = json.loads(data)
                            logger.debug("Parsed event %d: %s", chunk_count, event)
                            yield event
                        except json.JSONDecodeError as e:
                            logger.warning(
                                "Skipping malformed JSON at chunk %d: %s",
                                chunk_count,
                                e,
                            )
                            continue

                    elif line.startswith("event: "):
                        # Handle event types if needed
                        continue
                    elif line.startswith("id: "):
                        # Handle event IDs if needed
                        continue
                    elif line.startswith("retry: "):
                        # Handle retry instructions if needed
                        continue

                # No artificial delay - process data as it arrives for real-time streaming

        except httpx.StreamClosed:
            elapsed = time.time() - start_time
            logger.info("Stream closed after %d chunks in %.3fs", chunk_count, elapsed)
        except httpx.ReadError as e:
            elapsed = time.time() - start_time
            logger.error(
                "Stream read error after %d chunks in %.3fs", chunk_count, elapsed
            )
            raise NetworkException("Stream read error", cause=e)
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(
                "Unexpected error in event stream after %d chunks in %.3fs",
                chunk_count,
                elapsed,
            )
            raise AISDKException("Unexpected error in event stream", cause=e)
        finally:
            # Process any remaining data in buffer at the end
            if buffer:
                remaining_data = buffer.decode("utf-8", errors="ignore").strip()
                if remaining_data.startswith("data: "):
                    data = remaining_data[6:]
                    if data.strip() != "[DONE]":
                        try:
                            event = json.loads(data)
                            yield event
                        except json.JSONDecodeError:
                            pass

    def on_event(self, callback: Callable[[Dict[str, Any]], None]):
        """
        Process events with a callback function

        Args:
            callback (Callable[[Dict[str, Any]], None]): Callback function to process events
        """
        for event in self:
            callback(event)

    def close(self):
        """
        Close the event stream and clean up resources
        """
        if not self._closed:
            self._closed = True
            if hasattr(self._response, "close"):
                try:
                    self._response.close()
                except Exception as e:
                    logger.warning("Error closing response: %s", e)

            # Clean up the streaming client if it exists
            if hasattr(self._response, "_streaming_client"):
                try:
                    self._response._streaming_client.close()
                except Exception as e:
                    logger.warning("Error closing streaming client: %s", e)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class StreamController:
    """
    Controller for managing streaming requests
    """

    def __init__(self):
        self._callbacks = {"on_data": None, "on_error": None, "on_complete": None}

    def on_data(self, callback: Callable[[Dict[str, Any]], None]):
        """
        Set callback for data events

        Args:
            callback (Callable[[Dict[str, Any]], None]): Data callback function

        Returns:
            StreamController: This controller instance
        """
        self._callbacks["on_data"] = callback
        return self

    def on_error(self, callback: Callable[[Exception], None]):
        """
        Set callback for error events

        Args:
            callback (Callable[[Exception], None]): Error callback function

        Returns:
            StreamController: This controller instance
        """
        self._callbacks["on_error"] = callback
        return self

    def on_complete(self, callback: Callable[[], None]):
        """
        Set callback for completion events

        Args:
            callback (Callable[[], None]): Completion callback function

        Returns:
            StreamController: This controller instance
        """
        self._callbacks["on_complete"] = callback
        return self

    def process_stream(self, stream: EventStream):
        """
        Process a stream with the configured callbacks

        Args:
            stream (EventStream): Event stream to process
        """
        try:
            for event in stream:
                if self._callbacks["on_data"]:
                    self._callbacks["on_data"](event)

            if self._callbacks["on_complete"]:
                self._callbacks["on_complete"]()

        except Exception as e:
            if self._callbacks["on_error"]:
                self._callbacks["on_error"](e)
            else:
                raise

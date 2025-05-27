"""
Simple RSS feed error handling utility.

This module provides a lightweight wrapper for RSS feed operations
to provide consistent error handling.
"""

import functools
import logging
from typing import Callable

logger = logging.getLogger(__name__)


class RSSError(Exception):
    """RSS feed error with contextual information."""

    def __init__(self, message: str, original: Exception = None):
        """Initialize RSS error.

        Args:
            message: Error message
            original: Original exception that was caught
        """
        self.original = original
        super().__init__(message)


def handle_rss_error(func: Callable) -> Callable:
    """Decorator for handling RSS errors consistently.

    Catches errors in RSS operations and transforms them into RSSError
    with appropriate context and logging.

    Args:
        func: Function to decorate

    Returns:
        Decorated function with error handling
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        """Wrapped function with error handling."""
        try:
            return func(*args, **kwargs)
        except RSSError:
            # Already a RSSError, just re-raise
            raise
        except ValueError as e:
            # Handle validation errors
            logger.error(f"RSS validation error in {func.__name__}: {str(e)}")
            raise RSSError(f"{str(e)}", e)
        except Exception as e:
            # Handle other errors
            logger.exception(f"RSS operation failed in {func.__name__}: {str(e)}")

            # Determine appropriate error message
            if "timeout" in str(e).lower():
                message = f"RSS feed request timed out: {str(e)}"
            elif "connection" in str(e).lower():
                message = f"Could not connect to RSS feed: {str(e)}"
            elif "not found" in str(e).lower() or "404" in str(e).lower():
                message = f"RSS feed not found: {str(e)}"
            elif "parse" in str(e).lower() or "xml" in str(e).lower():
                message = f"Invalid RSS feed format: {str(e)}"
            else:
                message = f"RSS feed processing error: {str(e)}"

            raise RSSError(message, e)

    return wrapper

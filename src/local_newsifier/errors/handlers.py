"""
Service-specific error handlers.

This module provides pre-configured handlers for specific services.
"""

import functools
from typing import Callable, Optional

from .error import handle_service_error, with_retry, with_timing

# Service-specific error messages with troubleshooting hints
ERROR_MESSAGES = {
    "apify": {
        "auth": "Apify API key is invalid or expired. Check your APIFY_TOKEN in settings.",
        "rate_limit": "Apify rate limit exceeded. Try again later or upgrade your plan.",
        "server": "Apify server is experiencing issues. Try again later.",
    },
    "rss": {
        "network": (
            "Could not connect to RSS feed. Check the feed URL and your internet connection."
        ),
        "parse": "RSS feed format is invalid or unsupported.",
        "not_found": "RSS feed not found. Check the feed URL.",
    },
    "web_scraper": {
        "network": "Could not connect to website. Check the URL and your internet connection.",
        "auth": "Website requires authentication or blocks automated access.",
        "parse": "Could not extract content from website. The site structure may have changed.",
    },
    "database": {
        "connection": "Could not connect to the database. Check database connection settings.",
        "timeout": "Database operation timed out. The database may be overloaded.",
        "integrity": "Database constraint violation. The operation violates database rules.",
        "not_found": "Requested record not found in the database.",
        "multiple": "Multiple records found where only one was expected.",
        "validation": "Invalid database request. Check input parameters.",
        "transaction": "Transaction error. The operation could not be completed.",
    },
}


def create_service_handler(
    service: str, retry_attempts: Optional[int] = 3, include_timing: bool = True
) -> Callable:
    """Create a combined handler for a service.

    Args:
        service: Service identifier ("apify", "rss", etc.)
        retry_attempts: Number of retry attempts (None to disable)
        include_timing: Whether to include timing

    Returns:
        A decorator that combines error handling, retry, and timing
    """

    def decorator(func: Callable) -> Callable:
        """Combined decorator for service handling."""
        # Start with the original function
        result = func

        # Add error handling (innermost decorator)
        result = handle_service_error(service)(result)

        # Add retry if requested
        if retry_attempts:
            result = with_retry(retry_attempts)(result)

        # Add timing if requested (outermost decorator)
        if include_timing:
            result = with_timing(service)(result)

        # Use proper wrapper to maintain function metadata
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return result(*args, **kwargs)

        return wrapper

    return decorator


# Pre-configured handlers for common services
handle_apify = create_service_handler("apify")
handle_rss = create_service_handler("rss")
handle_web_scraper = create_service_handler("web_scraper")
handle_database = create_service_handler("database")


def get_error_message(service: str, error_type: str) -> str:
    """Get service-specific error message with troubleshooting hints.

    Args:
        service: Service identifier
        error_type: Error type

    Returns:
        Error message with troubleshooting hints
    """
    # Try service-specific message
    if service in ERROR_MESSAGES and error_type in ERROR_MESSAGES[service]:
        return ERROR_MESSAGES[service][error_type]

    # Generic messages by error type
    generic_messages = {
        "network": "Network connectivity issue. Check your internet connection.",
        "timeout": "Request timed out. The service may be slow or unresponsive.",
        "rate_limit": "Rate limit exceeded. Try again later.",
        "auth": "Authentication failed. Check your credentials.",
        "parse": "Failed to parse response. The format may have changed.",
        "validation": "Input validation failed. Check your request parameters.",
        "not_found": "Resource not found. Check the resource identifier.",
        "server": "Server error. Try again later.",
        "unknown": "Unknown error occurred.",
    }

    return generic_messages.get(error_type, "An error occurred.")

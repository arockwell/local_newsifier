"""
RSS Feed-specific error handling.

This module provides specialized error handling for RSS feed operations.
"""

from typing import Dict, Any, Callable, Optional, cast
import functools
import re

from .handlers import create_service_handler, handle_cli_errors
from .error import ServiceError


# RSS-specific error types
RSS_ERROR_TYPES = {
    # XML parsing errors
    "xml_parse": {"transient": False, "retry": False, "exit_code": 10},
    
    # Feed format errors (RSS/Atom structure)
    "feed_format": {"transient": False, "retry": False, "exit_code": 11},
    
    # Feed validation errors (missing required elements)
    "feed_validation": {"transient": False, "retry": False, "exit_code": 12},
    
    # Feed URL errors (malformed URLs)
    "url": {"transient": False, "retry": False, "exit_code": 13},
    
    # Feed encoding errors
    "encoding": {"transient": False, "retry": False, "exit_code": 14},
}

# RSS-specific error messages with troubleshooting hints
RSS_ERROR_MESSAGES = {
    "network": "Could not connect to RSS feed. Check the feed URL and your internet connection.",
    "parse": "RSS feed format is invalid or unsupported. Verify the feed URL returns valid RSS/Atom content.",
    "xml_parse": "Failed to parse XML content. The feed may have syntax errors.",
    "feed_format": "Feed structure doesn't match expected RSS or Atom format. Verify it's a valid feed.",
    "feed_validation": "Required elements are missing from the feed. Check the feed structure.",
    "url": "Feed URL is malformed or invalid. Check the URL format.",
    "encoding": "Feed has encoding issues. Try a different encoding or report to feed provider.",
    "not_found": "RSS feed not found. The URL may be incorrect or the feed may have been removed.",
    "timeout": "Connection to RSS feed timed out. The server may be slow or unavailable."
}


def _classify_rss_error(error: Exception) -> tuple:
    """Classify an RSS-specific exception.
    
    Args:
        error: The exception to classify
        
    Returns:
        Tuple of (error_type, error_message)
    """
    error_str = str(error).lower()
    error_type = type(error).__name__
    
    # XML parsing errors
    if "xml" in error_str and ("parse" in error_str or "syntax" in error_str):
        return "xml_parse", f"XML parsing error: {error}"
    
    # Feed format errors
    if "no entries found" in error_str or "no items found" in error_str:
        return "feed_format", f"Invalid feed format (no entries): {error}"
    
    if "not a valid feed" in error_str:
        return "feed_format", f"Invalid feed format: {error}"
    
    # URL errors
    if "invalid url" in error_str or "malformed url" in error_str:
        return "url", f"Invalid feed URL: {error}"
    
    # Encoding errors
    if "encoding" in error_str or "decode" in error_str:
        return "encoding", f"Feed encoding error: {error}"
    
    # Network errors - requests lib raises ConnectionError
    if "connectionerror" in error_type.lower() or "connection" in error_str:
        return "network", f"Could not connect to feed: {error}"
    
    # Not found errors - requests raises HTTPError for 404
    if "404" in error_str:
        return "not_found", f"Feed not found: {error}"
    
    # Timeout errors
    if "timeout" in error_str or "timed out" in error_str:
        return "timeout", f"Connection timed out: {error}"
    
    # Fall back to standard classification
    return None, None


def handle_rss_service(func: Callable) -> Callable:
    """RSS-specific service error handler decorator.
    
    Extends the standard RSS handler with RSS-specific error classification.
    
    Args:
        func: The function to decorate
        
    Returns:
        Decorated function with RSS error handling
    """
    # Create a base handler first
    base_handler = create_service_handler("rss", retry_attempts=3)
    decorated_func = base_handler(func)
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return decorated_func(*args, **kwargs)
        except ServiceError as e:
            # If it's already a ServiceError but needs more specific classification
            if e.service == "rss" and e.error_type in ("parse", "unknown"):
                # Try to classify more specifically if it's a generic error
                rss_type, rss_message = _classify_rss_error(e.original) if e.original else (None, None)
                
                # Only reclassify if we found a more specific type
                if rss_type and rss_type != e.error_type:
                    # Create a new error with the more specific classification
                    raise ServiceError(
                        service="rss",
                        error_type=rss_type,
                        message=rss_message or str(e),
                        original=e.original,
                        context=e.context
                    )
            
            # Otherwise, just re-raise
            raise
    
    return wrapper


# CLI decorator specialized for RSS errors
handle_rss_cli = handle_cli_errors("rss")


def get_rss_error_message(error_type: str) -> str:
    """Get RSS-specific error message with troubleshooting hints.
    
    Args:
        error_type: Error type
        
    Returns:
        Error message with troubleshooting hints
    """
    return RSS_ERROR_MESSAGES.get(error_type, "An error occurred with the RSS feed.")
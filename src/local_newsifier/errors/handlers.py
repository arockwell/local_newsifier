"""
Generic service error handlers.

This module provides reusable error handlers for various services.
"""

import functools
from typing import Callable, Dict, Optional

# First import core types to avoid circular dependencies
from .error import ServiceError, handle_service_error, with_retry, with_timing


def create_service_handler(
    service: str, 
    retry_attempts: Optional[int] = None
) -> Callable:
    """Create a service-specific error handler with optional retry.
    
    Args:
        service: Service identifier
        retry_attempts: Number of retry attempts (optional)
        
    Returns:
        Decorator function for error handling
    """
    # Create base handler
    handler = handle_service_error(service)
    
    # Add retry if specified
    if retry_attempts:
        retry = with_retry(max_attempts=retry_attempts)
        
        def combined_decorator(func: Callable) -> Callable:
            # Apply handlers in reverse order (retry is outermost)
            return retry(handler(func))
            
        return combined_decorator
    
    # Otherwise just return the handler
    return handler


# Create service-specific handlers
handle_apify = create_service_handler("apify", retry_attempts=2)
handle_web_scraper = create_service_handler("web_scraper", retry_attempts=3)

# The handle_rss handler is defined in rss.py to avoid circular dependencies
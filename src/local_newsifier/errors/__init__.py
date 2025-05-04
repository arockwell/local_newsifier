"""
Streamlined error handling for external services.

This module provides a unified approach to handling errors from
external services like Apify, RSS feeds, and web scrapers.
"""

# Import core error components
from .error import (
    ServiceError,
    ERROR_TYPES,
    handle_service_error,
    handle_rss_service,
    with_timing,
    _classify_error,
)

# Import CLI error utilities
from .cli import (
    handle_cli_errors,
    format_cli_error,
    print_cli_error,
)

# Create service-specific handlers
handle_apify = handle_service_error("apify", retry_attempts=2)
handle_web_scraper = handle_service_error("web_scraper", retry_attempts=2)

# Create service-specific CLI handlers
handle_apify_cli = handle_cli_errors("apify")
handle_rss_cli = handle_cli_errors("rss")

# Define an alias for backwards compatibility
handle_rss = handle_rss_service

__all__ = [
    # Core components
    'ServiceError',
    'ERROR_TYPES',
    'handle_service_error',
    'with_timing',
    
    # Service handlers
    'handle_rss_service',
    'handle_apify', 
    'handle_rss',
    'handle_web_scraper',
    
    # CLI handlers
    'handle_cli_errors',
    'handle_apify_cli',
    'handle_rss_cli',
    'format_cli_error',
    'print_cli_error'
]
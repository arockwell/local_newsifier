"""
Streamlined error handling for external services.

This module provides a unified approach to handling errors from
external services like Apify, RSS feeds, and web scrapers.
"""

# Import error core components first to avoid circular dependencies
from .error import ServiceError, handle_service_error, with_retry, with_timing, ERROR_TYPES

# Import rss-specific components - this must come after error imports
from .rss import handle_rss_service, handle_rss_cli, RSS_ERROR_TYPES, get_rss_error_message

# Register RSS error types with the main ERROR_TYPES dictionary
ERROR_TYPES.update(RSS_ERROR_TYPES)

# Import other handlers
from .handlers import handle_apify, handle_rss, handle_web_scraper
from .cli import handle_cli_errors, handle_apify_cli

# Override the imported handles with their more specific implementations
handle_rss = handle_rss_service  # Use the more specific implementation
handle_rss_cli = handle_rss_cli  # Already correct but included for clarity

__all__ = [
    # Core components
    'ServiceError',
    'handle_service_error',
    'with_retry',
    'with_timing',
    'ERROR_TYPES',
    
    # RSS-specific components
    'handle_rss_service',
    'RSS_ERROR_TYPES',
    'get_rss_error_message',
    
    # Service handlers
    'handle_apify', 
    'handle_rss',
    'handle_web_scraper',
    
    # CLI handlers
    'handle_cli_errors',
    'handle_apify_cli',
    'handle_rss_cli'
]
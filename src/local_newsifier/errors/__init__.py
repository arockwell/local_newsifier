"""
Streamlined error handling for external services.

This module provides a unified approach to handling errors from
external services like Apify, RSS feeds, and web scrapers.

IMPORTANT: The order of imports in this module is critical to prevent circular dependencies.
The steps are:
1. First import core error components from error.py
2. Then import service-specific components 
3. Register service-specific error types with ERROR_TYPES
4. Finally import handlers that might depend on both error and service components
"""

# Import error core components first to avoid circular dependencies
from .error import ServiceError, handle_service_error, with_retry, with_timing, ERROR_TYPES

# Import other handlers - these must come after error imports
from .handlers import handle_apify, handle_web_scraper
from .cli import handle_cli_errors, handle_apify_cli

# Import rss-specific components - this must come after both error and handlers imports
from .rss import handle_rss_service, handle_rss_cli, RSS_ERROR_TYPES, get_rss_error_message

# Register RSS error types with the main ERROR_TYPES dictionary
ERROR_TYPES.update(RSS_ERROR_TYPES)

# Define an alias for the handle_rss function for backwards compatibility
handle_rss = handle_rss_service  # Use the more specific implementation

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
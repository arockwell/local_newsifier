"""
Simplified error handling framework.

This module provides a streamlined error handling system with reduced line count.
"""

# Import main components for easy access
from .simplified_error import ServiceError, create_handler, classify_error

# Import pre-configured handlers
from .simplified_handlers import (
    handle_apify, 
    handle_rss, 
    handle_web_scraper, 
    handle_database,
    get_error_message
)

# Import CLI handlers
from .simplified_cli import (
    handle_apify_cli,
    handle_rss_cli,
    handle_database_cli,
    handle_web_scraper_cli
)

__all__ = [
    # Core components
    'ServiceError',
    'create_handler',
    'classify_error',
    
    # Pre-configured handlers
    'handle_apify',
    'handle_rss',
    'handle_web_scraper',
    'handle_database',
    'get_error_message',
    
    # CLI handlers
    'handle_apify_cli',
    'handle_rss_cli',
    'handle_database_cli',
    'handle_web_scraper_cli'
]
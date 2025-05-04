"""
Streamlined error handling for external services and internal operations.

This module provides a unified approach to handling errors from
external services like Apify, RSS feeds, web scrapers, and internal
operations like database access.
"""

from .error import ServiceError, handle_service_error, with_retry, with_timing
from .handlers import handle_apify, handle_rss, handle_web_scraper, handle_database
from .cli import handle_cli_errors, handle_apify_cli, handle_rss_cli, handle_database_cli

__all__ = [
    'ServiceError',
    'handle_service_error',
    'with_retry',
    'with_timing',
    'handle_apify', 
    'handle_rss',
    'handle_web_scraper',
    'handle_database',
    'handle_cli_errors',
    'handle_apify_cli',
    'handle_rss_cli',
    'handle_database_cli'
]
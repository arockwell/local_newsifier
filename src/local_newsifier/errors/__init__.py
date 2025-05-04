"""
Streamlined error handling for external services and internal operations.

This module provides a unified approach to handling errors from
external services like Apify, RSS feeds, web scrapers, and internal
operations like database access.
"""

from .error import ServiceError, handle_service_error, with_retry, with_timing
from .handlers import handle_apify, handle_rss, handle_web_scraper
from .cli import handle_cli_errors, handle_apify_cli, handle_rss_cli, handle_database_cli
from .database import classify_database_error, handle_database_error, handle_database

__all__ = [
    'ServiceError',
    'handle_service_error',
    'with_retry',
    'with_timing',
    'handle_apify', 
    'handle_rss',
    'handle_web_scraper',
    'handle_database',
    'handle_database_error',
    'classify_database_error',
    'handle_cli_errors',
    'handle_apify_cli',
    'handle_rss_cli',
    'handle_database_cli'
]
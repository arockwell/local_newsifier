"""
Error handling module for external service integrations.

This module provides a unified approach to handling errors 
from external services like Apify, RSS feeds, and web scrapers.
"""

from .service_errors import ServiceError
from .decorators import (
    handle_apify_errors,
    handle_rss_errors,
    retry_apify_calls,
    retry_rss_calls,
    time_service_calls,
    handle_apify,
    handle_rss
)
from .cli import (
    handle_apify_cli,
    handle_rss_cli
)

__all__ = [
    'ServiceError',
    'handle_apify_errors',
    'handle_rss_errors',
    'retry_apify_calls',
    'retry_rss_calls',
    'time_service_calls',
    'handle_apify',
    'handle_rss',
    'handle_apify_cli',
    'handle_rss_cli'
]
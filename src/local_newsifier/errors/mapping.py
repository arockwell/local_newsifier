"""
Error mapping configurations for external service integrations.

This module defines the error type definitions and mappings from 
service-specific exceptions to standardized ServiceError types.
"""

from typing import Dict, List, Optional, Pattern, Tuple, Type, Union
import re
import requests
from urllib.error import URLError, HTTPError

# Standard error type definitions
# These provide metadata about different error types that can occur
ERROR_TYPES = {
    # Network connectivity issues
    "network": {
        "description": "Network connectivity issue",
        "is_transient": True, 
        "retry": True,
        "backoff_factor": 1.0
    },
    
    # Request timeout errors
    "timeout": {
        "description": "Request timed out",
        "is_transient": True,
        "retry": True,
        "backoff_factor": 1.5
    },
    
    # Rate limiting errors
    "rate_limit": {
        "description": "Rate limit exceeded",
        "is_transient": True,
        "retry": True,
        "backoff_factor": 2.0
    },
    
    # Authentication errors
    "authentication": {
        "description": "Authentication failed",
        "is_transient": False,
        "retry": False
    },
    
    # Response parsing errors
    "parse": {
        "description": "Failed to parse response",
        "is_transient": False,
        "retry": False
    },
    
    # Input validation errors
    "validation": {
        "description": "Input validation failed",
        "is_transient": False,
        "retry": False
    },
    
    # Resource not found errors
    "not_found": {
        "description": "Resource not found",
        "is_transient": False,
        "retry": False
    },
    
    # Server-side errors
    "server": {
        "description": "Server-side error",
        "is_transient": True,
        "retry": True,
        "backoff_factor": 1.0
    },
    
    # API errors
    "api": {
        "description": "API error",
        "is_transient": False,
        "retry": False
    },
    
    # Configuration errors
    "configuration": {
        "description": "Configuration error",
        "is_transient": False,
        "retry": False
    },
    
    # Unknown/unexpected errors
    "unknown": {
        "description": "Unknown error",
        "is_transient": False,
        "retry": False
    }
}

# Pattern type for error matching
PatternType = Optional[Union[Pattern, str]]

# Service-specific error mappings (Apify)
# Format: (exception_type, match_pattern, error_type, message_template)
APIFY_ERROR_MAPPINGS: List[Tuple[Type[Exception], PatternType, str, str]] = [
    # Network errors
    (requests.ConnectionError, None, "network", "Failed to connect to Apify API: {error}"),
    (requests.Timeout, None, "timeout", "Request to Apify API timed out after {timeout}s: {error}"),
    
    # Status code based errors
    (requests.HTTPError, re.compile(r"429"), "rate_limit", "Apify API rate limit exceeded: {error}"),
    (requests.HTTPError, re.compile(r"401|403"), "authentication", "Apify API authentication failed: {error}"),
    (requests.HTTPError, re.compile(r"404"), "not_found", "Apify resource not found: {error}"),
    (requests.HTTPError, re.compile(r"5\d\d"), "server", "Apify server error: {error}"),
    (requests.HTTPError, re.compile(r"4\d\d"), "validation", "Apify request validation failed: {error}"),
    
    # Parsing errors
    (ValueError, re.compile(r"JSON"), "parse", "Failed to parse Apify JSON response: {error}"),
    (TypeError, re.compile(r"NoneType"), "parse", "Unexpected None response from Apify: {error}"),
    
    # Configuration errors
    (ValueError, re.compile(r"token|api_key|apiKey"), "configuration", "Apify configuration error: {error}"),
    
    # Fallback for any other exception
    (Exception, None, "unknown", "Unknown Apify error: {error}")
]

# RSS Feed error mappings
RSS_ERROR_MAPPINGS: List[Tuple[Type[Exception], PatternType, str, str]] = [
    # Network errors
    (requests.ConnectionError, None, "network", "Failed to connect to RSS feed: {error}"),
    (URLError, None, "network", "Failed to connect to RSS feed: {error}"),
    (requests.Timeout, None, "timeout", "RSS feed request timed out: {error}"),
    
    # HTTP errors
    (HTTPError, re.compile(r"401|403"), "authentication", "RSS feed authentication failed: {error}"),
    (HTTPError, re.compile(r"404"), "not_found", "RSS feed not found: {error}"),
    (HTTPError, re.compile(r"429"), "rate_limit", "RSS feed rate limit exceeded: {error}"),
    (HTTPError, re.compile(r"5\d\d"), "server", "RSS feed server error: {error}"),
    
    # Parsing errors
    (ValueError, re.compile(r"XML|ParseError"), "parse", "Failed to parse RSS feed: {error}"),
    (SyntaxError, None, "parse", "RSS feed syntax error: {error}"),
    
    # Fallback
    (Exception, None, "unknown", "Unknown RSS feed error: {error}")
]

# Web Scraper error mappings
WEB_SCRAPER_ERROR_MAPPINGS: List[Tuple[Type[Exception], PatternType, str, str]] = [
    # Network errors
    (requests.ConnectionError, None, "network", "Failed to connect to website: {error}"),
    (requests.Timeout, None, "timeout", "Website request timed out: {error}"),
    
    # HTTP errors
    (requests.HTTPError, re.compile(r"403"), "authentication", "Access to website forbidden: {error}"),
    (requests.HTTPError, re.compile(r"404"), "not_found", "Web page not found: {error}"),
    (requests.HTTPError, re.compile(r"429"), "rate_limit", "Website rate limit exceeded: {error}"),
    (requests.HTTPError, re.compile(r"5\d\d"), "server", "Website server error: {error}"),
    
    # Parsing errors
    (ValueError, re.compile(r"parse|selector|xpath"), "parse", "Failed to parse website content: {error}"),
    
    # Fallback
    (Exception, None, "unknown", "Unknown web scraping error: {error}")
]

# Mappings registry
ERROR_MAPPINGS: Dict[str, List[Tuple[Type[Exception], PatternType, str, str]]] = {
    "apify": APIFY_ERROR_MAPPINGS,
    "rss": RSS_ERROR_MAPPINGS,
    "web_scraper": WEB_SCRAPER_ERROR_MAPPINGS
}

def get_error_mappings(service: str) -> List[Tuple[Type[Exception], PatternType, str, str]]:
    """Get error mappings for a specific service.
    
    Args:
        service: The service identifier.
        
    Returns:
        A list of error mapping tuples.
    """
    return ERROR_MAPPINGS.get(service, [])

def get_error_type_info(error_type: str) -> Dict:
    """Get metadata for an error type.
    
    Args:
        error_type: The error type identifier.
        
    Returns:
        Dictionary with error type metadata.
    """
    return ERROR_TYPES.get(error_type, ERROR_TYPES["unknown"])
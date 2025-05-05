"""
Simplified service-specific error handlers.

This module provides pre-configured handlers and error messages.
"""

from .simplified_error import create_handler

# Error messages with troubleshooting hints - combined into a single nested dict
ERROR_MESSAGES = {
    "apify": {
        "auth": "Apify API key is invalid or expired. Check your APIFY_TOKEN in settings.",
        "rate_limit": "Apify rate limit exceeded. Try again later or upgrade your plan.",
        "server": "Apify server is experiencing issues. Try again later.",
        "network": "Could not connect to Apify API. Check your internet connection.",
        "timeout": "Apify request timed out. The service may be slow or unresponsive."
    },
    "rss": {
        "network": "Could not connect to RSS feed. Check the feed URL and your internet connection.",
        "parse": "RSS feed format is invalid or unsupported.",
        "not_found": "RSS feed not found. Check the feed URL.",
        "timeout": "RSS feed request timed out. The server may be slow or unresponsive."
    },
    "web_scraper": {
        "network": "Could not connect to website. Check the URL and your internet connection.",
        "auth": "Website requires authentication or blocks automated access.",
        "parse": "Could not extract content from website. The site structure may have changed.",
        "timeout": "Website request timed out. The site may be slow or blocking scrapers."
    },
    "database": {
        "connection": "Could not connect to the database. Check database connection settings.",
        "timeout": "Database operation timed out. The database may be overloaded.",
        "integrity": "Database constraint violation. The operation violates database rules.",
        "not_found": "Requested record not found in the database.",
        "multiple": "Multiple records found where only one was expected.",
        "validation": "Invalid database request. Check input parameters.",
        "transaction": "Transaction error. The operation could not be completed."
    },
    # Generic messages for any service
    "generic": {
        "network": "Network connectivity issue. Check your internet connection.",
        "timeout": "Request timed out. The service may be slow or unresponsive.",
        "rate_limit": "Rate limit exceeded. Try again later.",
        "auth": "Authentication failed. Check your credentials.",
        "parse": "Failed to parse response. The format may have changed.",
        "validation": "Input validation failed. Check your request parameters.",
        "not_found": "Resource not found. Check the resource identifier.",
        "server": "Server error. Try again later.",
        "unknown": "Unknown error occurred."
    }
}

# Pre-configured handlers for common services using the combined create_handler
handle_apify = create_handler("apify")
handle_rss = create_handler("rss")
handle_web_scraper = create_handler("web_scraper")
handle_database = create_handler("database")

def get_error_message(service: str, error_type: str) -> str:
    """Get service-specific error message with troubleshooting hints."""
    # Try service-specific message
    if service in ERROR_MESSAGES and error_type in ERROR_MESSAGES[service]:
        return ERROR_MESSAGES[service][error_type]
    
    # Fall back to generic message
    return ERROR_MESSAGES["generic"].get(error_type, "An error occurred.")
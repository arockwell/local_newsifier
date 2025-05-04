"""
CLI error presentation utilities.

This module provides utilities for presenting service errors
in a user-friendly way in command-line interfaces.
"""

import sys
import functools
from typing import Callable, Dict, Optional
import click

from .service_errors import ServiceError

# Error exit codes for CLI commands
# These provide consistent exit codes for different error types
EXIT_CODES = {
    # Network errors
    "network": 2,
    
    # Timeout errors
    "timeout": 3,
    
    # Rate limit errors
    "rate_limit": 4,
    
    # Authentication errors
    "authentication": 5,
    
    # Parsing errors
    "parse": 6,
    
    # Validation errors
    "validation": 7,
    
    # Not found errors
    "not_found": 8,
    
    # Server errors
    "server": 9,
    
    # Configuration errors
    "configuration": 10,
    
    # Unknown/unexpected errors
    "unknown": 1
}

# User-friendly error message templates with troubleshooting hints
ERROR_MESSAGES = {
    # Network errors
    "network": "Network error: {message}\nTroubleshooting: Check your internet connection and try again.",
    
    # Timeout errors
    "timeout": "Timeout error: {message}\nTroubleshooting: The operation took too long. Try again later or increase the timeout.",
    
    # Rate limit errors
    "rate_limit": "Rate limit exceeded: {message}\nTroubleshooting: Wait before trying again or reduce request frequency.",
    
    # Authentication errors
    "authentication": "Authentication failed: {message}\nTroubleshooting: Check your API key or credentials.",
    
    # Parsing errors
    "parse": "Parse error: {message}\nTroubleshooting: The response format may have changed or is invalid.",
    
    # Validation errors
    "validation": "Validation error: {message}\nTroubleshooting: Check your input parameters.",
    
    # Not found errors
    "not_found": "Not found: {message}\nTroubleshooting: Verify that the resource exists.",
    
    # Server errors
    "server": "Server error: {message}\nTroubleshooting: The service is experiencing issues. Try again later.",
    
    # Configuration errors
    "configuration": "Configuration error: {message}\nTroubleshooting: Check your configuration settings.",
    
    # Unknown errors
    "unknown": "Error: {message}\nPlease report this issue if it persists."
}

# Service-specific error messages that override the defaults
SERVICE_ERROR_MESSAGES = {
    "apify": {
        "authentication": "Apify authentication failed: {message}\nTroubleshooting: Check your Apify API token in the configuration.",
        "rate_limit": "Apify rate limit exceeded: {message}\nTroubleshooting: The free Apify plan has usage limits. Wait before trying again."
    },
    "rss": {
        "network": "RSS feed connection error: {message}\nTroubleshooting: Check that the RSS feed URL is accessible.",
        "parse": "RSS feed parsing error: {message}\nTroubleshooting: The feed may be malformed or in an unsupported format."
    }
}

def get_error_message_template(service: str, error_type: str) -> str:
    """Get the error message template for a specific service and error type.
    
    Args:
        service: The service identifier.
        error_type: The error type.
        
    Returns:
        The error message template.
    """
    # Check for service-specific template
    service_templates = SERVICE_ERROR_MESSAGES.get(service, {})
    if error_type in service_templates:
        return service_templates[error_type]
    
    # Fall back to general template
    return ERROR_MESSAGES.get(error_type, ERROR_MESSAGES["unknown"])

def handle_service_error_cli(service: str) -> Callable:
    """Factory for CLI command error handlers.
    
    Args:
        service: The service identifier.
        
    Returns:
        A decorator for handling service errors in CLI commands.
    """
    
    def decorator(func: Callable) -> Callable:
        """Decorator for handling service errors in CLI commands.
        
        Args:
            func: The CLI command function to wrap.
            
        Returns:
            The wrapped CLI command function.
        """
        @click.pass_context
        @functools.wraps(func)
        def wrapper(ctx, *args, **kwargs):
            """Wrapped CLI command function with error handling.
            
            Args:
                ctx: The Click context.
                *args: Positional arguments to pass to the command.
                **kwargs: Keyword arguments to pass to the command.
                
            Returns:
                The result of the command.
            """
            try:
                return func(ctx, *args, **kwargs)
            except ServiceError as e:
                # Get message template for this error type
                template = get_error_message_template(e.service, e.error_type)
                
                # Format error message
                error_message = template.format(message=str(e))
                
                # Add debug info if verbose mode
                verbose = ctx.obj.get('verbose', False) if ctx.obj else False
                if verbose:
                    error_details = "\n\nDebug Information:"
                    error_details += f"\n  Service: {e.service}"
                    error_details += f"\n  Error Type: {e.error_type}" 
                    error_details += f"\n  Timestamp: {e.timestamp}"
                    
                    if e.context:
                        error_details += "\n  Context:"
                        for k, v in e.context.items():
                            error_details += f"\n    {k}: {v}"
                    
                    if e.original:
                        error_details += f"\n  Original Error: {type(e.original).__name__}: {str(e.original)}"
                        
                    error_message += error_details
                
                # Print error message
                click.secho(error_message, fg='red', err=True)
                
                # Get exit code
                exit_code = EXIT_CODES.get(e.error_type, 1)
                sys.exit(exit_code)
            except Exception as e:
                # For unhandled exceptions
                error_message = f"Unexpected error: {str(e)}"
                
                # Add traceback in verbose mode
                verbose = ctx.obj.get('verbose', False) if ctx.obj else False
                if verbose:
                    import traceback
                    error_message += f"\n\n{traceback.format_exc()}"
                
                click.secho(error_message, fg='red', err=True)
                sys.exit(1)
                
        return wrapper
    
    return decorator

# Specific CLI handlers
handle_apify_cli = handle_service_error_cli("apify")
handle_rss_cli = handle_service_error_cli("rss")
handle_web_scraper_cli = handle_service_error_cli("web_scraper")
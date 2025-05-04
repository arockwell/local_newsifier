"""
Command-line error handling utilities.

This module provides decorators and utilities for handling errors in CLI commands.
"""

import functools
import sys
from typing import Callable, Dict, Optional

import click

# First import core types to avoid circular dependencies
from .error import ServiceError, ERROR_TYPES


def handle_cli_errors(service: str) -> Callable:
    """Create a CLI-specific error handler decorator.
    
    Args:
        service: Service identifier
        
    Returns:
        Decorator function for CLI error handling
    """
    def decorator(func: Callable) -> Callable:
        """Decorate a CLI function with error handling."""
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            """Wrapped function with CLI error handling."""
            try:
                return func(*args, **kwargs)
            except ServiceError as e:
                # Get error details for CLI presentation
                ctx = click.get_current_context()
                verbose = ctx.obj.get("verbose", False) if ctx.obj else False
                
                # Show error message
                click.secho(f"Error: {e}", fg="red", err=True)
                
                # Show troubleshooting hint if available
                from .rss import get_rss_error_message
                if service == "rss" and e.error_type in get_rss_error_message.__globals__.get("RSS_ERROR_MESSAGES", {}):
                    hint = get_rss_error_message(e.error_type)
                    if hint:
                        click.secho(f"Hint: {hint}", fg="yellow", err=True)
                
                # Show context in verbose mode
                if verbose:
                    click.echo("Context:", err=True)
                    for key, value in e.context.items():
                        click.echo(f"  {key}: {value}", err=True)
                    
                    if e.original:
                        click.echo(f"Original error: {type(e.original).__name__}: {e.original}", err=True)
                
                # Exit with appropriate code
                sys.exit(e.exit_code)
            except Exception as e:
                # Handle unhandled exceptions
                click.secho(f"Unhandled error: {type(e).__name__}: {e}", fg="red", err=True)
                sys.exit(1)
        
        return wrapper
    
    return decorator


# Create service-specific CLI handlers
handle_apify_cli = handle_cli_errors("apify")
# The handle_rss_cli handler is defined in rss.py to avoid circular dependencies
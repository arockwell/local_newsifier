"""
Command-line error handling utilities.

This module provides decorators and utilities for handling errors in CLI commands.
"""

import functools
import sys
from typing import Callable, Dict, List, Optional, Tuple, Any, Union

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
                
                # Use the standardized formatting function
                print_cli_error(e, verbose)
                
                # Exit with appropriate code
                sys.exit(e.exit_code)
            except Exception as e:
                # Handle unhandled exceptions
                click.secho(f"Unhandled error: {type(e).__name__}: {e}", fg="red", err=True)
                sys.exit(1)
        
        return wrapper
    
    return decorator


def format_cli_error(
    error: ServiceError, 
    verbose: bool = False
) -> List[Tuple[str, Optional[str], Optional[bool]]]:
    """Format a ServiceError for CLI display.
    
    Returns a list of (message, color, bold) tuples ready for click.secho().
    
    Args:
        error: The ServiceError to format
        verbose: Whether to include verbose details
        
    Returns:
        List of formatted lines as (text, color, bold) tuples
    """
    lines = []
    
    # Main error line - always red and bold
    lines.append((f"Error: {error}", "red", True))
    
    # Get troubleshooting hint if available
    hint = None
    if hasattr(error, "service") and error.service == "rss":
        # Import here to avoid circular import
        try:
            from .rss import get_rss_error_message, RSS_ERROR_MESSAGES
            if error.error_type in RSS_ERROR_MESSAGES:
                hint = get_rss_error_message(error.error_type)
        except (ImportError, AttributeError):
            # Fallback if import fails or attribute doesn't exist
            pass
    
    # Add hint if available
    if hint:
        lines.append((f"Hint: {hint}", "yellow", False))
    
    # Add context info if verbose
    if verbose and hasattr(error, "context") and error.context:
        lines.append(("Context:", None, True))
        for key, value in error.context.items():
            lines.append((f"  {key}: {value}", None, False))
        
        if hasattr(error, "original") and error.original:
            orig_type = type(error.original).__name__
            lines.append((f"Original error: {orig_type}: {error.original}", None, False))
    
    return lines


# Helper to print formatted error
def print_cli_error(error: ServiceError, verbose: bool = False):
    """Print a formatted ServiceError to the console.
    
    Args:
        error: The ServiceError to print
        verbose: Whether to include verbose details
    """
    formatted_lines = format_cli_error(error, verbose)
    for text, color, bold in formatted_lines:
        click.secho(text, fg=color, bold=bold, err=True)


# Create service-specific CLI handlers
handle_apify_cli = handle_cli_errors("apify")
# The handle_rss_cli handler is defined in rss.py to avoid circular dependencies
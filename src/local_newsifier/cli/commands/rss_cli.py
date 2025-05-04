"""
CLI utilities for handling RSS errors in a user-friendly way.
"""

import functools
import sys
from typing import Callable

import click

from local_newsifier.errors.rss_error import RSSError


def handle_rss_cli_errors(func: Callable) -> Callable:
    """Decorator for CLI commands that handles RSS errors.
    
    Catches RSSError exceptions and displays them in a user-friendly format.
    
    Args:
        func: CLI command function to decorate
        
    Returns:
        Decorated function with error handling
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        """Wrapped function with error handling."""
        try:
            return func(*args, **kwargs)
        except RSSError as e:
            # Get more details from Click context
            ctx = click.get_current_context()
            verbose = ctx.obj.get("verbose", False) if ctx.obj else False
            
            # Display error with color
            click.echo(click.style(f"Error: {str(e)}", fg="red", bold=True), err=True)
            
            # Display troubleshooting hint
            if "timeout" in str(e).lower():
                hint = "The server is taking too long to respond. Try again later."
            elif "connection" in str(e).lower():
                hint = "Could not connect to the RSS feed. Check your internet connection."
            elif "not found" in str(e).lower():
                hint = "The RSS feed could not be found. Check that the URL is correct."
            elif "format" in str(e).lower() or "parse" in str(e).lower():
                hint = "The feed format is invalid or could not be parsed. Check that it's a valid RSS/Atom feed."
            elif "exists" in str(e).lower():
                hint = "A feed with this URL already exists. Use another URL or update the existing feed."
            else:
                hint = "There was a problem with the RSS feed operation. Check the details above."
            
            click.echo(click.style(f"Hint: {hint}", fg="yellow"), err=True)
            
            # Show detailed information in verbose mode
            if verbose and e.original:
                click.echo("\nAdditional information:", err=True)
                click.echo(f"Original error: {type(e.original).__name__}: {e.original}", err=True)
            
            # Exit with non-zero status
            sys.exit(1)
        except Exception as e:
            # Handle other exceptions
            click.echo(click.style(f"Unexpected error: {type(e).__name__}: {str(e)}", fg="red", bold=True), err=True)
            
            # Show traceback in verbose mode
            if click.get_current_context().obj and click.get_current_context().obj.get("verbose", False):
                import traceback
                click.echo("\nTraceback:", err=True)
                click.echo(traceback.format_exc(), err=True)
            
            sys.exit(1)
    
    return wrapper
"""
Simplified CLI error handling utilities.

This module provides decorators for CLI error presentation with reduced line count.
"""

import functools
import sys
import traceback
from typing import Callable

import click

from .simplified_error import ServiceError
from .simplified_handlers import get_error_message

def handle_cli_errors(service: str) -> Callable:
    """Create a decorator for CLI error handling with a simplified implementation."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except ServiceError as e:
                # Get context from Click
                ctx = click.get_current_context()
                verbose = ctx.obj.get('verbose', False) if ctx.obj else False
                
                # Display error and hint in red and yellow
                click.secho(str(e), fg='red', err=True)
                click.secho(f"Hint: {get_error_message(e.service, e.error_type)}", fg='yellow', err=True)
                
                # Show debug info in verbose mode
                if verbose:
                    click.echo("\nDebug Information:", err=True)
                    error_dict = e.to_dict()
                    
                    # Show basic error properties
                    for key in ['service', 'error_type', 'timestamp']:
                        click.echo(f"  {key}: {error_dict[key]}", err=True)
                    
                    # Show context if available
                    if e.context:
                        click.echo("  Context:", err=True)
                        for key, value in e.context.items():
                            click.echo(f"    {key}: {value}", err=True)
                
                sys.exit(e.exit_code)
                
            except Exception as e:
                # Handle unhandled exceptions
                ctx = click.get_current_context()
                verbose = ctx.obj.get('verbose', False) if ctx.obj else False
                
                click.secho(f"Unexpected error: {str(e)}", fg='red', err=True)
                
                if verbose:
                    click.echo(traceback.format_exc(), err=True)
                
                sys.exit(1)
                
        return wrapper
    
    return decorator

# Pre-configured CLI handlers
handle_apify_cli = handle_cli_errors("apify")
handle_rss_cli = handle_cli_errors("rss")
handle_database_cli = handle_cli_errors("database")
handle_web_scraper_cli = handle_cli_errors("web_scraper")
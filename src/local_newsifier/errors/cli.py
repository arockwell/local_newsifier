"""
CLI error handling utilities.

This module provides decorators for CLI error presentation.
"""

import functools
import sys
import traceback
from typing import Callable, Optional

import click

from .error import ServiceError
from .handlers import get_error_message


def handle_cli_errors(service: str) -> Callable:
    """Create a decorator for CLI error handling.
    
    Args:
        service: Service identifier
        
    Returns:
        A decorator for CLI commands
    """
    def decorator(func: Callable) -> Callable:
        """Decorate a CLI command with error handling."""
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            """Wrapped CLI command with error handling."""
            try:
                return func(*args, **kwargs)
            except ServiceError as e:
                # Get context from Click
                ctx = click.get_current_context()
                verbose = ctx.obj.get('verbose', False) if ctx.obj else False
                
                # Display error message with service-specific hints
                error_msg = str(e)
                hint = get_error_message(e.service, e.error_type)
                
                click.secho(error_msg, fg='red', err=True)
                click.secho(f"Hint: {hint}", fg='yellow', err=True)
                
                # Show debug info in verbose mode
                if verbose:
                    click.echo("\nDebug Information:", err=True)
                    for key, value in e.to_dict().items():
                        if key not in ('message', 'context'):
                            click.echo(f"  {key}: {value}", err=True)
                    
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
                    click.echo("\nTraceback:", err=True)
                    click.echo(traceback.format_exc(), err=True)
                
                sys.exit(1)
                
        return wrapper
    
    return decorator


# Pre-configured handlers for common services
handle_apify_cli = handle_cli_errors("apify")
handle_rss_cli = handle_cli_errors("rss")
"""
Production environment safeguards for CLI operations.

This module provides safeguards for operations that could be destructive
when run against production environments.
"""

import functools
from typing import Callable, Optional

import click

from local_newsifier.cli.config import get_config


def is_prod_environment() -> bool:
    """Check if we're running against a production environment.

    Returns:
        bool: True if the current environment is production
    """
    config = get_config()
    current_env = config.get_current_env()
    env_config = config.get_env_config(current_env)

    # Check if environment is explicitly marked as production - various indicators
    is_prod_by_name = current_env == "prod" or current_env == "production"
    is_prod_by_flag = env_config.get("is_production", "").lower() == "true"
    has_prod_in_name = "prod" in env_config.get("name", "").lower()

    return is_prod_by_name or is_prod_by_flag or has_prod_in_name


def require_confirmation(
    message: Optional[str] = None, default: bool = False, abort: bool = True
) -> Callable:
    """Decorator to require confirmation for potentially destructive operations.

    Args:
        message: Custom confirmation message (default: generated from environment)
        default: Default answer if user just hits Enter
        abort: Whether to abort if confirmation fails

    Returns:
        Callable: Decorated function
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Check if we're in production
            if is_prod_environment():
                # Generate confirmation message if not provided
                prompt = message
                if not prompt:
                    # Get environment name for the message
                    config = get_config()
                    current_env = config.get_current_env()
                    env_config = config.get_env_config(current_env)
                    env_name = env_config.get("name", current_env)

                    # Extract command name from function
                    command_name = func.__name__.replace("_", " ")
                    # Keep line length under 100 chars
                    prompt = (
                        f"You are about to run {command_name} on "
                        f"PRODUCTION environment {env_name}. Continue?"
                    )

                # Ask for confirmation
                if not click.confirm(
                    click.style(prompt, fg="yellow", bold=True), default=default
                ):
                    if abort:
                        click.echo("Operation aborted.")
                        return None

            # If we're not in production or confirmation passed, run the function
            return func(*args, **kwargs)

        return wrapper

    return decorator


def prod_warning(func: Callable) -> Callable:
    """Decorator to display a warning when running against a production environment.

    This decorator doesn't require confirmation, it just displays a warning.

    Args:
        func: Function to decorate

    Returns:
        Callable: Decorated function
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Check if we're in production
        if is_prod_environment():
            # Get environment name for the message
            config = get_config()
            current_env = config.get_current_env()
            env_config = config.get_env_config(current_env)
            env_name = env_config.get("name", current_env)

            # Display warning
            click.echo(
                click.style(
                    f"⚠️  Running in PRODUCTION environment: {env_name}",
                    fg="yellow",
                    bold=True,
                )
            )

        # Run the function
        return func(*args, **kwargs)

    return wrapper

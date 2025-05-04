"""
Local Newsifier CLI - Main Entry Point.

The `nf` command is the entry point for the Local Newsifier CLI.
This module provides a foundation for managing RSS feeds and other local newsifier
operations from the command line.
"""

import logging
import sys

import click

from local_newsifier.cli.config import get_config

# Set up logger
logger = logging.getLogger(__name__)


@click.group()
@click.version_option(version="0.1.0")
@click.option(
    "--env", help="Environment to use (dev, staging, prod, etc.)", envvar="NF_ENV"
)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
def cli(env, verbose):
    """
    Local Newsifier CLI - A tool for managing local news data.

    This CLI provides commands for managing RSS feeds, processing articles,
    and analyzing news data.

    Use --env to specify which environment to use, or set the
    NF_ENV environment variable.
    """
    # Configure logging
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=log_level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Apply environment configuration if specified
    if env:
        config = get_config()

        # Check if environment exists
        if env not in config.get_env_names():
            click.echo(
                click.style(f"Error: Environment '{env}' not found", fg="red"), err=True
            )
            click.echo(f"Available environments: {', '.join(config.get_env_names())}")
            click.echo(f"Use 'nf config set-env {env}' to create it")
            sys.exit(1)

        # Apply environment configuration to settings
        applied_vars = config.apply_env_to_settings(env)
        if verbose:
            click.echo(f"Using environment: {env}")
            # Only show applied var names, not values (for security)
            if applied_vars:
                click.echo(f"Applied variables: {', '.join(applied_vars.keys())}")
    else:
        # Apply default environment
        config = get_config()
        default_env = config.get_current_env()
        applied_vars = config.apply_env_to_settings()
        if verbose:
            click.echo(f"Using default environment: {default_env}")
            if applied_vars:
                click.echo(f"Applied variables: {', '.join(applied_vars.keys())}")


def is_apify_command():
    """Check if the user is trying to run an apify command.

    This helps us avoid loading dependencies that have SQLite requirements
    when they're not needed.

    Returns:
        bool: True if the command is apify-related
    """
    # Check if 'apify' is in the command arguments
    return len(sys.argv) > 1 and sys.argv[1] == "apify"


# Conditionally load commands to avoid unnecessary dependencies
if is_apify_command():
    # Only load the apify command if it's being used
    from local_newsifier.cli.commands.apify import apify_group

    cli.add_command(apify_group)
else:
    # Load all other command groups
    from local_newsifier.cli.commands.apify import apify_group
    from local_newsifier.cli.commands.config import config_group
    from local_newsifier.cli.commands.db import db_group
    from local_newsifier.cli.commands.feeds import feeds_group

    cli.add_command(feeds_group)
    cli.add_command(db_group)
    cli.add_command(apify_group)
    cli.add_command(config_group)


def main():
    """Run the CLI application."""
    try:
        cli()
    except Exception as e:
        click.echo(click.style(f"Error: {str(e)}", fg="red"), err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

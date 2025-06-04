"""
Local Newsifier CLI - Main Entry Point

The `nf` command is the entry point for the Local Newsifier CLI.
This module provides a foundation for managing RSS feeds and other local newsifier
operations from the command line.
"""

import sys

import click
from tabulate import tabulate


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """
    Local Newsifier CLI - A tool for managing local news data.

    This CLI provides commands for managing RSS feeds, processing articles,
    and analyzing news data.
    """
    pass


def is_apify_command():
    """Check if the user is trying to run an apify command.

    This helps us avoid loading dependencies that have SQLite requirements
    when they're not needed.

    Returns:
        bool: True if the command is apify-related
    """
    # Check if 'apify' is in the command arguments
    return len(sys.argv) > 1 and (sys.argv[1] == "apify" or sys.argv[1] == "apify-config")


# Conditionally load commands to avoid unnecessary dependencies
if is_apify_command():
    # Only load the apify command if it's being used
    if sys.argv[1] == "apify":
        from local_newsifier.cli.commands.apify import apify_group

        cli.add_command(apify_group)
    elif sys.argv[1] == "apify-config":
        from local_newsifier.cli.commands.apify_config import apify_config_group

        cli.add_command(apify_config_group)
else:
    # Load all other command groups
    from local_newsifier.cli.commands.apify import apify_group
    from local_newsifier.cli.commands.apify_config import apify_config_group
    from local_newsifier.cli.commands.db import db_group
    from local_newsifier.cli.commands.feeds import feeds_group

    cli.add_command(feeds_group)
    cli.add_command(db_group)
    cli.add_command(apify_group)
    cli.add_command(apify_config_group)


def main():
    """Run the CLI application."""
    try:
        cli()
    except Exception as e:
        click.echo(click.style(f"Error: {str(e)}", fg="red"), err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

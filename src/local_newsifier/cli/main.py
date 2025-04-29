"""
Local Newsifier CLI - Main Entry Point

The `nf` command is the entry point for the Local Newsifier CLI.
This module provides a foundation for managing RSS feeds and other local newsifier
operations from the command line.
"""

import sys
import click
from tabulate import tabulate

from local_newsifier.cli.commands.feeds import feeds_group
from local_newsifier.cli.commands.db import db_group
from local_newsifier.cli.commands.apify import apify_group


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """
    Local Newsifier CLI - A tool for managing local news data.
    
    This CLI provides commands for managing RSS feeds, processing articles,
    and analyzing news data.
    """
    pass


# Add command groups
cli.add_command(feeds_group)
cli.add_command(db_group)
cli.add_command(apify_group)


def main():
    """Run the CLI application."""
    try:
        cli()
    except Exception as e:
        click.echo(click.style(f"Error: {str(e)}", fg="red"), err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

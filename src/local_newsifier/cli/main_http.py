"""
Local Newsifier CLI - Main Entry Point with HTTP client support.

The `nf` command is the entry point for the Local Newsifier CLI.
This version uses HTTP client to communicate with the FastAPI backend,
eliminating event loop conflicts.
"""

import sys

import click


@click.group()
@click.version_option(version="0.1.0")
@click.option("--api-url", envvar="NEWSIFIER_API_URL", help="API base URL")
@click.pass_context
def cli(ctx, api_url):
    """
    Local Newsifier CLI - A tool for managing local news data.

    This CLI provides commands for managing RSS feeds, processing articles,
    and analyzing news data through HTTP API.
    """
    # Store API URL in context for child commands
    ctx.ensure_object(dict)
    ctx.obj["api_url"] = api_url


def is_apify_command():
    """Check if the user is trying to run an apify command.

    This helps us avoid loading dependencies that have SQLite requirements
    when they're not needed.

    Returns:
        bool: True if the command is apify-related
    """
    # Check if 'apify' is in the command arguments
    return len(sys.argv) > 1 and (sys.argv[1] == "apify" or sys.argv[1] == "apify-config")


# Load HTTP-based command groups
from local_newsifier.cli.commands.db_http import db_group
from local_newsifier.cli.commands.feeds_http import feeds_group

cli.add_command(feeds_group)
cli.add_command(db_group)

# TODO: Migrate apify commands to HTTP when ready
if is_apify_command():
    # Only load the apify command if it's being used
    if sys.argv[1] == "apify":
        from local_newsifier.cli.commands.apify import apify_group

        cli.add_command(apify_group)
    elif sys.argv[1] == "apify-config":
        from local_newsifier.cli.commands.apify_config import apify_config_group

        cli.add_command(apify_config_group)
else:
    # Load apify commands for help display
    from local_newsifier.cli.commands.apify import apify_group
    from local_newsifier.cli.commands.apify_config import apify_config_group

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

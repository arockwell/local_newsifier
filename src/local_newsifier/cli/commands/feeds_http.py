"""
RSS Feeds management commands using HTTP client.

This module provides commands for managing RSS feeds through HTTP API:
- Listing feeds
- Adding new feeds
- Showing feed details
- Removing feeds
- Processing feeds
- Fetching all active feeds
- Updating feed properties
"""

import json
import sys

import click
from tabulate import tabulate

from local_newsifier.cli.http_client import NewsifierAPIError, NewsifierClient


@click.group(name="feeds")
@click.pass_context
def feeds_group(ctx):
    """Manage RSS feeds."""
    # Initialize HTTP client in context
    ctx.ensure_object(dict)
    api_url = ctx.obj.get("api_url")
    ctx.obj["client"] = NewsifierClient(base_url=api_url)


@feeds_group.command(name="list")
@click.option("--active-only", is_flag=True, help="Show only active feeds")
@click.option("--json", "json_output", is_flag=True, help="Output as JSON")
@click.option("--limit", type=int, default=100, help="Maximum number of feeds to display")
@click.option("--skip", type=int, default=0, help="Number of feeds to skip")
@click.pass_context
def list_feeds(ctx, active_only, json_output, limit, skip):
    """List all feeds with optional filtering."""
    client = ctx.obj["client"]

    try:
        with client:
            feeds = client.list_feeds(active_only=active_only, limit=limit, skip=skip)
    except NewsifierAPIError as e:
        click.echo(click.style(f"Error: {e.detail}", fg="red"), err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(click.style(f"Unexpected error: {str(e)}", fg="red"), err=True)
        sys.exit(1)

    if json_output:
        click.echo(json.dumps(feeds, indent=2))
        return

    if not feeds:
        click.echo("No feeds found.")
        return

    # Format data for table
    table_data = []
    for feed in feeds:
        table_data.append(
            [
                feed["id"],
                feed["name"],
                feed["url"][:50] + "..." if len(feed["url"]) > 50 else feed["url"],
                "✓" if feed["is_active"] else "✗",
                feed.get("last_fetched_at", "Never"),
            ]
        )

    headers = ["ID", "Name", "URL", "Active", "Last Fetched"]
    click.echo(tabulate(table_data, headers=headers, tablefmt="simple"))
    click.echo(f"\nTotal feeds: {len(feeds)}")


@feeds_group.command(name="add")
@click.argument("url")
@click.option("--name", help="Custom name for the feed")
@click.option("--description", help="Description of the feed")
@click.option("--json", "json_output", is_flag=True, help="Output as JSON")
@click.pass_context
def add_feed(ctx, url, name, description, json_output):
    """Add a new RSS feed."""
    client = ctx.obj["client"]

    try:
        with client:
            feed = client.add_feed(url=url, name=name, description=description)
    except NewsifierAPIError as e:
        if e.status_code == 400:
            click.echo(click.style(f"Error: {e.detail}", fg="red"), err=True)
        else:
            click.echo(click.style(f"Error: {e.detail}", fg="red"), err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(click.style(f"Unexpected error: {str(e)}", fg="red"), err=True)
        sys.exit(1)

    if json_output:
        click.echo(json.dumps(feed, indent=2))
        return

    click.echo(click.style(f"✓ Added feed: {feed['name']} (ID: {feed['id']})", fg="green"))


@feeds_group.command(name="show")
@click.argument("feed_id", type=int)
@click.option("--json", "json_output", is_flag=True, help="Output as JSON")
@click.pass_context
def show_feed(ctx, feed_id, json_output):
    """Show details for a specific feed."""
    client = ctx.obj["client"]

    try:
        with client:
            feed = client.get_feed(feed_id)
    except NewsifierAPIError as e:
        if e.status_code == 404:
            click.echo(click.style(f"Error: Feed with ID {feed_id} not found", fg="red"), err=True)
        else:
            click.echo(click.style(f"Error: {e.detail}", fg="red"), err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(click.style(f"Unexpected error: {str(e)}", fg="red"), err=True)
        sys.exit(1)

    if json_output:
        click.echo(json.dumps(feed, indent=2))
        return

    # Display feed details
    click.echo(click.style(f"Feed Details (ID: {feed['id']})", fg="green", bold=True))
    click.echo(f"Name: {feed['name']}")
    click.echo(f"URL: {feed['url']}")
    if feed.get("description"):
        click.echo(f"Description: {feed['description']}")
    click.echo(f"Active: {'Yes' if feed['is_active'] else 'No'}")
    click.echo(f"Created: {feed['created_at']}")
    click.echo(f"Updated: {feed['updated_at']}")
    click.echo(f"Last Fetched: {feed.get('last_fetched_at', 'Never')}")

    # Show recent logs if available
    if feed.get("recent_logs"):
        click.echo(click.style("\nRecent Processing Logs:", fg="cyan", bold=True))

        log_table = []
        for log in feed["recent_logs"]:
            log_table.append(
                [
                    log["id"],
                    log["started_at"],
                    log["completed_at"] or "In Progress",
                    log["status"],
                    log["articles_found"] or 0,
                    log["articles_added"] or 0,
                ]
            )

        log_headers = ["ID", "Started At", "Completed At", "Status", "Found", "Added"]
        click.echo(tabulate(log_table, headers=log_headers, tablefmt="simple"))


@feeds_group.command(name="remove")
@click.argument("feed_id", type=int)
@click.confirmation_option(prompt="Are you sure you want to remove this feed?")
@click.pass_context
def remove_feed(ctx, feed_id):
    """Remove a feed."""
    client = ctx.obj["client"]

    try:
        with client:
            result = client.delete_feed(feed_id)
    except NewsifierAPIError as e:
        if e.status_code == 404:
            click.echo(click.style(f"Error: Feed with ID {feed_id} not found", fg="red"), err=True)
        else:
            click.echo(click.style(f"Error: {e.detail}", fg="red"), err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(click.style(f"Unexpected error: {str(e)}", fg="red"), err=True)
        sys.exit(1)

    click.echo(click.style(f"✓ {result['message']}", fg="green"))


@feeds_group.command(name="update")
@click.argument("feed_id", type=int)
@click.option("--name", help="New name for the feed")
@click.option("--description", help="New description for the feed")
@click.option("--active/--inactive", default=None, help="Set feed active status")
@click.option("--json", "json_output", is_flag=True, help="Output as JSON")
@click.pass_context
def update_feed(ctx, feed_id, name, description, active, json_output):
    """Update feed properties."""
    client = ctx.obj["client"]

    # Check if any update was provided
    if name is None and description is None and active is None:
        click.echo(
            click.style(
                "Error: No updates provided. Use --name, --description, or --active/--inactive",
                fg="red",
            ),
            err=True,
        )
        sys.exit(1)

    try:
        with client:
            feed = client.update_feed(
                feed_id=feed_id, name=name, description=description, is_active=active
            )
    except NewsifierAPIError as e:
        if e.status_code == 404:
            click.echo(click.style(f"Error: Feed with ID {feed_id} not found", fg="red"), err=True)
        else:
            click.echo(click.style(f"Error: {e.detail}", fg="red"), err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(click.style(f"Unexpected error: {str(e)}", fg="red"), err=True)
        sys.exit(1)

    if json_output:
        click.echo(json.dumps(feed, indent=2))
        return

    click.echo(click.style(f"✓ Updated feed: {feed['name']} (ID: {feed['id']})", fg="green"))
    if name:
        click.echo(f"  Name: {feed['name']}")
    if description is not None:
        click.echo(f"  Description: {feed['description'] or '(removed)'}")
    if active is not None:
        click.echo(f"  Active: {'Yes' if feed['is_active'] else 'No'}")


@feeds_group.command(name="process")
@click.argument("feed_id", type=int)
@click.option("--json", "json_output", is_flag=True, help="Output as JSON")
@click.pass_context
def process_feed(ctx, feed_id, json_output):
    """Process a specific feed immediately."""
    client = ctx.obj["client"]

    click.echo(f"Processing feed {feed_id}...")

    try:
        with client:
            result = client.process_feed(feed_id)
    except NewsifierAPIError as e:
        if e.status_code == 404:
            click.echo(click.style(f"Error: Feed with ID {feed_id} not found", fg="red"), err=True)
        else:
            click.echo(click.style(f"Error: {e.detail}", fg="red"), err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(click.style(f"Unexpected error: {str(e)}", fg="red"), err=True)
        sys.exit(1)

    if json_output:
        click.echo(json.dumps(result, indent=2))
        return

    # Display processing results
    status = result.get("status", "unknown")
    if status == "success":
        click.echo(click.style("✓ Feed processed successfully", fg="green"))
        click.echo(f"  Articles found: {result.get('articles_found', 0)}")
        click.echo(f"  Articles added: {result.get('articles_added', 0)}")
        if result.get("message"):
            click.echo(f"  Message: {result['message']}")
    else:
        click.echo(click.style(f"✗ Feed processing failed: {status}", fg="red"))
        if result.get("error"):
            click.echo(f"  Error: {result['error']}")


@feeds_group.command(name="fetch-all")
@click.option("--json", "json_output", is_flag=True, help="Output as JSON")
@click.pass_context
def fetch_all_feeds(ctx, json_output):
    """Process all active feeds."""
    client = ctx.obj["client"]

    click.echo("Processing all active feeds...")

    try:
        with client:
            result = client.process_all_feeds()
    except NewsifierAPIError as e:
        click.echo(click.style(f"Error: {e.detail}", fg="red"), err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(click.style(f"Unexpected error: {str(e)}", fg="red"), err=True)
        sys.exit(1)

    if json_output:
        click.echo(json.dumps(result, indent=2))
        return

    # Display summary
    total_processed = result.get("processed", 0)
    click.echo(click.style(f"\n✓ Processed {total_processed} feeds", fg="green", bold=True))

    if result.get("results"):
        # Show results table
        table_data = []
        total_found = 0
        total_added = 0

        for feed_result in result["results"]:
            status = feed_result.get("status", "unknown")
            found = feed_result.get("articles_found", 0)
            added = feed_result.get("articles_added", 0)

            table_data.append(
                [
                    feed_result.get("feed_id", "?"),
                    feed_result.get("feed_name", "Unknown"),
                    status,
                    found,
                    added,
                    feed_result.get("error", "") if status != "success" else "",
                ]
            )

            total_found += found
            total_added += added

        headers = ["Feed ID", "Name", "Status", "Found", "Added", "Error"]
        click.echo("\n" + tabulate(table_data, headers=headers, tablefmt="simple"))

        # Summary
        click.echo(f"\nTotal articles found: {total_found}")
        click.echo(f"Total articles added: {total_added}")

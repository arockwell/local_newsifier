"""
Database diagnostics commands using HTTP client.

This module provides commands for inspecting and managing database state through HTTP API:
- Viewing table statistics
- Checking for duplicate records
- Analyzing data integrity
- Showing detailed entity information
"""

import json
import sys
from typing import Optional

import click
from tabulate import tabulate

from local_newsifier.cli.http_client import NewsifierAPIError, NewsifierClient


@click.group(name="db")
@click.pass_context
def db_group(ctx):
    """Inspect and manage database state."""
    # Initialize HTTP client in context
    ctx.ensure_object(dict)
    api_url = ctx.obj.get("api_url")
    ctx.obj["client"] = NewsifierClient(base_url=api_url)


@db_group.command(name="stats")
@click.option("--json", "json_output", is_flag=True, help="Output as JSON")
@click.pass_context
def db_stats(ctx, json_output: bool):
    """Show database statistics for all major tables."""
    client = ctx.obj["client"]

    try:
        with client:
            stats = client.get_db_stats()
    except NewsifierAPIError as e:
        click.echo(click.style(f"Error: {e.detail}", fg="red"), err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(click.style(f"Unexpected error: {str(e)}", fg="red"), err=True)
        sys.exit(1)

    # Output stats
    if json_output:
        click.echo(json.dumps(stats, indent=2))
        return

    # Display stats in a human-readable format
    click.echo(click.style("Database Statistics", fg="green", bold=True))

    # Articles table
    click.echo(click.style("\nArticles:", fg="cyan", bold=True))
    click.echo(f"Total count: {stats['articles']['count']}")
    if stats["articles"]["latest"]:
        click.echo(f"Most recent: {stats['articles']['latest']}")
    if stats["articles"]["oldest"]:
        click.echo(f"Oldest: {stats['articles']['oldest']}")

    # RSS Feeds table
    click.echo(click.style("\nRSS Feeds:", fg="cyan", bold=True))
    click.echo(f"Total count: {stats['rss_feeds']['count']}")
    click.echo(f"Active: {stats['rss_feeds']['active']}")
    click.echo(f"Inactive: {stats['rss_feeds']['inactive']}")

    # Processing Logs table
    click.echo(click.style("\nFeed Processing Logs:", fg="cyan", bold=True))
    click.echo(f"Total count: {stats['feed_processing_logs']['count']}")

    # Entities table
    click.echo(click.style("\nEntities:", fg="cyan", bold=True))
    click.echo(f"Total count: {stats['entities']['count']}")


@db_group.command(name="duplicates")
@click.option("--limit", type=int, default=10, help="Maximum number of duplicates to display")
@click.option("--json", "json_output", is_flag=True, help="Output as JSON")
@click.pass_context
def check_duplicates(ctx, limit: int, json_output: bool):
    """Find duplicate articles (same URL) and show details."""
    client = ctx.obj["client"]

    try:
        with client:
            results = client.get_duplicates(limit=limit)
    except NewsifierAPIError as e:
        click.echo(click.style(f"Error: {e.detail}", fg="red"), err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(click.style(f"Unexpected error: {str(e)}", fg="red"), err=True)
        sys.exit(1)

    if not results:
        click.echo("No duplicate articles found.")
        return

    # Output results
    if json_output:
        click.echo(json.dumps(results, indent=2))
        return

    # Display in human-readable format
    click.echo(
        click.style(f"Found {len(results)} URLs with duplicate articles:", fg="yellow", bold=True)
    )

    for idx, result in enumerate(results):
        click.echo(click.style(f"\n{idx + 1}. URL: {result['url']}", fg="cyan"))
        click.echo(f"   Number of duplicates: {result['count']}")

        table_data = []
        for article in result["articles"]:
            table_data.append(
                [
                    article["id"],
                    article["title"] or "(No title)",
                    article["created_at"],
                    article["status"],
                    article["content_len"],
                ]
            )

        headers = ["ID", "Title", "Created At", "Status", "Content Length"]
        click.echo(tabulate(table_data, headers=headers, tablefmt="simple"))


@db_group.command(name="articles")
@click.option("--source", help="Filter by article source")
@click.option("--status", help="Filter by article status")
@click.option("--before", help="Show articles created before date (YYYY-MM-DD)")
@click.option("--after", help="Show articles created after date (YYYY-MM-DD)")
@click.option("--limit", type=int, default=10, help="Maximum number of articles to display")
@click.option("--json", "json_output", is_flag=True, help="Output as JSON")
@click.pass_context
def list_articles(
    ctx,
    source: Optional[str],
    status: Optional[str],
    before: Optional[str],
    after: Optional[str],
    limit: int,
    json_output: bool,
):
    """List articles with filtering options."""
    client = ctx.obj["client"]

    try:
        with client:
            results = client.list_articles(
                source=source, status=status, before=before, after=after, limit=limit
            )
    except NewsifierAPIError as e:
        if e.status_code == 400:
            click.echo(click.style(f"Error: {e.detail}", fg="red"), err=True)
        else:
            click.echo(click.style(f"Error: {e.detail}", fg="red"), err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(click.style(f"Unexpected error: {str(e)}", fg="red"), err=True)
        sys.exit(1)

    if not results:
        click.echo("No articles found matching the criteria.")
        return

    # Output results
    if json_output:
        click.echo(json.dumps(results, indent=2))
        return

    # Display in human-readable format
    click.echo(click.style(f"Articles ({len(results)} results):", fg="green", bold=True))

    table_data = []
    for article in results:
        title = article["title"]
        if title and len(title) > 40:
            title = title[:37] + "..."

        url = article["url"]
        if url and len(url) > 40:
            url = url[:37] + "..."

        table_data.append(
            [
                article["id"],
                title or "(No title)",
                url,
                article["source"],
                article["status"],
                article["created_at"],
                article["content_len"],
            ]
        )

    headers = ["ID", "Title", "URL", "Source", "Status", "Created At", "Content Length"]
    click.echo(tabulate(table_data, headers=headers, tablefmt="simple"))


@db_group.command(name="inspect")
@click.argument("table", type=click.Choice(["article", "rss_feed", "feed_log", "entity"]))
@click.argument("id", type=int)
@click.option("--json", "json_output", is_flag=True, help="Output as JSON")
@click.pass_context
def inspect_record(ctx, table: str, id: int, json_output: bool):
    """Inspect a specific database record in detail."""
    client = ctx.obj["client"]

    try:
        with client:
            result = client.inspect_record(table, id)
    except NewsifierAPIError as e:
        if e.status_code == 404:
            click.echo(click.style(f"Error: {e.detail}", fg="red"), err=True)
        else:
            click.echo(click.style(f"Error: {e.detail}", fg="red"), err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(click.style(f"Unexpected error: {str(e)}", fg="red"), err=True)
        sys.exit(1)

    # Output results
    if json_output:
        click.echo(json.dumps(result, indent=2))
        return

    # Display in human-readable format
    click.echo(click.style(f"{table.upper()} (ID: {id})", fg="green", bold=True))

    # Display the data in a table format
    table_data = []
    for key, value in result.items():
        if key == "recent_logs":
            continue  # Handle logs separately
        table_data.append([key, value])

    click.echo(tabulate(table_data, headers=["Field", "Value"], tablefmt="simple"))

    # Show logs if available
    if table == "rss_feed" and result.get("recent_logs"):
        click.echo(click.style("\nRecent Processing Logs:", fg="cyan", bold=True))

        log_table = []
        for log in result["recent_logs"]:
            status_str = log["status"]

            log_table.append(
                [
                    log["id"],
                    log["started_at"],
                    log["completed_at"] or "",
                    status_str,
                    log["articles_found"] or 0,
                    log["articles_added"] or 0,
                    log["error_message"] or "",
                ]
            )

        log_headers = ["ID", "Started At", "Completed At", "Status", "Found", "Added", "Error"]
        click.echo(tabulate(log_table, headers=log_headers, tablefmt="simple"))


@db_group.command(name="purge-duplicates")
@click.option(
    "--dry-run", is_flag=True, help="Show what would be deleted without actually deleting"
)
@click.option("--json", "json_output", is_flag=True, help="Output as JSON")
@click.confirmation_option(prompt="This will delete duplicate articles. Are you sure?")
@click.pass_context
def purge_duplicates(ctx, dry_run: bool, json_output: bool):
    """Remove duplicate articles, keeping the oldest version."""
    client = ctx.obj["client"]

    try:
        with client:
            result = client.purge_duplicates(dry_run=dry_run)
    except NewsifierAPIError as e:
        click.echo(click.style(f"Error: {e.detail}", fg="red"), err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(click.style(f"Unexpected error: {str(e)}", fg="red"), err=True)
        sys.exit(1)

    # Output results
    if json_output:
        click.echo(json.dumps(result, indent=2))
        return

    # Display in human-readable format
    action_text = "Would remove" if dry_run else "Removed"
    msg = f"{action_text} {result['total_removed']} duplicate articles "
    msg += f"across {result['total_urls']} URLs"
    click.echo(
        click.style(
            msg,
            fg="green" if not dry_run else "yellow",
            bold=True,
        )
    )

    if dry_run:
        click.echo(click.style("(DRY RUN - No changes were made)", fg="yellow"))

    for detail in result["details"]:
        click.echo(f"\nURL: {detail['url']}")
        click.echo(f"  Kept article ID: {detail['kept_id']}")
        click.echo(f"  Removed article IDs: {', '.join(map(str, detail['removed_ids']))}")

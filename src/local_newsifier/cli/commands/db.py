"""
Database diagnostics commands.

This module provides commands for inspecting and managing database state, including:
- Viewing table statistics
- Checking for duplicate records
- Analyzing data integrity
- Showing detailed entity information
"""

import json
from datetime import datetime
from typing import Annotated, Any, Dict, List, Optional

import click
from fastapi import Depends
from fastapi_injectable import get_injected_obj
from sqlalchemy import func, text
from sqlmodel import Session, select
from tabulate import tabulate

from local_newsifier.di.providers import (get_article_crud, get_entity_crud,
                                          get_feed_processing_log_crud, get_rss_feed_crud,
                                          get_session)


@click.group(name="db")
def db_group():
    """Inspect and manage database state."""
    pass


@db_group.command(name="stats")
@click.option("--json", "json_output", is_flag=True, help="Output as JSON")
def db_stats(json_output: bool):
    """Show database statistics for all major tables."""
    # Get dependencies using injectable providers
    session_gen = get_injected_obj(get_session)
    session = next(session_gen)

    # Import models only when needed
    from local_newsifier.models.article import Article
    from local_newsifier.models.entity import Entity
    from local_newsifier.models.rss_feed import RSSFeed, RSSFeedProcessingLog

    # Collect table statistics
    stats = {}

    # Article stats
    article_count = session.exec(select(func.count()).select_from(Article)).one()
    latest_article = session.exec(
        select(Article).order_by(Article.created_at.desc()).limit(1)
    ).first()
    oldest_article = session.exec(select(Article).order_by(Article.created_at).limit(1)).first()

    # RSS Feed stats
    feed_count = session.exec(select(func.count()).select_from(RSSFeed)).one()
    active_feed_count = session.exec(
        select(func.count()).select_from(RSSFeed).where(RSSFeed.is_active == True)
    ).one()

    # RSSFeedProcessingLog stats
    processing_log_count = session.exec(
        select(func.count()).select_from(RSSFeedProcessingLog)
    ).one()

    # Entity stats
    entity_count = session.exec(select(func.count()).select_from(Entity)).one()

    stats["articles"] = {
        "count": article_count,
        "latest": format_datetime(latest_article.created_at) if latest_article else None,
        "oldest": format_datetime(oldest_article.created_at) if oldest_article else None,
    }

    stats["rss_feeds"] = {
        "count": feed_count,
        "active": active_feed_count,
        "inactive": feed_count - active_feed_count,
    }

    stats["feed_processing_logs"] = {
        "count": processing_log_count,
    }

    stats["entities"] = {
        "count": entity_count,
    }

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
def check_duplicates(limit: int, json_output: bool):
    """Find duplicate articles (same URL) and show details."""
    # Get dependencies using injectable providers
    session_gen = get_injected_obj(get_session)
    session = next(session_gen)

    # Import the Article model directly
    from local_newsifier.models.article import Article

    # Query to find duplicate URLs
    duplicate_urls = session.exec(
        select(Article.url, func.count(Article.id).label("count"))
        .group_by(Article.url)
        .having(func.count(Article.id) > 1)
        .order_by(text("count DESC"))
        .limit(limit)
    ).all()

    if not duplicate_urls:
        click.echo("No duplicate articles found.")
        return

    # Get detailed information about the duplicates
    results = []
    for url, count in duplicate_urls:
        duplicates = session.exec(
            select(Article).where(Article.url == url).order_by(Article.created_at)
        ).all()

        duplicate_info = {"url": url, "count": count, "articles": []}

        for article in duplicates:
            duplicate_info["articles"].append(
                {
                    "id": article.id,
                    "title": (
                        article.title[:50] + "..."
                        if article.title and len(article.title) > 50
                        else article.title
                    ),
                    "created_at": format_datetime(article.created_at),
                    "status": article.status,
                    "content_len": len(article.content) if article.content else 0,
                }
            )

        results.append(duplicate_info)

    # Output results
    if json_output:
        click.echo(json.dumps(results, indent=2))
        return

    # Display in human-readable format
    click.echo(
        click.style(f"Found {len(results)} URLs with duplicate articles:", fg="yellow", bold=True)
    )

    for idx, result in enumerate(results):
        click.echo(click.style(f"\n{idx+1}. URL: {result['url']}", fg="cyan"))
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
def list_articles(
    source: Optional[str],
    status: Optional[str],
    before: Optional[str],
    after: Optional[str],
    limit: int,
    json_output: bool,
):
    """List articles with filtering options."""
    # Get dependencies using injectable providers
    session_gen = get_injected_obj(get_session)
    session = next(session_gen)

    # Import the Article model directly
    from local_newsifier.models.article import Article

    # Build the query with filters
    query = select(Article)

    if source:
        query = query.where(Article.source == source)

    if status:
        query = query.where(Article.status == status)

    if before:
        try:
            before_date = datetime.strptime(before, "%Y-%m-%d")
            query = query.where(Article.created_at < before_date)
        except ValueError:
            click.echo(
                click.style("Error: Invalid date format for --before. Use YYYY-MM-DD", fg="red"),
                err=True,
            )
            return

    if after:
        try:
            after_date = datetime.strptime(after, "%Y-%m-%d")
            query = query.where(Article.created_at > after_date)
        except ValueError:
            click.echo(
                click.style("Error: Invalid date format for --after. Use YYYY-MM-DD", fg="red"),
                err=True,
            )
            return

    # Order by most recent first and apply limit
    query = query.order_by(Article.created_at.desc()).limit(limit)

    # Execute query
    articles = session.exec(query).all()

    if not articles:
        click.echo("No articles found matching the criteria.")
        return

    # Format the results
    results = []
    for article in articles:
        results.append(
            {
                "id": article.id,
                "title": article.title,
                "url": article.url,
                "source": article.source,
                "status": article.status,
                "created_at": format_datetime(article.created_at),
                "content_len": len(article.content) if article.content else 0,
            }
        )

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
def inspect_record(table: str, id: int, json_output: bool):
    """Inspect a specific database record in detail."""
    # Get dependencies using injectable providers
    session_gen = get_injected_obj(get_session)
    session = next(session_gen)
    article_crud = get_injected_obj(get_article_crud)
    rss_feed_crud = get_injected_obj(get_rss_feed_crud)
    entity_crud = get_injected_obj(get_entity_crud)
    feed_processing_log_crud = get_injected_obj(get_feed_processing_log_crud)

    # Import model only when needed for feed_log
    from local_newsifier.models.entity import Entity
    from local_newsifier.models.rss_feed import RSSFeedProcessingLog

    result = None

    if table == "article":
        article = article_crud.get(session, id=id)
        if not article:
            click.echo(click.style(f"Error: Article with ID {id} not found", fg="red"), err=True)
            return

        result = {
            "id": article.id,
            "title": article.title,
            "url": article.url,
            "source": article.source,
            "status": article.status,
            "created_at": format_datetime(article.created_at),
            "updated_at": format_datetime(article.updated_at),
            "published_at": format_datetime(article.published_at) if article.published_at else None,
            "scraped_at": format_datetime(article.scraped_at) if article.scraped_at else None,
            "content_len": len(article.content) if article.content else 0,
            "content_preview": (
                (article.content[:200] + "...")
                if article.content and len(article.content) > 200
                else article.content
            ),
        }

    elif table == "rss_feed":
        feed = rss_feed_crud.get(session, id=id)
        if not feed:
            click.echo(click.style(f"Error: RSS Feed with ID {id} not found", fg="red"), err=True)
            return

        # Get processing logs for this feed
        logs = session.exec(
            select(RSSFeedProcessingLog)
            .where(RSSFeedProcessingLog.feed_id == id)
            .order_by(RSSFeedProcessingLog.started_at.desc())
            .limit(5)
        ).all()

        log_data = []
        for log in logs:
            log_data.append(
                {
                    "id": log.id,
                    "status": log.status,
                    "started_at": format_datetime(log.started_at),
                    "completed_at": format_datetime(log.completed_at) if log.completed_at else None,
                    "articles_found": log.articles_found,
                    "articles_added": log.articles_added,
                    "error_message": log.error_message,
                }
            )

        result = {
            "id": feed.id,
            "name": feed.name,
            "url": feed.url,
            "description": feed.description,
            "is_active": feed.is_active,
            "created_at": format_datetime(feed.created_at),
            "updated_at": format_datetime(feed.updated_at),
            "last_fetched_at": (
                format_datetime(feed.last_fetched_at) if feed.last_fetched_at else None
            ),
            "recent_logs": log_data,
        }

    elif table == "feed_log":
        # Use feed_processing_log_crud instead of direct session access
        log = feed_processing_log_crud.get(session, id=id)
        if not log:
            click.echo(
                click.style(f"Error: Feed Processing Log with ID {id} not found", fg="red"),
                err=True,
            )
            return

        result = {
            "id": log.id,
            "feed_id": log.feed_id,
            "status": log.status,
            "started_at": format_datetime(log.started_at),
            "completed_at": format_datetime(log.completed_at) if log.completed_at else None,
            "articles_found": log.articles_found,
            "articles_added": log.articles_added,
            "error_message": log.error_message,
        }

    elif table == "entity":
        # Use entity_crud instead of direct session access
        entity = entity_crud.get(session, id=id)
        if not entity:
            click.echo(click.style(f"Error: Entity with ID {id} not found", fg="red"), err=True)
            return

        result = {
            "id": entity.id,
            "name": entity.name,
            "entity_type": entity.entity_type,
            "created_at": format_datetime(entity.created_at),
            "updated_at": format_datetime(entity.updated_at),
        }

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
            status_color = "green" if log["status"] == "success" else "red"
            status = click.style(log["status"], fg=status_color)

            log_table.append(
                [
                    log["id"],
                    log["started_at"],
                    log["completed_at"] or "",
                    status,
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
def purge_duplicates(dry_run: bool, json_output: bool):
    """Remove duplicate articles, keeping the oldest version."""
    # Get dependencies using injectable providers
    session_gen = get_injected_obj(get_session)
    session = next(session_gen)
    article_crud = get_injected_obj(get_article_crud)

    # Import the Article model directly
    from local_newsifier.models.article import Article

    # Query to find duplicate URLs
    duplicate_urls = session.exec(
        select(Article.url, func.count(Article.id).label("count"))
        .group_by(Article.url)
        .having(func.count(Article.id) > 1)
    ).all()

    if not duplicate_urls:
        click.echo("No duplicate articles found.")
        return

    # Process each set of duplicates
    results = []
    total_removed = 0

    for url, count in duplicate_urls:
        duplicates = session.exec(
            select(Article).where(Article.url == url).order_by(Article.created_at)
        ).all()

        # Keep the oldest (first) article
        to_keep = duplicates[0]
        to_remove = duplicates[1:]

        result = {
            "url": url,
            "kept_id": to_keep.id,
            "removed_ids": [a.id for a in to_remove],
            "removed_count": len(to_remove),
        }
        results.append(result)
        total_removed += len(to_remove)

        # Remove duplicates if not a dry run
        if not dry_run:
            for article in to_remove:
                # Use article_crud to remove articles
                article_crud.remove(session, id=article.id)

    # Commit changes if not a dry run
    if not dry_run:
        session.commit()
        action_text = "Removed"
    else:
        action_text = "Would remove"

    # Output results
    if json_output:
        output = {
            "total_urls": len(results),
            "total_removed": total_removed,
            "dry_run": dry_run,
            "details": results,
        }
        click.echo(json.dumps(output, indent=2))
        return

    # Display in human-readable format
    click.echo(
        click.style(
            f"{action_text} {total_removed} duplicate articles across {len(results)} URLs",
            fg="green" if not dry_run else "yellow",
            bold=True,
        )
    )

    if dry_run:
        click.echo(click.style("(DRY RUN - No changes were made)", fg="yellow"))

    for result in results:
        click.echo(f"\nURL: {result['url']}")
        click.echo(f"  Kept article ID: {result['kept_id']}")
        click.echo(f"  Removed article IDs: {', '.join(map(str, result['removed_ids']))}")


def format_datetime(dt):
    """Format a datetime object for display."""
    if not dt:
        return None
    return dt.strftime("%Y-%m-%d %H:%M:%S")

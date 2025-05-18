"""
RSS Feeds management commands.

This module provides commands for managing RSS feeds, including:
- Listing feeds
- Adding new feeds
- Showing feed details
- Removing feeds
- Processing feeds
- Fetching all active feeds
- Updating feed properties
"""

import json
import click
from datetime import datetime
from tabulate import tabulate

from local_newsifier.di.providers import (
    get_rss_feed_service,
    get_article_crud,
    get_session,
    get_entity_tracking_flow,
    get_news_pipeline_flow,
)
from local_newsifier.errors.cli import handle_rss_cli


@click.group(name="feeds")
def feeds_group():
    """Manage RSS feeds."""
    pass


@feeds_group.command(name="list")
@click.option("--active-only", is_flag=True, help="Show only active feeds")
@click.option("--json", "json_output", is_flag=True, help="Output as JSON")
@click.option("--limit", type=int, default=100, help="Maximum number of feeds to display")
@click.option("--skip", type=int, default=0, help="Number of feeds to skip")
def list_feeds(active_only, json_output, limit, skip):
    """List all feeds with optional filtering."""
    rss_feed_service = get_rss_feed_service()
    feeds = rss_feed_service.list_feeds(skip=skip, limit=limit, active_only=active_only)
    
    if json_output:
        click.echo(json.dumps(feeds, indent=2))
        return
    
    if not feeds:
        click.echo("No feeds found.")
        return
    
    # Format data for table
    table_data = []
    for feed in feeds:
        last_fetched = feed["last_fetched_at"]
        if last_fetched:
            last_fetched = datetime.fromisoformat(last_fetched).strftime("%Y-%m-%d %H:%M")
        
        table_data.append([
            feed["id"],
            feed["name"],
            feed["url"],
            "✓" if feed["is_active"] else "✗",
            last_fetched or "Never"
        ])
    
    # Display table
    headers = ["ID", "Name", "URL", "Active", "Last Fetched"]
    click.echo(tabulate(table_data, headers=headers, tablefmt="simple"))


@feeds_group.command(name="add")
@click.argument("url", required=True)
@click.option("--name", help="Feed name (defaults to URL if not provided)")
@click.option("--description", help="Feed description")
def add_feed(url, name, description):
    """Add a new feed."""
    feed_name = name or url
    
    try:
        rss_feed_service = get_rss_feed_service()
        feed = rss_feed_service.create_feed(url=url, name=feed_name, description=description)
        click.echo(f"Feed added successfully with ID: {feed['id']}")
    except ValueError as e:
        click.echo(click.style(f"Error: {str(e)}", fg="red"), err=True)


@feeds_group.command(name="show")
@click.argument("id", type=int, required=True)
@click.option("--json", "json_output", is_flag=True, help="Output as JSON")
@click.option("--show-logs", is_flag=True, help="Show processing logs")
def show_feed(id, json_output, show_logs):
    """Show feed details."""
    rss_feed_service = get_rss_feed_service()
    feed = rss_feed_service.get_feed(id)
    if not feed:
        click.echo(click.style(f"Error: Feed with ID {id} not found", fg="red"), err=True)
        return
    
    # Get logs if requested
    logs = []
    if show_logs:
        logs = rss_feed_service.get_feed_processing_logs(id, limit=5)
    
    if json_output:
        result = {
            "feed": feed,
        }
        if show_logs:
            result["logs"] = logs
        click.echo(json.dumps(result, indent=2))
        return
    
    # Display feed details
    click.echo(click.style(f"Feed #{feed['id']}: {feed['name']}", fg="green", bold=True))
    click.echo(f"URL: {feed['url']}")
    if feed['description']:
        click.echo(f"Description: {feed['description']}")
    click.echo(f"Active: {'Yes' if feed['is_active'] else 'No'}")
    
    last_fetched = feed["last_fetched_at"]
    if last_fetched:
        last_fetched = datetime.fromisoformat(last_fetched).strftime("%Y-%m-%d %H:%M:%S")
        click.echo(f"Last Fetched: {last_fetched}")
    else:
        click.echo("Last Fetched: Never")
    
    created_at = datetime.fromisoformat(feed["created_at"]).strftime("%Y-%m-%d %H:%M:%S")
    click.echo(f"Created At: {created_at}")
    
    # Display logs if requested
    if show_logs and logs:
        click.echo("\nRecent Processing Logs:")
        log_data = []
        for log in logs:
            started_at = datetime.fromisoformat(log["started_at"]).strftime("%Y-%m-%d %H:%M:%S")
            completed_at = ""
            if log["completed_at"]:
                completed_at = datetime.fromisoformat(log["completed_at"]).strftime("%Y-%m-%d %H:%M:%S")
            
            status_color = "green" if log["status"] == "success" else "red"
            status = click.style(log["status"], fg=status_color)
            
            log_data.append([
                log["id"],
                started_at,
                completed_at,
                status,
                log["articles_found"],
                log["articles_added"],
                log["error_message"] or ""
            ])
        
        log_headers = ["ID", "Started At", "Completed At", "Status", "Found", "Added", "Error"]
        click.echo(tabulate(log_data, headers=log_headers, tablefmt="simple"))


@feeds_group.command(name="remove")
@click.argument("id", type=int, required=True)
@click.option("--force", is_flag=True, help="Skip confirmation")
def remove_feed(id, force):
    """Remove a feed."""
    rss_feed_service = get_rss_feed_service()
    feed = rss_feed_service.get_feed(id)
    if not feed:
        click.echo(click.style(f"Error: Feed with ID {id} not found", fg="red"), err=True)
        return
    
    if not force:
        if not click.confirm(f"Are you sure you want to remove feed '{feed['name']}' (ID: {id})?"):
            click.echo("Operation canceled.")
            return
    
    result = rss_feed_service.remove_feed(id)
    if result:
        click.echo(f"Feed '{feed['name']}' (ID: {id}) removed successfully.")
    else:
        click.echo(click.style(f"Error removing feed with ID {id}", fg="red"), err=True)


def direct_process_article(article_id):
    """Process an article directly without Celery.
    
    This function provides a synchronous processing path for CLI operations,
    bypassing the need for Celery task infrastructure.
    
    Args:
        article_id: The ID of the article to process
        
    Returns:
        bool: True if processing was successful, False otherwise
    """
    # Get all required dependencies from providers
    article_crud = get_article_crud()
    session = get_session()
    
    # Get flow services from providers
    news_pipeline_flow = get_news_pipeline_flow()
    entity_tracking_flow = get_entity_tracking_flow()
    
    try:
        # Get the article from the database
        article = article_crud.get(session, id=article_id)
        if not article:
            click.echo(f"Article with ID {article_id} not found")
            return False
        
        # Process the article through the news pipeline
        if article.url and news_pipeline_flow:
            news_pipeline_flow.process_url_directly(article.url)
        
        # Process entities in the article
        entities = None
        if entity_tracking_flow:
            entities = entity_tracking_flow.process_article(article.id)
        
        click.echo(f"Processed article {article_id}: {article.title}")
        if entities:
            click.echo(f"  Found {len(entities)} entities")
        
        return True
    except Exception as e:
        click.echo(click.style(f"Error processing article {article_id}: {str(e)}", fg="red"), err=True)
        return False


@feeds_group.command(name="process")
@click.argument("id", type=int, required=True)
@click.option("--no-process", is_flag=True, help="Skip article processing, just fetch articles")
def process_feed(id, no_process):
    """Process a specific feed."""
    rss_feed_service = get_rss_feed_service()
    feed = rss_feed_service.get_feed(id)
    if not feed:
        click.echo(click.style(f"Error: Feed with ID {id} not found", fg="red"), err=True)
        return
    
    click.echo(f"Processing feed '{feed['name']}' (ID: {id})...")
    
    # Use direct processing function if not skipping processing
    task_func = None if no_process else direct_process_article
    
    result = rss_feed_service.process_feed(id, task_queue_func=task_func)
    
    if result["status"] == "success":
        click.echo(click.style("Processing completed successfully!", fg="green"))
        click.echo(f"Articles found: {result['articles_found']}")
        click.echo(f"Articles added: {result['articles_added']}")
    else:
        click.echo(click.style("Processing failed.", fg="red"), err=True)
        click.echo(click.style(f"Error: {result['message']}", fg="red"), err=True)


@feeds_group.command(name="update")
@click.argument("id", type=int, required=True)
@click.option("--name", help="New feed name")
@click.option("--description", help="New feed description")
@click.option("--active/--inactive", help="Set feed active or inactive")
def update_feed(id, name, description, active):
    """Update feed properties."""
    rss_feed_service = get_rss_feed_service()
    feed = rss_feed_service.get_feed(id)
    if not feed:
        click.echo(click.style(f"Error: Feed with ID {id} not found", fg="red"), err=True)
        return
    
    # Check if at least one property to update was provided
    if name is None and description is None and active is None:
        click.echo("No properties specified for update. Use --name, --description, or --active/--inactive.")
        return
    
    # Prepare update parameters
    update_params = {}
    if name is not None:
        update_params["name"] = name
    if description is not None:
        update_params["description"] = description
    if active is not None:
        update_params["is_active"] = active
    
    # Update feed
    updated_feed = rss_feed_service.update_feed(id, **update_params)
    
    if updated_feed:
        click.echo(f"Feed '{updated_feed['name']}' (ID: {id}) updated successfully.")
    else:
        click.echo(click.style(f"Error updating feed with ID {id}", fg="red"), err=True)


@feeds_group.command(name="fetch")
@click.option("--no-process", is_flag=True, help="Skip article processing, just fetch articles")
@click.option("--active-only", is_flag=True, default=True, help="Process only active feeds (default: True)")
@handle_rss_cli
def fetch_feeds(no_process, active_only):
    """Fetch articles from all active feeds.
    
    This command fetches articles from all active RSS feeds.
    It's useful for bulk processing multiple feeds at once.
    """
    rss_feed_service = get_rss_feed_service()
    
    # Show what we're about to do
    click.echo(f"Fetching {'active ' if active_only else 'all '}feeds...")
    
    # Get all the feeds we need to process
    feeds = rss_feed_service.list_feeds(active_only=active_only)
    if not feeds:
        click.echo("No feeds found to process.")
        return
    
    # Set up processing function if needed
    task_func = None if no_process else direct_process_article
    
    # Track success and failure
    successful = 0
    failed = 0
    
    # Process each feed
    with click.progressbar(feeds, label="Processing feeds", 
                          item_show_func=lambda f: f["name"] if f else "") as feed_list:
        for feed in feed_list:
            try:
                result = rss_feed_service.process_feed(feed["id"], task_queue_func=task_func)
                if result["status"] == "success":
                    successful += 1
                else:
                    failed += 1
            except Exception as e:
                click.echo(f"\nError processing feed '{feed['name']}': {str(e)}", err=True)
                failed += 1
    
    # Show summary
    total = len(feeds)
    click.echo(f"\nProcessed {total} feeds: {successful} successful, {failed} failed")
    
    if successful == total:
        click.echo(click.style("All feeds processed successfully!", fg="green"))
    elif successful > 0:
        click.echo(click.style(f"Partially successful: {successful}/{total} feeds processed", fg="yellow"))
    else:
        click.echo(click.style("Failed to process any feeds", fg="red"), err=True)

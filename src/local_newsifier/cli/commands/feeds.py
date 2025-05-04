"""
Improved RSS Feeds management commands using proper dependency injection.

This module provides commands for managing RSS feeds with true dependency injection:
- Listing feeds
- Adding new feeds
- Showing feed details
- Removing feeds
- Processing feeds
- Updating feed properties
"""

import json
import click
from datetime import datetime
from tabulate import tabulate
from typing import Any, Optional, TYPE_CHECKING

# Import injectable provider functions
from local_newsifier.di.providers import (
    get_rss_feed_service,
    get_article_crud,
    get_news_pipeline_flow,
    get_entity_tracking_flow,
    get_session as get_db_session,
)

# Type checking imports - these won't be used at runtime
if TYPE_CHECKING:
    from local_newsifier.services.rss_feed_service import RSSFeedService
    from local_newsifier.crud.article import ArticleCRUD
    from local_newsifier.flows.news_pipeline import NewsPipelineFlow
    from local_newsifier.flows.entity_tracking_flow import EntityTrackingFlow
    from sqlmodel import Session


# Command class with proper DI
class FeedsCommands:
    """Feed management commands with proper dependency injection."""
    
    def __init__(
        self,
        rss_feed_service=None,
        article_crud=None,
        news_pipeline_flow=None,
        entity_tracking_flow=None,
        session=None
    ):
        """Initialize with injected dependencies.
        
        This constructor allows dependencies to be injected directly (useful for testing)
        or retrieved from provider functions (for normal operation).
        
        Args:
            rss_feed_service: RSS feed service or None to use provider
            article_crud: Article CRUD or None to use provider
            news_pipeline_flow: News pipeline flow or None to use provider
            entity_tracking_flow: Entity tracking flow or None to use provider
            session: Database session or None to use provider
        """
        # Initialize dependencies - allow injection or use providers
        self.rss_feed_service = rss_feed_service or get_rss_feed_service()
        self.article_crud = article_crud or get_article_crud()
        self.news_pipeline_flow = news_pipeline_flow or get_news_pipeline_flow()
        self.entity_tracking_flow = entity_tracking_flow or get_entity_tracking_flow()
        
        # Get session if it wasn't injected
        if session is None:
            db_session = get_db_session()
            if db_session is not None:
                self.session = next(db_session)
            else:
                self.session = None
        else:
            self.session = session
    

    def list_feeds(self, active_only, json_output, limit, skip):
        """List all feeds with optional filtering."""
        feeds = self.rss_feed_service.list_feeds(skip=skip, limit=limit, active_only=active_only)
        
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
    
    
    def add_feed(self, url, name, description):
        """Add a new feed."""
        feed_name = name or url
        
        try:
            feed = self.rss_feed_service.create_feed(url=url, name=feed_name, description=description)
            click.echo(f"Feed added successfully with ID: {feed['id']}")
        except ValueError as e:
            click.echo(click.style(f"Error: {str(e)}", fg="red"), err=True)
    
    
    def show_feed(self, id, json_output, show_logs):
        """Show feed details."""
        feed = self.rss_feed_service.get_feed(id)
        if not feed:
            click.echo(click.style(f"Error: Feed with ID {id} not found", fg="red"), err=True)
            return
        
        # Get logs if requested
        logs = []
        if show_logs:
            logs = self.rss_feed_service.get_feed_processing_logs(id, limit=5)
        
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
    
    
    def remove_feed(self, id, force):
        """Remove a feed."""
        feed = self.rss_feed_service.get_feed(id)
        if not feed:
            click.echo(click.style(f"Error: Feed with ID {id} not found", fg="red"), err=True)
            return
        
        if not force:
            if not click.confirm(f"Are you sure you want to remove feed '{feed['name']}' (ID: {id})?"):
                click.echo("Operation canceled.")
                return
        
        result = self.rss_feed_service.remove_feed(id)
        if result:
            click.echo(f"Feed '{feed['name']}' (ID: {id}) removed successfully.")
        else:
            click.echo(click.style(f"Error removing feed with ID {id}", fg="red"), err=True)
    

    def direct_process_article(self, article_id):
        """Process an article directly without Celery."""
        try:
            # Get the article from the database
            article = self.article_crud.get(self.session, id=article_id)
            if not article:
                click.echo(f"Article with ID {article_id} not found")
                return False
            
            # Process the article through the news pipeline
            if article.url and self.news_pipeline_flow:
                self.news_pipeline_flow.process_url_directly(article.url)
            
            # Process entities in the article
            entities = None
            if self.entity_tracking_flow:
                entities = self.entity_tracking_flow.process_article(article.id)
            
            click.echo(f"Processed article {article_id}: {article.title}")
            if entities:
                click.echo(f"  Found {len(entities)} entities")
            
            return True
        except Exception as e:
            click.echo(click.style(f"Error processing article {article_id}: {str(e)}", fg="red"), err=True)
            return False
    
    
    def process_feed(self, id, no_process):
        """Process a specific feed."""
        feed = self.rss_feed_service.get_feed(id)
        if not feed:
            click.echo(click.style(f"Error: Feed with ID {id} not found", fg="red"), err=True)
            return
        
        click.echo(f"Processing feed '{feed['name']}' (ID: {id})...")
        
        # Use direct processing function if not skipping processing
        task_func = None if no_process else self.direct_process_article
        
        result = self.rss_feed_service.process_feed(id, task_queue_func=task_func)
        
        if result["status"] == "success":
            click.echo(click.style("Processing completed successfully!", fg="green"))
            click.echo(f"Articles found: {result['articles_found']}")
            click.echo(f"Articles added: {result['articles_added']}")
        else:
            click.echo(click.style("Processing failed.", fg="red"), err=True)
            click.echo(click.style(f"Error: {result['message']}", fg="red"), err=True)
    
    
    def update_feed(self, id, name, description, active):
        """Update feed properties."""
        feed = self.rss_feed_service.get_feed(id)
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
        updated_feed = self.rss_feed_service.update_feed(id, **update_params)
        
        if updated_feed:
            click.echo(f"Feed '{updated_feed['name']}' (ID: {id}) updated successfully.")
        else:
            click.echo(click.style(f"Error updating feed with ID {id}", fg="red"), err=True)


# Using Click's pass_obj pattern for dependency management
@click.group(name="feeds")
@click.pass_context
def feeds_group(ctx):
    """Manage RSS feeds."""
    # Initialize commands object with dependencies
    ctx.obj = FeedsCommands()


@feeds_group.command(name="list")
@click.option("--active-only", is_flag=True, help="Show only active feeds")
@click.option("--json", "json_output", is_flag=True, help="Output as JSON")
@click.option("--limit", type=int, default=100, help="Maximum number of feeds to display")
@click.option("--skip", type=int, default=0, help="Number of feeds to skip")
@click.pass_obj
def list_feeds(feeds_commands, active_only, json_output, limit, skip):
    """List all feeds with optional filtering."""
    feeds_commands.list_feeds(active_only, json_output, limit, skip)


@feeds_group.command(name="add")
@click.argument("url", required=True)
@click.option("--name", help="Feed name (defaults to URL if not provided)")
@click.option("--description", help="Feed description")
@click.pass_obj
def add_feed(feeds_commands, url, name, description):
    """Add a new feed."""
    feeds_commands.add_feed(url, name, description)


@feeds_group.command(name="show")
@click.argument("id", type=int, required=True)
@click.option("--json", "json_output", is_flag=True, help="Output as JSON")
@click.option("--show-logs", is_flag=True, help="Show processing logs")
@click.pass_obj
def show_feed(feeds_commands, id, json_output, show_logs):
    """Show feed details."""
    feeds_commands.show_feed(id, json_output, show_logs)


@feeds_group.command(name="remove")
@click.argument("id", type=int, required=True)
@click.option("--force", is_flag=True, help="Skip confirmation")
@click.pass_obj
def remove_feed(feeds_commands, id, force):
    """Remove a feed."""
    feeds_commands.remove_feed(id, force)


@feeds_group.command(name="process")
@click.argument("id", type=int, required=True)
@click.option("--no-process", is_flag=True, help="Skip article processing, just fetch articles")
@click.pass_obj
def process_feed(feeds_commands, id, no_process):
    """Process a specific feed."""
    feeds_commands.process_feed(id, no_process)


@feeds_group.command(name="update")
@click.argument("id", type=int, required=True)
@click.option("--name", help="New feed name")
@click.option("--description", help="New feed description")
@click.option("--active/--inactive", help="Set feed active or inactive")
@click.pass_obj
def update_feed(feeds_commands, id, name, description, active):
    """Update feed properties."""
    feeds_commands.update_feed(id, name, description, active)
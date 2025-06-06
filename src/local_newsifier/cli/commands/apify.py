"""
Apify integration commands.

This module provides commands for interacting with the Apify API, including:
- Running actors
- Retrieving dataset items
- Fetching actor details
- Testing the Apify connection
"""

import json
import logging
import os
from typing import Optional

import click
from fastapi_injectable import get_injected_obj
from tabulate import tabulate

from local_newsifier.config.settings import settings
from local_newsifier.crud.apify_source_config import apify_source_config as config_crud
from local_newsifier.di.providers import get_apify_service_cli, get_session
from local_newsifier.services.apify_schedule_manager import ApifyScheduleManager
from local_newsifier.services.apify_service import ApifyService


@click.group(name="apify")
def apify_group():
    """Interact with the Apify API."""
    pass


def _ensure_token():
    """Ensure the Apify token is set in environment or settings.

    Returns:
        bool: True if token is available, False otherwise
    """
    # Check if running in test mode
    if os.environ.get("PYTEST_CURRENT_TEST") is not None:
        # In test mode, provide a default token if not set
        if not settings.APIFY_TOKEN:
            logging.warning("Running CLI in test mode with dummy APIFY_TOKEN")
            settings.APIFY_TOKEN = "test_dummy_token"
        return True

    # Check environment first
    token = os.environ.get("APIFY_TOKEN")
    if token:
        settings.APIFY_TOKEN = token
        return True

    # Check if already set in settings
    if settings.APIFY_TOKEN:
        return True

    click.echo(click.style("Error: APIFY_TOKEN is not set.", fg="red"), err=True)
    click.echo("Please set it using one of these methods:")
    click.echo("  1. Export as environment variable: export APIFY_TOKEN=your_token")
    click.echo("  2. Add to .env file: APIFY_TOKEN=your_token")
    click.echo("  3. Use --token option with this command")
    return False


@apify_group.command(name="test")
@click.option("--token", help="Apify API token (overrides environment/settings)")
def test_connection(token):
    """Test the Apify API connection."""
    if token:
        settings.APIFY_TOKEN = token
    elif not _ensure_token():
        return

    try:
        # Get ApifyService from injectable provider with token parameter
        apify_service = get_injected_obj(lambda: get_apify_service_cli(token))

        # Test if we can access the client
        client = apify_service.client

        # Simple test operation - get user info
        user = client.user().get()

        click.echo(click.style("✓ Connection to Apify API successful!", fg="green"))
        click.echo(f"Connected as: {user.get('username', 'Unknown user')}")

    except ValueError as e:
        click.echo(click.style(f"Error: {str(e)}", fg="red"), err=True)
    except Exception as e:
        click.echo(click.style(f"Error connecting to Apify API: {str(e)}", fg="red"), err=True)


@apify_group.command(name="run-actor")
@click.argument("actor_id", required=True)
@click.option("--input", "-i", help="JSON string or file path for actor input")
@click.option("--wait/--no-wait", default=True, help="Wait for the run to finish")
@click.option("--token", help="Apify API token (overrides environment/settings)")
@click.option("--output", "-o", help="Save output to file")
def run_actor(actor_id, input, wait, token, output):
    """Run an Apify actor.

    ACTOR_ID can be in the format username/actor-name or actor-id.

    For specific actor types, we recommend using the following specialized commands:
    - For web-scraper actor: Use 'nf apify web-scraper' command (handles pageFunction)
    - For website-content-crawler: Use 'nf apify scrape-content' command

    Examples:
        nf apify run-actor apify/web-scraper --input '{"startUrls":[{"url":"https://example.com"}],
            "pageFunction":"async function pageFunction(c) { return {url: c.request.url} }"}'
        nf apify run-actor apify/website-content-crawler --input actor_input.json
    """
    if token:
        settings.APIFY_TOKEN = token
    elif not _ensure_token():
        return

    # Parse input
    run_input = {}
    if input:
        if os.path.isfile(input):
            try:
                with open(input, "r") as f:
                    run_input = json.load(f)
                click.echo(f"Loaded input from file: {input}")
            except Exception as e:
                click.echo(
                    click.style(f"Error loading input file: {str(e)}", fg="red"),
                    err=True,
                )
                return
        else:
            try:
                run_input = json.loads(input)
            except json.JSONDecodeError:
                click.echo(click.style("Error: Input must be valid JSON", fg="red"), err=True)
                return

    try:
        # Get ApifyService from injectable provider with token parameter
        apify_service = get_injected_obj(lambda: get_apify_service_cli(token))

        # Run the actor
        click.echo(f"Running actor {actor_id}...")
        run = apify_service.client.actor(actor_id).call(
            run_input=run_input, wait_secs=0 if not wait else None
        )

        # Process result
        if wait:
            click.echo(click.style("✓ Actor run completed!", fg="green"))

            # Get the dataset ID
            dataset_id = run.get("defaultDatasetId")
            if dataset_id:
                click.echo(f"Default dataset ID: {dataset_id}")
                click.echo(f"To retrieve the data: nf apify get-dataset {dataset_id}")
        else:
            click.echo(click.style("✓ Actor run started!", fg="green"))
            click.echo("Run details:")

        # Display or save output
        if output:
            with open(output, "w") as f:
                json.dump(run, f, indent=2)
            click.echo(f"Output saved to {output}")
        else:
            click.echo(json.dumps(run, indent=2))

    except ValueError as e:
        click.echo(click.style(f"Error: {str(e)}", fg="red"), err=True)
    except Exception as e:
        click.echo(click.style(f"Error running actor: {str(e)}", fg="red"), err=True)


@apify_group.command(name="get-dataset")
@click.argument("dataset_id", required=True)
@click.option("--limit", type=int, default=10, help="Maximum number of items to retrieve")
@click.option("--offset", type=int, default=0, help="Number of items to skip")
@click.option("--token", help="Apify API token (overrides environment/settings)")
@click.option("--output", "-o", help="Save output to file")
@click.option(
    "--format",
    "format_type",
    type=click.Choice(["json", "table"]),
    default="json",
    help="Output format (json or table)",
)
def get_dataset(dataset_id, limit, offset, token, output, format_type):
    """Retrieve items from an Apify dataset.

    DATASET_ID is the ID of the dataset to retrieve.

    Examples:
        nf apify get-dataset bPmJXQ5Ym98KjL9TP --limit 5
        nf apify get-dataset bPmJXQ5Ym98KjL9TP --output dataset_results.json
    """
    if token:
        settings.APIFY_TOKEN = token
    elif not _ensure_token():
        return

    try:
        # Get ApifyService from injectable provider with token parameter
        apify_service = get_injected_obj(lambda: get_apify_service_cli(token))

        # Get dataset items
        click.echo(f"Retrieving items from dataset {dataset_id}...")

        # Get the dataset and items
        dataset = apify_service.client.dataset(dataset_id)
        dataset_items = dataset.list_items(limit=limit, offset=offset).get("items", [])

        result = {"items": dataset_items}

        items = result.get("items", [])
        count = len(items)

        click.echo(click.style(f"✓ Retrieved {count} items!", fg="green"))

        # Process output
        if output:
            with open(output, "w") as f:
                json.dump(result, f, indent=2)
            click.echo(f"Output saved to {output}")
            return

        # Display results
        if format_type == "table" and items:
            # Try to create a tabular view if possible
            if isinstance(items[0], dict):
                # Use the first item's keys as columns
                headers = list(items[0].keys())

                # Limit to a reasonable number of columns
                if len(headers) > 5:
                    headers = headers[:5]
                    click.echo("Note: Only showing first 5 columns due to space constraints")

                # Create table data
                table_data = []
                for item in items:
                    row = []
                    for header in headers:
                        value = item.get(header, "")
                        # Truncate long values
                        if isinstance(value, str) and len(value) > 50:
                            value = value[:47] + "..."
                        elif not isinstance(value, (str, int, float, bool, type(None))):
                            value = str(type(value).__name__)
                        row.append(value)
                    table_data.append(row)

                click.echo(tabulate(table_data, headers=headers, tablefmt="simple"))
            else:
                click.echo("Cannot display as table - items are not dictionaries")
                click.echo(json.dumps(items, indent=2))
        else:
            click.echo(json.dumps(items, indent=2))

    except ValueError as e:
        click.echo(click.style(f"Error: {str(e)}", fg="red"), err=True)
    except Exception as e:
        click.echo(click.style(f"Error retrieving dataset: {str(e)}", fg="red"), err=True)


@apify_group.command(name="get-actor")
@click.argument("actor_id", required=True)
@click.option("--token", help="Apify API token (overrides environment/settings)")
def get_actor(actor_id, token):
    """Get details about an Apify actor.

    ACTOR_ID can be in the format username/actor-name or actor-id.

    Examples:
        nf apify get-actor apify/web-scraper
    """
    if token:
        settings.APIFY_TOKEN = token
    elif not _ensure_token():
        return

    try:
        # Get ApifyService from injectable provider with token parameter
        apify_service = get_injected_obj(lambda: get_apify_service_cli(token))

        # Get actor details
        click.echo(f"Retrieving details for actor {actor_id}...")
        actor = apify_service.client.actor(actor_id).get()

        click.echo(click.style("✓ Actor details retrieved!", fg="green"))
        click.echo(f"Name: {actor.get('name')}")
        click.echo(f"Title: {actor.get('title')}")
        click.echo(f"Description: {actor.get('description', 'N/A')}")
        click.echo(f"Version: {actor.get('version', {}).get('versionNumber', 'N/A')}")

        # Display input schema if available
        input_schema = actor.get("defaultRunInput")
        if input_schema:
            click.echo("\nInput Schema:")
            click.echo(json.dumps(input_schema, indent=2))

    except ValueError as e:
        click.echo(click.style(f"Error: {str(e)}", fg="red"), err=True)
    except Exception as e:
        click.echo(click.style(f"Error retrieving actor details: {str(e)}", fg="red"), err=True)


@apify_group.command(name="scrape-content")
@click.argument("url", required=True)
@click.option("--max-pages", type=int, default=5, help="Maximum number of pages to scrape")
@click.option("--max-depth", type=int, default=1, help="Maximum crawl depth from start URL")
@click.option("--token", help="Apify API token (overrides environment/settings)")
@click.option("--output", "-o", help="Save output to file")
def scrape_content(url, max_pages, max_depth, token, output):
    """Scrape content from a website using Apify website-content-crawler.

    This is a convenience command that uses Apify's website-content-crawler actor
    to scrape content from a website.

    URL is the starting URL to scrape from.

    Examples:
        nf apify scrape-content https://example.com --max-pages 10
        nf apify scrape-content https://news.site.com --max-depth 2 --output results.json
    """
    if token:
        settings.APIFY_TOKEN = token
    elif not _ensure_token():
        return

    try:
        # Get ApifyService from injectable provider with token parameter
        apify_service = get_injected_obj(lambda: get_apify_service_cli(token))

        # Configure the actor input
        run_input = {
            "startUrls": [{"url": url}],
            "maxCrawlPages": max_pages,
            "maxCrawlDepth": max_depth,
            "maxPagesPerCrawl": max_pages,
        }

        # Run the actor
        click.echo(f"Scraping content from {url}...")
        click.echo(f"Using max pages: {max_pages}, max depth: {max_depth}")

        run = apify_service.client.actor("apify/website-content-crawler").call(run_input=run_input)

        # Get the dataset ID
        dataset_id = run.get("defaultDatasetId")
        if not dataset_id:
            click.echo(click.style("Error: No dataset ID found in result", fg="red"), err=True)
            return

        click.echo(f"Scraping complete! Retrieving data from dataset: {dataset_id}")

        # Get the dataset items
        dataset = apify_service.client.dataset(dataset_id)
        items = dataset.list_items().get("items", [])

        click.echo(click.style(f"✓ Retrieved {len(items)} pages of content!", fg="green"))

        # Save or display the results
        if output:
            with open(output, "w") as f:
                json.dump(items, f, indent=2)
            click.echo(f"Output saved to {output}")
        else:
            # Display a summary of the results
            click.echo("\nScraping Results Summary:")
            table_data = []
            for i, item in enumerate(items[:10], 1):  # Show up to 10 items
                url = item.get("url", "N/A")
                title = item.get("title", "N/A")
                # Truncate title if too long
                if len(title) > 50:
                    title = title[:47] + "..."

                table_data.append([i, title, url])

            if items:
                headers = ["#", "Title", "URL"]
                click.echo(tabulate(table_data, headers=headers, tablefmt="simple"))

                if len(items) > 10:
                    remaining_items = len(items) - 10
                    click.echo(f"\n...and {remaining_items} more items.")
            else:
                click.echo("No items were scraped.")

    except ValueError as e:
        click.echo(click.style(f"Error: {str(e)}", fg="red"), err=True)
    except Exception as e:
        click.echo(click.style(f"Error scraping content: {str(e)}", fg="red"), err=True)


@apify_group.command(name="web-scraper")
@click.argument("url", required=True)
@click.option("--selector", default="a", help="CSS selector for links to follow")
@click.option("--max-pages", type=int, default=5, help="Maximum number of pages to scrape")
@click.option("--wait-for", help="CSS selector to wait for before scraping")
@click.option("--page-function", help="Custom page function JavaScript code")
@click.option("--output", "-o", help="Save output to file")
@click.option("--token", help="Apify API token (overrides environment/settings)")
def web_scraper(url, selector, max_pages, wait_for, page_function, output, token):
    """Scrape websites using Apify's web-scraper actor.

    This command uses Apify's web-scraper actor to scrape websites,
    handling all required configuration including the pageFunction.

    URL is the starting URL to scrape from.

    Examples:
        nf apify web-scraper https://example.com
        nf apify web-scraper https://news.site.com --selector "article a" --output results.json
    """
    if token:
        settings.APIFY_TOKEN = token
    elif not _ensure_token():
        return

    try:
        # Get ApifyService from injectable provider with token parameter
        apify_service = get_injected_obj(lambda: get_apify_service_cli(token))

        # Default page function if not provided
        default_page_function = """
        async function pageFunction(context) {
            const { request, log, jQuery } = context;
            const $ = jQuery;
            const title = $('title').text();
            const h1 = $('h1').text();

            log.info("Page " + request.url + " loaded.");

            // Extract all text from main content (if available), or body as fallback
            const mainText = $('main, article, #content, .content').text() ||
                $('body').text();

            // Return data
            return {
                url: request.url,
                title: title,
                h1: h1,
                content: mainText
            };
        }
        """

        # Configure the actor input
        run_input = {
            "startUrls": [{"url": url}],
            "linkSelector": selector,
            "pageFunction": page_function or default_page_function,
            "maxPagesPerCrawl": max_pages,
        }

        # Add waitFor if provided
        if wait_for:
            run_input["waitFor"] = wait_for

        # Run the actor
        click.echo(f"Scraping website from {url}...")
        click.echo(f"Using selector: {selector}, max pages: {max_pages}")

        run = apify_service.client.actor("apify/web-scraper").call(run_input=run_input)

        # Get the dataset ID
        dataset_id = run.get("defaultDatasetId")
        if not dataset_id:
            click.echo(click.style("Error: No dataset ID found in result", fg="red"), err=True)
            return

        click.echo(f"Scraping complete! Retrieving data from dataset: {dataset_id}")

        # Get the dataset items
        dataset = apify_service.client.dataset(dataset_id)
        items = dataset.list_items().get("items", [])

        click.echo(click.style(f"✓ Retrieved {len(items)} pages of data!", fg="green"))

        # Save or display the results
        if output:
            with open(output, "w") as f:
                json.dump(items, f, indent=2)
            click.echo(f"Output saved to {output}")
        else:
            # Display a summary of the results
            click.echo("\nScraping Results Summary:")
            table_data = []
            for i, item in enumerate(items[:10], 1):  # Show up to 10 items
                url = item.get("url", "N/A")
                title = item.get("title", "N/A")
                # Truncate title if too long
                if len(title) > 50:
                    title = title[:47] + "..."

                table_data.append([i, title, url])

            if items:
                headers = ["#", "Title", "URL"]
                click.echo(tabulate(table_data, headers=headers, tablefmt="simple"))

                if len(items) > 10:
                    remaining_items = len(items) - 10
                    click.echo(f"\n...and {remaining_items} more items.")
            else:
                click.echo("No items were scraped.")

    except ValueError as e:
        click.echo(click.style(f"Error: {str(e)}", fg="red"), err=True)
    except Exception as e:
        click.echo(click.style(f"Error scraping website: {str(e)}", fg="red"), err=True)


# Create a group for schedule commands
@apify_group.group(name="schedules")
def schedules_group():
    """Manage Apify schedules."""
    pass


def _get_schedule_manager(token: Optional[str] = None) -> ApifyScheduleManager:
    """Get a configured ApifyScheduleManager instance.

    Args:
        token: Optional Apify API token

    Returns:
        ApifyScheduleManager: Configured schedule manager
    """
    apify_service = ApifyService(token)
    session = get_session()
    return ApifyScheduleManager(
        apify_service=apify_service,
        apify_source_config_crud=config_crud,
        session_factory=lambda: session,
    )


@schedules_group.command(name="list")
@click.option("--token", help="Apify API token (overrides environment/settings)")
@click.option("--with-apify", is_flag=True, help="Include Apify schedule details")
@click.option(
    "--format",
    "format_type",
    type=click.Choice(["table", "json"]),
    default="table",
    help="Output format (table or json)",
)
def list_schedules(token: str, with_apify: bool, format_type: str):
    """List all schedules and their status."""
    if token:
        settings.APIFY_TOKEN = token
    elif not _ensure_token():
        return

    try:
        # Get all scheduled configs from database
        configs = []
        session = get_session()
        db_configs = config_crud.get_scheduled_configs(session, enabled_only=False)
        # Convert to dictionaries to avoid session binding issues
        for config in db_configs:
            configs.append(
                {
                    "id": config.id,
                    "name": config.name,
                    "actor_id": config.actor_id,
                    "schedule": config.schedule,
                    "schedule_id": config.schedule_id,
                    "is_active": config.is_active,
                    "last_run_at": config.last_run_at,
                }
            )

        if not configs:
            click.echo("No scheduled configurations found.")
            return

        # If json format is requested, just dump the data
        if format_type == "json":
            output = []
            for config in configs:
                item = config.copy()
                # Convert datetime to string if present
                if item["last_run_at"]:
                    item["last_run_at"] = item["last_run_at"].isoformat()
                output.append(item)
            click.echo(json.dumps(output, indent=2))
            return

        # If we also need Apify details, get them
        if with_apify:
            schedule_manager = _get_schedule_manager(token)
            table_data = []

            for config in configs:
                status = schedule_manager.verify_schedule_status(config["id"])

                # Format for table display
                exists = "✓" if status["exists"] else "✗"
                synced = "✓" if status["synced"] else "✗"
                schedule_id = config["schedule_id"] or "N/A"
                last_run = (
                    config["last_run_at"].strftime("%Y-%m-%d %H:%M")
                    if config["last_run_at"]
                    else "Never"
                )

                row = [
                    config["id"],
                    config["name"],
                    config["schedule"],
                    "Active" if config["is_active"] else "Inactive",
                    schedule_id,
                    exists,
                    synced,
                    last_run,
                ]
                table_data.append(row)

            headers = [
                "ID",
                "Name",
                "Schedule",
                "Status",
                "Schedule ID",
                "Exists",
                "Synced",
                "Last Run",
            ]
            click.echo(tabulate(table_data, headers=headers, tablefmt="simple"))
        else:
            # Simple table without Apify API calls
            table_data = []
            for config in configs:
                schedule_id = config["schedule_id"] or "N/A"
                last_run = (
                    config["last_run_at"].strftime("%Y-%m-%d %H:%M")
                    if config["last_run_at"]
                    else "Never"
                )

                row = [
                    config["id"],
                    config["name"],
                    config["schedule"],
                    "Active" if config["is_active"] else "Inactive",
                    schedule_id,
                    last_run,
                ]
                table_data.append(row)

            headers = ["ID", "Name", "Schedule", "Status", "Schedule ID", "Last Run"]
            click.echo(tabulate(table_data, headers=headers, tablefmt="simple"))

    except Exception as e:
        click.echo(click.style(f"Error listing schedules: {str(e)}", fg="red"), err=True)


@schedules_group.command(name="sync")
@click.option("--token", help="Apify API token (overrides environment/settings)")
def sync_schedules(token: str):
    """Synchronize database configs with Apify schedules."""
    if token:
        settings.APIFY_TOKEN = token
    elif not _ensure_token():
        return

    try:
        # Create schedule manager
        schedule_manager = _get_schedule_manager(token)

        # Run sync operation
        click.echo("Synchronizing schedules with Apify...")
        results = schedule_manager.sync_schedules()

        # Display results
        click.echo(click.style("✓ Schedules synchronized successfully!", fg="green"))
        click.echo(f"Created: {results['created']}")
        click.echo(f"Updated: {results['updated']}")
        click.echo(f"Deleted: {results['deleted']}")
        click.echo(f"Unchanged: {results['unchanged']}")

        # Display any errors
        if results["errors"]:
            click.echo("\nErrors encountered:")
            for error in results["errors"]:
                click.echo(click.style(f"  - {error}", fg="yellow"))

    except Exception as e:
        click.echo(click.style(f"Error synchronizing schedules: {str(e)}", fg="red"), err=True)


@schedules_group.command(name="create")
@click.argument("config_id", type=int)
@click.option("--token", help="Apify API token (overrides environment/settings)")
def create_schedule(config_id: int, token: str):
    """Create a schedule for a specific config."""
    if token:
        settings.APIFY_TOKEN = token
    elif not _ensure_token():
        return

    try:
        # Create schedule manager
        schedule_manager = _get_schedule_manager(token)

        # Create schedule
        click.echo(f"Creating schedule for config {config_id}...")
        created = schedule_manager.create_schedule_for_config(config_id)

        if created:
            click.echo(click.style("✓ Schedule created successfully!", fg="green"))
        else:
            click.echo("Schedule already exists, no changes made.")

    except Exception as e:
        click.echo(click.style(f"Error creating schedule: {str(e)}", fg="red"), err=True)


@schedules_group.command(name="update")
@click.argument("config_id", type=int)
@click.option("--token", help="Apify API token (overrides environment/settings)")
def update_schedule(config_id: int, token: str):
    """Update a schedule for a specific config."""
    if token:
        settings.APIFY_TOKEN = token
    elif not _ensure_token():
        return

    try:
        # Create schedule manager
        schedule_manager = _get_schedule_manager(token)

        # Update schedule
        click.echo(f"Updating schedule for config {config_id}...")
        updated = schedule_manager.update_schedule_for_config(config_id)

        if updated:
            click.echo(click.style("✓ Schedule updated successfully!", fg="green"))
        else:
            click.echo("Schedule is already up to date, no changes made.")

    except Exception as e:
        click.echo(click.style(f"Error updating schedule: {str(e)}", fg="red"), err=True)


@schedules_group.command(name="delete")
@click.argument("config_id", type=int)
@click.option("--token", help="Apify API token (overrides environment/settings)")
def delete_schedule(config_id: int, token: str):
    """Delete a schedule for a specific config."""
    if token:
        settings.APIFY_TOKEN = token
    elif not _ensure_token():
        return

    try:
        # Create schedule manager
        schedule_manager = _get_schedule_manager(token)

        # Delete schedule
        click.echo(f"Deleting schedule for config {config_id}...")
        deleted = schedule_manager.delete_schedule_for_config(config_id)

        if deleted:
            click.echo(click.style("✓ Schedule deleted successfully!", fg="green"))
        else:
            click.echo("No schedule found to delete.")

    except Exception as e:
        click.echo(click.style(f"Error deleting schedule: {str(e)}", fg="red"), err=True)


@schedules_group.command(name="status")
@click.argument("config_id", type=int)
@click.option("--token", help="Apify API token (overrides environment/settings)")
def schedule_status(config_id: int, token: str):
    """Check the status of a schedule for a specific config."""
    if token:
        settings.APIFY_TOKEN = token
    elif not _ensure_token():
        return

    try:
        # Create schedule manager
        schedule_manager = _get_schedule_manager(token)

        # Get schedule status
        click.echo(f"Checking schedule status for config {config_id}...")
        status = schedule_manager.verify_schedule_status(config_id)

        # Display status
        click.echo("\nSchedule Status:")
        click.echo(f"Config ID: {config_id}")
        click.echo(f"Name: {status['config_details']['name']}")
        click.echo(f"Schedule: {status['config_details']['schedule']}")
        click.echo(f"Active: {status['config_details']['is_active']}")

        if status["exists"]:
            click.echo(click.style("✓ Schedule exists in Apify", fg="green"))
            click.echo(f"Schedule ID: {status['config_details']['schedule_id']}")

            if status["synced"]:
                click.echo(click.style("✓ Schedule is in sync with config", fg="green"))
            else:
                click.echo(click.style("✗ Schedule is out of sync with config", fg="yellow"))
                click.echo("Run 'nf apify schedules update CONFIG_ID' to synchronize.")
        else:
            click.echo(click.style("✗ Schedule does not exist in Apify", fg="red"))
            if status["config_details"]["schedule_id"]:
                click.echo("Schedule ID exists in config but not in Apify.")
                click.echo("Run 'nf apify schedules create CONFIG_ID' to create the schedule.")
            else:
                click.echo("No schedule ID in config.")

    except Exception as e:
        click.echo(click.style(f"Error checking schedule status: {str(e)}", fg="red"), err=True)


@apify_group.command(name="process-dataset")
@click.argument("dataset_id", required=True)
@click.option("--dry-run", is_flag=True, help="Show what would be created without saving")
@click.option(
    "--min-content-length", type=int, default=500, help="Minimum content length (default: 500)"
)
@click.option("--source-name", default="apify", help="Override source name (default: 'apify')")
@click.option("--force", is_flag=True, help="Process even if articles exist")
@click.option("--token", help="Apify API token (overrides environment/settings)")
def process_dataset(dataset_id, dry_run, min_content_length, source_name, force, token):
    """Process an Apify dataset and create articles from it.

    This command processes any dataset ID into articles, with options to:
    - Preview what would be created (dry-run)
    - Set minimum content length
    - Override source name
    - Force processing even if articles exist

    DATASET_ID is the ID of the dataset to process.

    Examples:
        nf apify process-dataset bPmJXQ5Ym98KjL9TP --dry-run
        nf apify process-dataset bPmJXQ5Ym98KjL9TP --min-content-length 1000
        nf apify process-dataset bPmJXQ5Ym98KjL9TP --source-name "news-crawler" --force
    """
    if token:
        settings.APIFY_TOKEN = token
    elif not _ensure_token():
        return

    try:
        # Get ApifyService and session
        apify_service = get_injected_obj(lambda: get_apify_service_cli(token))
        session = get_session()

        # Fetch dataset items
        click.echo(f"Fetching dataset {dataset_id}...")
        dataset_items = apify_service.client.dataset(dataset_id).list_items().items
        click.echo(f"Dataset contains {len(dataset_items)} items")

        articles_to_create = []
        skipped_reasons = {"no_url": 0, "no_title": 0, "short_content": 0, "duplicate": 0}

        # Import article CRUD
        from datetime import UTC, datetime

        from local_newsifier.crud.article import article as article_crud
        from local_newsifier.models.article import Article

        # Process each item
        for idx, item in enumerate(dataset_items):
            # Log available fields for first few items
            if idx < 3:
                click.echo(f"\nItem {idx} fields: {list(item.keys())}")

            # Extract URL - required field
            url = item.get("url", "")
            if not url:
                skipped_reasons["no_url"] += 1
                continue

            # Extract title - required field
            title = item.get("title", "")
            if not title:
                skipped_reasons["no_title"] += 1
                continue

            # Extract content with improved field mapping
            content = (
                item.get("text", "")  # Primary field from most actors
                or item.get("markdown", "")  # Alternative format
                or item.get("content", "")  # Legacy/custom actors
                or item.get("body", "")  # Fallback
            )

            # Check metadata for additional content
            metadata = item.get("metadata", {})
            if not content and metadata:
                content = metadata.get("description", "")

            # Which field was used?
            content_source = None
            if item.get("text"):
                content_source = "text"
            elif item.get("markdown"):
                content_source = "markdown"
            elif item.get("content"):
                content_source = "content"
            elif item.get("body"):
                content_source = "body"
            elif metadata and metadata.get("description"):
                content_source = "metadata.description"

            # Skip if content too short
            if len(content) < min_content_length:
                if idx < 3:
                    msg = f"Item {idx} content too short: {len(content)} chars"
                    if content_source:
                        msg += f" (from {content_source})"
                    click.echo(msg)
                skipped_reasons["short_content"] += 1
                continue

            # Check if article already exists (unless force flag is set)
            if not force and article_crud.get_by_url(session, url=url):
                skipped_reasons["duplicate"] += 1
                continue

            # Extract metadata fields if available
            published_at = datetime.now(UTC).replace(tzinfo=None)

            # Try to parse published date from metadata
            if metadata and metadata.get("publishedAt"):
                try:
                    # Handle various date formats
                    pub_str = metadata["publishedAt"]
                    if isinstance(pub_str, str):
                        published_at = datetime.fromisoformat(
                            pub_str.replace("Z", "+00:00")
                        ).replace(tzinfo=None)
                except Exception:
                    pass  # Use default if parsing fails

            # Create article object
            article = {
                "url": url,
                "title": title,
                "content": content,
                "source": item.get("source", source_name),
                "published_at": published_at,
                "scraped_at": datetime.now(UTC).replace(tzinfo=None),
                "content_length": len(content),
                "content_source": content_source,
            }

            articles_to_create.append(article)

            if idx < 3:
                msg = f"Item {idx} would create article: {title[:50]}..."
                msg += f" ({len(content)} chars"
                if content_source:
                    msg += f" from {content_source}"
                msg += ")"
                click.echo(msg)

        # Display summary
        click.echo(click.style("\n=== Processing Summary ===", fg="cyan", bold=True))
        click.echo(f"Total items: {len(dataset_items)}")
        click.echo(f"Articles to create: {len(articles_to_create)}")
        click.echo(f"Skipped: {sum(skipped_reasons.values())}")
        click.echo(f"  - No URL: {skipped_reasons['no_url']}")
        click.echo(f"  - No title: {skipped_reasons['no_title']}")
        click.echo(f"  - Content too short: {skipped_reasons['short_content']}")
        click.echo(f"  - Duplicate: {skipped_reasons['duplicate']}")

        if dry_run:
            click.echo(
                click.style("\n=== DRY RUN MODE - No articles created ===", fg="yellow", bold=True)
            )

            # Show first few articles that would be created
            if articles_to_create:
                click.echo("\nSample articles that would be created:")
                table_data = []
                for i, article in enumerate(articles_to_create[:5]):
                    table_data.append(
                        [
                            i + 1,
                            (
                                article["title"][:40] + "..."
                                if article["title"] and len(article["title"]) > 40
                                else article["title"] or "(No title)"
                            ),
                            article["content_length"],
                            article["content_source"],
                            (
                                article["url"][:50] + "..."
                                if len(article["url"]) > 50
                                else article["url"]
                            ),
                        ]
                    )

                headers = ["#", "Title", "Content Len", "Source Field", "URL"]
                click.echo(tabulate(table_data, headers=headers, tablefmt="simple"))

                if len(articles_to_create) > 5:
                    click.echo(f"\n...and {len(articles_to_create) - 5} more articles")
        else:
            # Create articles
            if articles_to_create:
                click.echo(f"\nCreating {len(articles_to_create)} articles...")

                created_count = 0
                for article_data in articles_to_create:
                    try:
                        # Remove our tracking fields before creating
                        article_data.pop("content_length", None)
                        article_data.pop("content_source", None)

                        # Create article
                        new_article = Article(
                            url=article_data["url"],
                            title=article_data["title"],
                            content=article_data["content"],
                            source=article_data["source"],
                            published_at=article_data["published_at"],
                            status="published",
                            scraped_at=article_data["scraped_at"],
                        )
                        session.add(new_article)
                        created_count += 1

                    except Exception as e:
                        click.echo(f"Error creating article: {str(e)}", err=True)

                # Commit all articles
                if created_count > 0:
                    session.commit()
                    click.echo(
                        click.style(f"✓ Successfully created {created_count} articles!", fg="green")
                    )
                else:
                    click.echo("No articles were created.")
            else:
                click.echo("\nNo articles to create based on the dataset and filters.")

    except Exception as e:
        click.echo(click.style(f"Error processing dataset: {str(e)}", fg="red"), err=True)


@apify_group.command(name="debug-dataset")
@click.argument("dataset_id", required=True)
@click.option("--token", help="Apify API token (overrides environment/settings)")
@click.option(
    "--format",
    "format_type",
    type=click.Choice(["json", "table"]),
    default="table",
    help="Output format (json or table)",
)
def debug_dataset(dataset_id, token, format_type):
    """Debug why articles aren't being created from an Apify dataset.

    This command analyzes a dataset and reports:
    - Total items in the dataset
    - Which fields are present/missing
    - Content length for each item
    - Whether articles would be created
    - Existing articles that prevent creation

    DATASET_ID is the ID of the dataset to analyze.

    Examples:
        nf apify debug-dataset bPmJXQ5Ym98KjL9TP
        nf apify debug-dataset bPmJXQ5Ym98KjL9TP --format json
    """
    if token:
        settings.APIFY_TOKEN = token
    elif not _ensure_token():
        return

    try:
        # Make HTTP request to the debug endpoint
        import requests

        from local_newsifier.config.settings import get_settings

        config = get_settings()
        base_url = getattr(config, "API_BASE_URL", None) or "http://localhost:8000"
        url = f"{base_url}/webhooks/apify/debug/{dataset_id}"

        response = requests.get(url)

        if response.status_code == 404:
            click.echo(
                click.style(f"Error: Dataset {dataset_id} not found or inaccessible", fg="red"),
                err=True,
            )
            return
        elif response.status_code != 200:
            click.echo(
                click.style(f"Error: {response.json().get('detail', 'Unknown error')}", fg="red"),
                err=True,
            )
            return

        analysis = response.json()

        # Display results based on format
        if format_type == "json":
            click.echo(json.dumps(analysis, indent=2))
            return

        # Table format - summary first
        click.echo(click.style("\n=== Dataset Analysis Summary ===", fg="cyan", bold=True))
        click.echo(f"Dataset ID: {analysis['dataset_id']}")
        click.echo(f"Total Items: {analysis['total_items']}")

        summary = analysis["summary"]
        click.echo("\nItem Analysis:")
        click.echo(f"  Valid items: {summary['valid_items']}")
        click.echo(f"  Missing URL: {summary['missing_url']}")
        click.echo(f"  Missing title: {summary['missing_title']}")
        click.echo(f"  Missing content: {summary['missing_content']}")
        click.echo(f"  Content too short: {summary['content_too_short']}")
        click.echo(f"  Duplicate articles: {summary['duplicate_articles']}")
        click.echo(f"  Creatable articles: {summary['creatable_articles']}")

        # Show recommendations if any
        if analysis.get("recommendations"):
            click.echo(click.style("\n=== Recommendations ===", fg="yellow", bold=True))
            for rec in analysis["recommendations"]:
                click.echo(f"  • {rec}")

        # Show detailed item analysis if not too many items
        if analysis["total_items"] > 0 and analysis["total_items"] <= 20:
            click.echo(click.style("\n=== Detailed Item Analysis ===", fg="cyan", bold=True))
            table_data = []

            for item in analysis["items_analysis"]:
                issues_str = ", ".join(item["issues"]) if item["issues"] else "None"
                if len(issues_str) > 40:
                    issues_str = issues_str[:37] + "..."

                table_data.append(
                    [
                        item["index"],
                        "✓" if item["has_url"] else "✗",
                        "✓" if item["has_title"] else "✗",
                        item["content_length"],
                        "✓" if item["would_create_article"] else "✗",
                        issues_str,
                    ]
                )

            headers = ["#", "URL", "Title", "Content Len", "Would Create", "Issues"]
            click.echo(tabulate(table_data, headers=headers, tablefmt="simple"))

        elif analysis["total_items"] > 20:
            click.echo(
                f"\n(Detailed analysis available for {analysis['total_items']} items - "
                "use --format json to see all)"
            )

    except requests.exceptions.ConnectionError:
        click.echo(
            click.style(
                "Error: Cannot connect to API. Make sure the API server is running.", fg="red"
            ),
            err=True,
        )
        click.echo("Start the API with: make run-api")
    except Exception as e:
        click.echo(click.style(f"Error debugging dataset: {str(e)}", fg="red"), err=True)

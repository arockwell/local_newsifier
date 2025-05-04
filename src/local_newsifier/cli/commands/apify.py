"""
Apify integration commands with proper dependency injection.

This module provides commands for interacting with the Apify API, including:
- Running actors
- Retrieving dataset items
- Fetching actor details
- Testing the Apify connection

Uses a class-based approach with proper dependency injection.
"""

import json
import os
from typing import Optional, Dict, Any, List

import click
from tabulate import tabulate

# Import injectable provider function
from local_newsifier.di.providers import get_apify_service
# Import settings for token management
from local_newsifier.config.settings import settings


class ApifyCommands:
    """Apify API commands with proper dependency injection."""
    
    def __init__(self, apify_service=None):
        """Initialize with injected dependencies.
        
        This constructor allows dependencies to be injected directly (useful for testing)
        or retrieved from provider functions (for normal operation).
        
        Args:
            apify_service: Apify service or None to use provider
        """
        # Initialize apify_service - allow injection or use provider
        self.apify_service = apify_service or get_apify_service()
    
    def _ensure_token(self, token: Optional[str] = None) -> bool:
        """Ensure the Apify token is set in environment or settings.
    
        Args:
            token: Token parameter that overrides environment/settings
            
        Returns:
            bool: True if token is available, False otherwise
        """
        # Use provided token if available
        if token:
            settings.APIFY_TOKEN = token
            return True
            
        # Check environment next
        env_token = os.environ.get("APIFY_TOKEN")
        if env_token:
            settings.APIFY_TOKEN = env_token
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


    def test_connection(self, token: Optional[str] = None):
        """Test the Apify API connection.
        
        Args:
            token: Optional token to use for this operation
        """
        if not self._ensure_token(token):
            return

        try:
            # Test if we can access the client
            client = self.apify_service.client

            # Simple test operation - get user info
            user = client.user().get()

            click.echo(click.style("✓ Connection to Apify API successful!", fg="green"))
            click.echo(f"Connected as: {user.get('username', 'Unknown user')}")

        except ValueError as e:
            click.echo(click.style(f"Error: {str(e)}", fg="red"), err=True)
        except Exception as e:
            click.echo(
                click.style(f"Error connecting to Apify API: {str(e)}", fg="red"), err=True
            )


    def run_actor(self, actor_id: str, input_data: Optional[str] = None, 
                wait: bool = True, token: Optional[str] = None, 
                output: Optional[str] = None):
        """Run an Apify actor.
    
        Args:
            actor_id: ID of the actor to run
            input_data: JSON string or file path for actor input
            wait: Whether to wait for the run to finish
            token: Optional token to use for this operation
            output: Optional file path to save output to
        """
        if not self._ensure_token(token):
            return
    
        # Parse input
        run_input = {}
        if input_data:
            if os.path.isfile(input_data):
                try:
                    with open(input_data, "r") as f:
                        run_input = json.load(f)
                    click.echo(f"Loaded input from file: {input_data}")
                except Exception as e:
                    click.echo(
                        click.style(f"Error loading input file: {str(e)}", fg="red"),
                        err=True,
                    )
                    return
            else:
                try:
                    run_input = json.loads(input_data)
                except json.JSONDecodeError:
                    click.echo(
                        click.style("Error: Input must be valid JSON", fg="red"), err=True
                    )
                    return
    
        try:
            # Run the actor
            click.echo(f"Running actor {actor_id}...")
            result = self.apify_service.run_actor(actor_id, run_input)
    
            # Process result
            if wait:
                click.echo(click.style("✓ Actor run completed!", fg="green"))
    
                # Get the dataset ID
                dataset_id = result.get("defaultDatasetId")
                if dataset_id:
                    click.echo(f"Default dataset ID: {dataset_id}")
                    click.echo(f"To retrieve the data: nf apify get-dataset {dataset_id}")
            else:
                click.echo(click.style("✓ Actor run started!", fg="green"))
                click.echo("Run details:")
    
            # Display or save output
            if output:
                with open(output, "w") as f:
                    json.dump(result, f, indent=2)
                click.echo(f"Output saved to {output}")
            else:
                click.echo(json.dumps(result, indent=2))
    
        except ValueError as e:
            click.echo(click.style(f"Error: {str(e)}", fg="red"), err=True)
        except Exception as e:
            click.echo(click.style(f"Error running actor: {str(e)}", fg="red"), err=True)


    def get_dataset(self, dataset_id: str, limit: int = 10, offset: int = 0, 
                  token: Optional[str] = None, output: Optional[str] = None, 
                  format_type: str = "json"):
        """Retrieve items from an Apify dataset.
    
        Args:
            dataset_id: ID of the dataset to retrieve
            limit: Maximum number of items to retrieve
            offset: Number of items to skip
            token: Optional token to use for this operation
            output: Optional file path to save output to
            format_type: Output format (json or table)
        """
        if not self._ensure_token(token):
            return
    
        try:
            # Get dataset items
            click.echo(f"Retrieving items from dataset {dataset_id}...")
            result = self.apify_service.get_dataset_items(dataset_id, limit=limit, offset=offset)
    
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
                        click.echo(
                            "Note: Only showing first 5 columns due to space constraints"
                        )
    
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
            click.echo(
                click.style(f"Error retrieving dataset: {str(e)}", fg="red"), err=True
            )


    def get_actor(self, actor_id: str, token: Optional[str] = None):
        """Get details about an Apify actor.
    
        Args:
            actor_id: ID of the actor to retrieve
            token: Optional token to use for this operation
        """
        if not self._ensure_token(token):
            return
    
        try:
            # Get actor details
            click.echo(f"Retrieving details for actor {actor_id}...")
            actor = self.apify_service.get_actor_details(actor_id)
    
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
            click.echo(
                click.style(f"Error retrieving actor details: {str(e)}", fg="red"), err=True
            )


    def scrape_content(self, url: str, max_pages: int = 5, max_depth: int = 1, 
                       token: Optional[str] = None, output: Optional[str] = None):
        """Scrape content from a website using Apify website-content-crawler.
    
        Args:
            url: Starting URL to scrape from
            max_pages: Maximum number of pages to scrape
            max_depth: Maximum crawl depth from start URL
            token: Optional token to use for this operation
            output: Optional file path to save output to
        """
        if not self._ensure_token(token):
            return
    
        try:
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
    
            result = self.apify_service.run_actor("apify/website-content-crawler", run_input)
    
            # Get the dataset ID
            dataset_id = result.get("defaultDatasetId")
            if not dataset_id:
                click.echo(
                    click.style("Error: No dataset ID found in result", fg="red"), err=True
                )
                return
    
            click.echo(f"Scraping complete! Retrieving data from dataset: {dataset_id}")
    
            # Get the dataset items
            dataset = self.apify_service.get_dataset_items(dataset_id)
            items = dataset.get("items", [])
    
            click.echo(
                click.style(f"✓ Retrieved {len(items)} pages of content!", fg="green")
            )
    
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


    def web_scraper(self, url: str, selector: str = "a", max_pages: int = 5,
                   wait_for: Optional[str] = None, page_function: Optional[str] = None,
                   output: Optional[str] = None, token: Optional[str] = None):
        """Scrape websites using Apify's web-scraper actor.
    
        Args:
            url: Starting URL to scrape from
            selector: CSS selector for links to follow
            max_pages: Maximum number of pages to scrape
            wait_for: CSS selector to wait for before scraping
            page_function: Custom page function JavaScript code
            output: Optional file path to save output to
            token: Optional token to use for this operation
        """
        if not self._ensure_token(token):
            return
    
        try:
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
    
            result = self.apify_service.run_actor("apify/web-scraper", run_input)
    
            # Get the dataset ID
            dataset_id = result.get("defaultDatasetId")
            if not dataset_id:
                click.echo(
                    click.style("Error: No dataset ID found in result", fg="red"), err=True
                )
                return
    
            click.echo(f"Scraping complete! Retrieving data from dataset: {dataset_id}")
    
            # Get the dataset items
            dataset = self.apify_service.get_dataset_items(dataset_id)
            items = dataset.get("items", [])
    
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


# Using Click's pass_obj pattern for dependency management
@click.group(name="apify")
@click.pass_context
def apify_group(ctx):
    """Interact with the Apify API."""
    # Initialize commands object with dependencies
    ctx.obj = ApifyCommands()


@apify_group.command(name="test")
@click.option("--token", help="Apify API token (overrides environment/settings)")
@click.pass_obj
def test_connection(apify_commands, token):
    """Test the Apify API connection."""
    apify_commands.test_connection(token)


@apify_group.command(name="run-actor")
@click.argument("actor_id", required=True)
@click.option("--input", "-i", help="JSON string or file path for actor input")
@click.option("--wait/--no-wait", default=True, help="Wait for the run to finish")
@click.option("--token", help="Apify API token (overrides environment/settings)")
@click.option("--output", "-o", help="Save output to file")
@click.pass_obj
def run_actor(apify_commands, actor_id, input, wait, token, output):
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
    apify_commands.run_actor(actor_id, input, wait, token, output)


@apify_group.command(name="get-dataset")
@click.argument("dataset_id", required=True)
@click.option(
    "--limit", type=int, default=10, help="Maximum number of items to retrieve"
)
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
@click.pass_obj
def get_dataset(apify_commands, dataset_id, limit, offset, token, output, format_type):
    """Retrieve items from an Apify dataset.

    DATASET_ID is the ID of the dataset to retrieve.

    Examples:
        nf apify get-dataset bPmJXQ5Ym98KjL9TP --limit 5
        nf apify get-dataset bPmJXQ5Ym98KjL9TP --output dataset_results.json
    """
    apify_commands.get_dataset(dataset_id, limit, offset, token, output, format_type)


@apify_group.command(name="get-actor")
@click.argument("actor_id", required=True)
@click.option("--token", help="Apify API token (overrides environment/settings)")
@click.pass_obj
def get_actor(apify_commands, actor_id, token):
    """Get details about an Apify actor.

    ACTOR_ID can be in the format username/actor-name or actor-id.

    Examples:
        nf apify get-actor apify/web-scraper
    """
    apify_commands.get_actor(actor_id, token)


@apify_group.command(name="scrape-content")
@click.argument("url", required=True)
@click.option(
    "--max-pages", type=int, default=5, help="Maximum number of pages to scrape"
)
@click.option(
    "--max-depth", type=int, default=1, help="Maximum crawl depth from start URL"
)
@click.option("--token", help="Apify API token (overrides environment/settings)")
@click.option("--output", "-o", help="Save output to file")
@click.pass_obj
def scrape_content(apify_commands, url, max_pages, max_depth, token, output):
    """Scrape content from a website using Apify website-content-crawler.

    This is a convenience command that uses Apify's website-content-crawler actor
    to scrape content from a website.

    URL is the starting URL to scrape from.

    Examples:
        nf apify scrape-content https://example.com --max-pages 10
        nf apify scrape-content https://news.site.com --max-depth 2 --output results.json
    """
    apify_commands.scrape_content(url, max_pages, max_depth, token, output)


@apify_group.command(name="web-scraper")
@click.argument("url", required=True)
@click.option("--selector", default="a", help="CSS selector for links to follow")
@click.option(
    "--max-pages", type=int, default=5, help="Maximum number of pages to scrape"
)
@click.option("--wait-for", help="CSS selector to wait for before scraping")
@click.option("--page-function", help="Custom page function JavaScript code")
@click.option("--output", "-o", help="Save output to file")
@click.option("--token", help="Apify API token (overrides environment/settings)")
@click.pass_obj
def web_scraper(apify_commands, url, selector, max_pages, wait_for, page_function, output, token):
    """Scrape websites using Apify's web-scraper actor.

    This command uses Apify's web-scraper actor to scrape websites,
    handling all required configuration including the pageFunction.

    URL is the starting URL to scrape from.

    Examples:
        nf apify web-scraper https://example.com
        nf apify web-scraper https://news.site.com --selector "article a" --output results.json
    """
    apify_commands.web_scraper(url, selector, max_pages, wait_for, page_function, output, token)

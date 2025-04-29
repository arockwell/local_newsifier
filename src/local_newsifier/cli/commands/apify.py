"""
Apify integration commands.

This module provides commands for interacting with the Apify API, including:
- Running actors
- Retrieving dataset items
- Fetching actor details
- Testing the Apify connection
"""

import os
import json
import click
from datetime import datetime
from tabulate import tabulate

# Import directly instead of using container to avoid loading flow dependencies
from local_newsifier.config.settings import settings
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
        # Create the Apify service directly
        apify_service = ApifyService(token)
        
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
    
    Examples:
        nf apify run-actor apify/web-scraper --input '{"startUrls":[{"url":"https://example.com"}]}'
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
                with open(input, 'r') as f:
                    run_input = json.load(f)
                click.echo(f"Loaded input from file: {input}")
            except Exception as e:
                click.echo(click.style(f"Error loading input file: {str(e)}", fg="red"), err=True)
                return
        else:
            try:
                run_input = json.loads(input)
            except json.JSONDecodeError:
                click.echo(click.style("Error: Input must be valid JSON", fg="red"), err=True)
                return
    
    try:
        # Create Apify service directly
        apify_service = ApifyService(token)
        
        # Run the actor
        click.echo(f"Running actor {actor_id}...")
        result = apify_service.run_actor(actor_id, run_input)
        
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
            with open(output, 'w') as f:
                json.dump(result, f, indent=2)
            click.echo(f"Output saved to {output}")
        else:
            click.echo(json.dumps(result, indent=2))
        
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
@click.option("--format", "format_type", type=click.Choice(['json', 'table']), default='json',
              help="Output format (json or table)")
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
        # Create Apify service directly
        apify_service = ApifyService(token)
        
        # Get dataset items
        click.echo(f"Retrieving items from dataset {dataset_id}...")
        result = apify_service.get_dataset_items(dataset_id, limit=limit, offset=offset)
        
        items = result.get("items", [])
        count = len(items)
        
        click.echo(click.style(f"✓ Retrieved {count} items!", fg="green"))
        
        # Process output
        if output:
            with open(output, 'w') as f:
                json.dump(result, f, indent=2)
            click.echo(f"Output saved to {output}")
            return
        
        # Display results
        if format_type == 'table' and items:
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
        # Create Apify service directly
        apify_service = ApifyService(token)
        
        # Get actor details
        click.echo(f"Retrieving details for actor {actor_id}...")
        actor = apify_service.get_actor_details(actor_id)
        
        click.echo(click.style(f"✓ Actor details retrieved!", fg="green"))
        click.echo(f"Name: {actor.get('name')}")
        click.echo(f"Title: {actor.get('title')}")
        click.echo(f"Description: {actor.get('description', 'N/A')}")
        click.echo(f"Version: {actor.get('version', {}).get('versionNumber', 'N/A')}")
        
        # Display input schema if available
        input_schema = actor.get('defaultRunInput')
        if input_schema:
            click.echo("\nInput Schema:")
            click.echo(json.dumps(input_schema, indent=2))
        
    except ValueError as e:
        click.echo(click.style(f"Error: {str(e)}", fg="red"), err=True)
    except Exception as e:
        click.echo(click.style(f"Error retrieving actor details: {str(e)}", fg="red"), err=True)


@apify_group.command(name="scrape-content")
@click.argument("url", required=True)
@click.option("--max-pages", type=int, default=5, 
              help="Maximum number of pages to scrape")
@click.option("--max-depth", type=int, default=1,
              help="Maximum crawl depth from start URL")
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
        # Create Apify service directly
        apify_service = ApifyService(token)
        
        # Configure the actor input
        run_input = {
            "startUrls": [{"url": url}],
            "maxCrawlPages": max_pages,
            "maxCrawlDepth": max_depth,
            "maxPagesPerCrawl": max_pages
        }
        
        # Run the actor
        click.echo(f"Scraping content from {url}...")
        click.echo(f"Using max pages: {max_pages}, max depth: {max_depth}")
        
        result = apify_service.run_actor("apify/website-content-crawler", run_input)
        
        # Get the dataset ID
        dataset_id = result.get("defaultDatasetId")
        if not dataset_id:
            click.echo(click.style("Error: No dataset ID found in result", fg="red"), err=True)
            return
            
        click.echo(f"Scraping complete! Retrieving data from dataset: {dataset_id}")
        
        # Get the dataset items
        dataset = apify_service.get_dataset_items(dataset_id)
        items = dataset.get("items", [])
        
        click.echo(click.style(f"✓ Retrieved {len(items)} pages of content!", fg="green"))
        
        # Save or display the results
        if output:
            with open(output, 'w') as f:
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
                    click.echo(f"\n...and {len(items) - 10} more items.")
            else:
                click.echo("No items were scraped.")
        
    except ValueError as e:
        click.echo(click.style(f"Error: {str(e)}", fg="red"), err=True)
    except Exception as e:
        click.echo(click.style(f"Error scraping content: {str(e)}", fg="red"), err=True)

# Local Newsifier CLI Guide

## Overview
The CLI (Command Line Interface) module provides command-line tools for interacting with the Local Newsifier system. It allows users to perform various tasks without using the web interface.

## CLI Architecture

### Main CLI Application
- **main.py**: Entry point for the CLI application
- Sets up Click command groups and shared options
- Provides the `nf` command

### Command Groups
- **apify.py**: Commands for Apify web scraping integration
- **feeds.py**: Commands for managing and processing RSS feeds
- **db.py**: Commands for database operations and maintenance

## Common CLI Patterns

### Command Group Structure
Commands are organized into logical groups:

```python
@click.group(name="feeds")
def feeds_group():
    """Manage RSS feeds and fetch articles."""
    pass

@feeds_group.command(name="list")
def list_feeds():
    """List all configured RSS feeds."""
    # Command implementation...

@feeds_group.command(name="fetch")
@click.option("--feed-id", type=int, help="ID of the feed to fetch")
def fetch_feed(feed_id):
    """Fetch articles from RSS feeds."""
    # Command implementation...
```

### Command-Line Arguments and Options
- Use positional arguments for required inputs
- Use options with flags for optional parameters
- Add help text to all commands and options

```python
@apify_group.command(name="scrape-content")
@click.argument("url", required=True)
@click.option("--max-pages", type=int, default=5, 
              help="Maximum number of pages to scrape")
@click.option("--max-depth", type=int, default=1,
              help="Maximum crawl depth from start URL")
@click.option("--token", help="Apify API token (overrides environment/settings)")
@click.option("--output", "-o", help="Save output to file")
def scrape_content(url, max_pages, max_depth, token, output):
    """Scrape content from a website using Apify."""
    # Command implementation...
```

### Container-Based Services
CLI commands use the DI container to get services:

```python
def list_feeds():
    """List all configured RSS feeds."""
    try:
        # Get the container
        from local_newsifier.container import container
        
        # Get the RSS feed service
        feed_service = container.get("rss_feed_service")
        
        # Get feeds and display them
        feeds = feed_service.list_feeds()
        # ...
    except Exception as e:
        click.echo(click.style(f"Error: {str(e)}", fg="red"), err=True)
```

### Error Handling
CLI commands handle errors gracefully:

```python
def process_feed(feed_id):
    """Process a feed and its articles."""
    try:
        # Command implementation...
    except ValueError as e:
        click.echo(click.style(f"Error: {str(e)}", fg="red"), err=True)
    except Exception as e:
        click.echo(click.style(f"Unexpected error: {str(e)}", fg="red"), err=True)
        # Optionally show stack trace in verbose mode
        if verbose:
            import traceback
            click.echo(traceback.format_exc())
```

### Styled Output
Use Click styling for better readability:

```python
# Success messages in green
click.echo(click.style("✓ Feed added successfully!", fg="green"))

# Error messages in red
click.echo(click.style("Error: Invalid URL", fg="red"), err=True)

# Warnings in yellow
click.echo(click.style("Warning: No articles found", fg="yellow"))

# Important information in blue
click.echo(click.style("Processing feed: Example Feed", fg="blue"))
```

### Tabular Output
For structured data, use tabulate for formatted output:

```python
from tabulate import tabulate

def list_feeds():
    """List all configured RSS feeds."""
    # ...
    
    # Format feeds as a table
    table_data = []
    for feed in feeds:
        table_data.append([
            feed.id,
            feed.name,
            feed.url,
            feed.is_active,
            feed.last_fetched_at or "Never"
        ])
    
    headers = ["ID", "Name", "URL", "Active", "Last Fetched"]
    click.echo(tabulate(table_data, headers=headers, tablefmt="simple"))
```

### Progress Bars
For long-running operations, show progress:

```python
def process_feeds():
    """Process all feeds."""
    # ...
    
    with click.progressbar(feeds, label="Processing feeds") as bar:
        for feed in bar:
            process_feed(feed.id)
```

## Command Implementations

### Direct Processing vs Task Queueing
CLI commands can process directly or queue tasks:

```python
def process_feed(feed_id, use_queue=True):
    """Process a feed.
    
    Args:
        feed_id: ID of the feed to process
        use_queue: Whether to use the task queue or process directly
    """
    if use_queue:
        # Queue task for asynchronous processing
        from local_newsifier.tasks import fetch_feed
        task = fetch_feed.delay(feed_id)
        click.echo(f"Queued task {task.id} for feed {feed_id}")
    else:
        # Process directly
        feed_service.process_feed(feed_id, task_queue_func=direct_process_article)
        click.echo(f"Processed feed {feed_id} directly")
```

### File Input/Output
Handle file input and output:

```python
def export_data(data, output_file):
    """Export data to a file.
    
    Args:
        data: The data to export
        output_file: Path to the output file
    """
    if output_file:
        file_extension = output_file.split(".")[-1].lower()
        
        if file_extension == "json":
            with open(output_file, "w") as f:
                json.dump(data, f, indent=2)
        elif file_extension == "csv":
            # Convert to CSV
            # ...
        else:
            # Default to JSON
            with open(output_file, "w") as f:
                json.dump(data, f, indent=2)
                
        click.echo(f"Data exported to {output_file}")
    else:
        # Print to console
        click.echo(json.dumps(data, indent=2))
```

## Command Reference

### RSS Feed Commands

```bash
# List all configured feeds
nf feeds list

# Add a new feed
nf feeds add --name "Example Feed" --url https://example.com/rss.xml

# Fetch articles from a feed
nf feeds fetch --feed-id 1

# Process articles from a feed
nf feeds process --feed-id 1
```

### Apify Commands

```bash
# Test Apify API connection
nf apify test

# Run an Apify actor
nf apify run-actor apify/web-scraper --input input.json

# Get items from an Apify dataset
nf apify get-dataset DATASET_ID

# Scrape content from a URL
nf apify scrape-content https://example.com
```

### Database Commands

```bash
# List database tables
nf db list-tables

# Show table schema
nf db show-schema --table articles

# Count records in a table
nf db count --table articles
```

## Best Practices

### Command Design
- Group related commands together
- Use descriptive names for commands and options
- Provide help text for all commands and options
- Follow command naming conventions (verb-noun)

### Error Handling
- Handle expected errors gracefully
- Provide clear error messages
- Set appropriate exit codes
- Optionally show stack traces in verbose mode

### User Experience
- Provide feedback for long-running operations
- Use colored output for different message types
- Format structured data as tables
- Support both human-readable and machine-readable output

### Service Integration
- Use the DI container to get services
- Avoid direct database access in command handlers
- Delegate business logic to services
- Handle both direct processing and task queuing

### Testing
- Test command-line argument parsing
- Mock service dependencies
- Test error handling
- Verify output formatting
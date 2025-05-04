# Apify Error Handling Example

This document provides examples of how to use the error handling framework with the Apify service.

## Service Implementation

```python
# src/local_newsifier/services/apify_service.py

from apify_client import ApifyClient
from ..errors import handle_apify

class ApifyService:
    def __init__(self, token=None):
        self._token = token
        self._client = None
        
    @property
    def client(self):
        if self._client is None:
            if not self._token:
                raise ValueError("Apify token is required")
            self._client = ApifyClient(self._token)
        return self._client
    
    @handle_apify
    def run_actor(self, actor_id, run_input):
        """Run an Apify actor with error handling, retry and timing.
        
        Args:
            actor_id: The ID of the Apify actor to run.
            run_input: The input for the actor.
            
        Returns:
            The actor run result.
            
        Raises:
            ServiceError: For various Apify-related errors.
        """
        return self.client.actor(actor_id).call(run_input=run_input)
    
    @handle_apify
    def get_dataset_items(self, dataset_id):
        """Get items from an Apify dataset with error handling.
        
        Args:
            dataset_id: The ID of the Apify dataset.
            
        Returns:
            The dataset items.
            
        Raises:
            ServiceError: For various Apify-related errors.
        """
        return self.client.dataset(dataset_id).list_items().items
    
    @handle_apify
    def scrape_article(self, url):
        """Scrape an article using the Apify article extractor actor.
        
        Args:
            url: The URL of the article to scrape.
            
        Returns:
            The extracted article data.
            
        Raises:
            ServiceError: For various Apify-related errors.
        """
        actor_id = "apify/website-content-crawler"
        run_input = {"startUrls": [{"url": url}]}
        
        run = self.client.actor(actor_id).call(run_input=run_input)
        dataset_id = run["defaultDatasetId"]
        
        items = self.client.dataset(dataset_id).list_items().items
        if not items:
            raise ValueError(f"No content extracted from {url}")
            
        return items[0]
```

## CLI Integration

```python
# src/local_newsifier/cli/commands/apify.py

import click
from ...errors import handle_apify_cli
from ...services.apify_service import ApifyService

@click.group("apify")
def apify_group():
    """Commands for working with Apify."""
    pass

@apify_group.command("test")
@handle_apify_cli
@click.pass_context
def test_apify(ctx):
    """Test the Apify API connection."""
    apify_service = ctx.obj['container'].get("apify_service")
    actors = apify_service.client.actors().list()
    click.echo(f"Successfully connected to Apify API. Found {len(actors.items)} actors.")

@apify_group.command("scrape-content")
@click.argument("url")
@handle_apify_cli
@click.pass_context
def scrape_content(ctx, url):
    """Scrape content from a URL using Apify."""
    apify_service = ctx.obj['container'].get("apify_service")
    result = apify_service.scrape_article(url)
    click.echo(f"Successfully scraped content from {url}")
    click.echo(f"Title: {result.get('title', 'Unknown')}")
    click.echo(f"Content length: {len(result.get('text', ''))} characters")
```

## Error Handling in Action

### Network Error

```
$ nf apify test
Network error: Failed to connect to Apify API: Connection refused
Troubleshooting: Check your internet connection and try again.
```

### Authentication Error

```
$ nf apify test
Authentication failed: Apify API authentication failed: 401 Client Error: Unauthorized for url: https://api.apify.com/v2/actors
Troubleshooting: Check your Apify API token in the configuration.
```

### Rate Limit Error

```
$ nf apify scrape-content https://example.com
Rate limit exceeded: Apify API rate limit exceeded: 429 Client Error: Too Many Requests for url: https://api.apify.com/v2/acts/run
Troubleshooting: The free Apify plan has usage limits. Wait before trying again.
```

### Detailed Error Information (Verbose Mode)

```
$ nf apify test --verbose
Authentication failed: Apify API authentication failed: 401 Client Error: Unauthorized for url: https://api.apify.com/v2/actors

Debug Information:
  Service: apify
  Error Type: authentication
  Timestamp: 2023-05-04T15:23:45.678901
  Context:
    function: test_apify
    url: https://api.apify.com/v2/actors
    status_code: 401
  Original Error: HTTPError: 401 Client Error: Unauthorized for url: https://api.apify.com/v2/actors
```

## Benefits of the Error Handling Framework

1. **User-Friendly Messages**: Error messages include troubleshooting hints.
2. **Automatic Retry**: Transient errors are automatically retried.
3. **Context Preservation**: Detailed error context for debugging.
4. **Consistent Exit Codes**: Each error type has a specific exit code.
5. **Performance Monitoring**: Service calls are automatically timed.

## Next Steps

The same error handling pattern can be applied to other external integrations:

1. RSS feed service
2. Web scraper tool
3. News pipeline service

Using the same approach ensures consistent error handling across all external integrations.
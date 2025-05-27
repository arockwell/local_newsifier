# Apify Error Handling Example

This document provides examples of using the streamlined error handling framework with the Apify service.

## Service Implementation

```python
from apify_client import ApifyClient
from local_newsifier.errors import handle_apify

class ApifyService:
    """Service for interacting with the Apify API."""

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

        All errors will be transformed into ServiceError with
        contextual information and automatic retry for transient errors.
        """
        return self.client.actor(actor_id).call(run_input=run_input)

    @handle_apify
    def get_dataset_items(self, dataset_id):
        """Get items from an Apify dataset with error handling."""
        return self.client.dataset(dataset_id).list_items().items
```

## CLI Integration

```python
import click
from local_newsifier.errors import handle_apify_cli

@click.group(name="apify")
def apify_group():
    """Interact with the Apify API."""
    pass

@apify_group.command(name="test")
@handle_apify_cli
def test_connection():
    """Test the Apify API connection."""
    apify_service = ApifyService()
    actors = apify_service.client.actors().list()
    click.echo(f"Successfully connected to Apify API. Found {len(actors.items)} actors.")

@apify_group.command(name="scrape-content")
@click.argument("url")
@handle_apify_cli
def scrape_content(url):
    """Scrape content from a URL using Apify."""
    apify_service = ApifyService()
    result = apify_service.scrape_article(url)
    click.echo(f"Successfully scraped content from {url}")
    click.echo(f"Title: {result.get('title', 'Unknown')}")
```

## Error Examples

### Network Error

```
apify.network: Failed to connect to Apify API: Connection refused
Hint: Network connectivity issue. Check your internet connection.
```

### Authentication Error

```
apify.auth: Authentication failed: 401 Client Error: Unauthorized
Hint: Apify API key is invalid or expired. Check your APIFY_TOKEN in settings.
```

### Rate Limit Error

```
apify.rate_limit: Rate limit exceeded: 429 Client Error: Too Many Requests
Hint: Apify rate limit exceeded. Try again later or upgrade your plan.
```

## Benefits Over Traditional Approach

### Traditional Approach (15+ lines per method)

```python
def run_actor(self, actor_id, run_input):
    try:
        return self.client.actor(actor_id).call(run_input=run_input)
    except requests.ConnectionError as e:
        logger.error(f"Network error in run_actor: {e}")
        raise ApifyNetworkError(f"Failed to connect to Apify API: {e}")
    except requests.Timeout as e:
        logger.error(f"Timeout in run_actor: {e}")
        raise ApifyTimeoutError(f"Request to Apify API timed out: {e}")
    except requests.HTTPError as e:
        status_code = e.response.status_code if hasattr(e, 'response') else None
        if status_code == 401:
            raise ApifyAuthError(f"Authentication failed: {e}")
        elif status_code == 429:
            raise ApifyRateLimitError(f"Rate limit exceeded: {e}")
        # More error handling...
```

### Streamlined Approach (2 lines per method)

```python
@handle_apify
def run_actor(self, actor_id, run_input):
    return self.client.actor(actor_id).call(run_input=run_input)
```

## Implementation Details

1. **Error Classification**: Exceptions automatically categorized by type and status code
2. **Context Collection**: Function name, arguments, status codes captured automatically
3. **Automatic Retry**: Transient errors retried with exponential backoff
4. **Timing**: Performance metrics logged for all service calls
5. **User-Friendly Messages**: Errors presented with troubleshooting hints

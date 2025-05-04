# Streamlined Error Handling

This guide explains the streamlined error handling framework used in the Local Newsifier application.

## Core Concepts

The error handling system is built on three key principles:

1. **Unified Error Type**: A single `ServiceError` class instead of a complex hierarchy
2. **Descriptive Errors**: Context-rich errors with service, type, and troubleshooting info
3. **Consistent Patterns**: Same error handling approach across all services

## ServiceError Class

All service errors are represented by the `ServiceError` class:

```python
# Example error creation
error = ServiceError(
    service="apify",          # Service identifier
    error_type="network",     # Error type
    message="Connection failed",
    original=original_error,  # Original exception
    context={"url": "https://api.example.com"}
)
```

### Error Types

Common error types used across all services:

| Type        | Description             | Transient | Exit Code |
|-------------|-------------------------|-----------|-----------|
| `network`   | Network connectivity    | Yes       | 2         |
| `timeout`   | Request timed out       | Yes       | 3         |
| `rate_limit`| Rate limit exceeded     | Yes       | 4         |
| `auth`      | Authentication failed   | No        | 5         |
| `parse`     | Failed to parse response| No        | 6         |
| `validation`| Input validation failed | No        | 7         |
| `not_found` | Resource not found      | No        | 8         |
| `server`    | Server-side error       | Yes       | 9         |
| `unknown`   | Unknown error           | No        | 1         |

## Using Error Handling

### Service Methods

```python
from local_newsifier.errors import handle_apify

class ApifyService:
    
    @handle_apify
    def run_actor(self, actor_id, run_input):
        """Run an Apify actor with full error handling.
        
        Errors will be automatically transformed, retried, and timed.
        """
        return self.client.actor(actor_id).call(run_input=run_input)
```

### CLI Commands

```python
from local_newsifier.errors import handle_apify_cli
import click

@click.command()
@handle_apify_cli
def test_command():
    """CLI command with error handling."""
    # Run code that might raise exceptions
    # Errors will be presented in user-friendly format
```

## Error Handling Components

### Error Classification

The system automatically classifies errors from various sources:

```python
# HTTP errors classified by status code
response = requests.get("https://api.example.com")
response.raise_for_status()  # 401 → auth, 404 → not_found, etc.

# Exception types
try:
    json.loads(invalid_json)  # ValueError → parse
except Exception as e:
    # Automatically classified
```

### Automatic Retry

Transient errors are automatically retried with backoff:

```python
# This method will retry network errors automatically
@handle_apify
def fetch_data(url):
    return requests.get(url).json()
```

### Context Preservation

All errors include rich context for debugging:

```python
try:
    service.run_actor("some-actor", {"url": "example.com"})
except ServiceError as e:
    print(e.context)  # Contains function name, args, status code, etc.
```

## API Reference

### Decorators

- `@handle_apify` - For Apify service methods
- `@handle_rss` - For RSS feed methods
- `@handle_web_scraper` - For web scraper methods
- `@handle_apify_cli` - For Apify CLI commands
- `@handle_rss_cli` - For RSS CLI commands

### Manual Usage

For custom error handling:

```python
from local_newsifier.errors import ServiceError

# Create an error
raise ServiceError("custom", "validation", "Custom error message")

# Handle errors
try:
    # Code that might raise ServiceError
except ServiceError as e:
    if e.error_type == "network":
        # Retry logic
    elif e.error_type == "auth":
        # Authentication handling
```

## CLI Error Presentation

When errors occur in CLI commands, they're presented in a user-friendly format:

```
apify.auth: Authentication failed: 401 Unauthorized
Hint: Apify API key is invalid or expired. Check your APIFY_TOKEN in settings.
```

In verbose mode (`--verbose`), additional debug information is shown:

```
Debug Information:
  service: apify
  error_type: auth
  timestamp: 2023-06-01T12:34:56.789012
  Context:
    function: test_connection
    status_code: 401
    url: https://api.apify.com/v2/actors
```
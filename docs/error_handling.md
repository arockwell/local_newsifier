# Error Handling Framework

This document describes the unified error handling framework for external service integrations in the Local Newsifier application.

## Overview

The error handling framework provides a standardized approach to handling errors from external services like Apify, RSS feeds, and web scrapers. It includes:

1. **Common Error Structure**: A single `ServiceError` class with contextual information
2. **Error Categorization**: Standardized error types across services
3. **Automatic Retry**: Configurable retry logic for transient errors
4. **Performance Monitoring**: Timing information for service calls
5. **User-Friendly CLI Errors**: Consistent error presentation with troubleshooting hints

## Core Components

### ServiceError Class

The `ServiceError` class is the foundation of the error handling framework. It provides a standardized way to represent errors from external services:

```python
class ServiceError(Exception):
    def __init__(
        self,
        service: str,          # Service identifier (e.g., "apify", "rss")
        error_type: str,       # Error type (e.g., "network", "timeout")
        message: str,          # Human-readable error message
        original: Exception = None,  # Original exception
        context: Dict = None,  # Additional context information
        is_transient: bool = False   # Whether error is likely temporary
    )
```

### Error Types

Common error types used across services:

| Error Type       | Description                     | Transient | Retry |
|------------------|---------------------------------|-----------|-------|
| `network`        | Network connectivity issue      | Yes       | Yes   |
| `timeout`        | Request timed out               | Yes       | Yes   |
| `rate_limit`     | Rate limit exceeded             | Yes       | Yes   |
| `authentication` | Authentication failed           | No        | No    |
| `parse`          | Failed to parse response        | No        | No    |
| `validation`     | Input validation failed         | No        | No    |
| `not_found`      | Resource not found              | No        | No    |
| `server`         | Server-side error               | Yes       | Yes   |
| `configuration`  | Configuration error             | No        | No    |
| `unknown`        | Unknown error                   | No        | No    |

## Usage Examples

### Basic Error Handling

```python
from local_newsifier.errors import handle_apify_errors

@handle_apify_errors
def fetch_data(url):
    response = requests.get(url)
    response.raise_for_status()
    return response.json()
```

The `handle_apify_errors` decorator will catch exceptions and transform them into appropriate `ServiceError` instances with context information.

### Combined Error Handling

```python
from local_newsifier.errors import handle_apify

@handle_apify  # Combines error handling, retry, and timing
def fetch_dataset(dataset_id):
    # Code that might fail in various ways
    return client.dataset(dataset_id).items()
```

The `handle_apify` decorator combines error handling, retry logic, and performance monitoring.

### CLI Error Handling

```python
import click
from local_newsifier.errors import handle_apify_cli

@click.command()
@click.argument("url")
@handle_apify_cli
@click.pass_context
def scrape_content(ctx, url):
    """Scrape content from a URL using Apify."""
    result = apify_service.scrape_article(url)
    click.echo(f"Successfully scraped: {result.title}")
```

The `handle_apify_cli` decorator provides user-friendly error messages with troubleshooting hints.

## Key Benefits

1. **Simplicity**: Single error class instead of complex hierarchy
2. **Context Preservation**: Detailed error context for easier debugging
3. **Automatic Retry**: Built-in retry logic for transient errors
4. **Improved UX**: User-friendly error messages in CLI
5. **Performance Insights**: Automatic timing of service calls
6. **Consistency**: Same error handling pattern across all services

## Implementation Details

- **Error Mapping**: Service-specific exception mappings in `mapping.py`
- **Decorator Factories**: Service-specific decorator creation in `decorators.py`
- **CLI Integration**: Click-compatible error handling in `cli.py`

## Adding a New Service Integration

To add error handling for a new service:

1. Add error mappings in `mapping.py`:

```python
NEW_SERVICE_ERROR_MAPPINGS = [
    (ExceptionType, pattern, "error_type", "Message template: {error}")
]

ERROR_MAPPINGS["new_service"] = NEW_SERVICE_ERROR_MAPPINGS
```

2. Create service-specific decorators in `__init__.py`:

```python
handle_new_service_errors = create_error_handler("new_service")
retry_new_service_calls = create_retry_handler("new_service")
handle_new_service = create_service_handler("new_service")
handle_new_service_cli = handle_service_error_cli("new_service")
```

3. Add any service-specific error messages in `cli.py`:

```python
SERVICE_ERROR_MESSAGES["new_service"] = {
    "error_type": "Custom message template: {message}",
}
```

4. Use the decorators in your service implementation:

```python
@handle_new_service
def service_method():
    # Implementation
```
# RSS Error Handling

This document explains the error handling approach for RSS feed operations in the Local Newsifier system.

## Overview

The system uses a streamlined approach to error handling for all external service integrations, including RSS feeds. This approach:

1. Uses a single `ServiceError` class for all error types
2. Provides decorators for consistent error handling
3. Adds specific context to error messages
4. Categorizes errors for appropriate handling
5. Provides automatic retry for transient errors

## Error Structure

All errors are instances of `ServiceError` with the following attributes:

- `service`: Identifies the service that raised the error (e.g., "rss")
- `error_type`: Specific error classification (e.g., "network", "timeout", "xml_parse")
- `message`: Human-readable error message
- `original`: The original exception that was caught (for tracking the root cause)
- `context`: Additional context information about the error
- `transient`: Boolean indicating if the error is likely temporary
- `exit_code`: Integer code for CLI applications

## RSS-Specific Error Types

RSS feed operations can produce these specific error types:

| Error Type | Description | Transient | Retry |
|------------|-------------|-----------|-------|
| xml_parse | XML parsing errors | No | No |
| feed_format | Feed structure errors | No | No |
| feed_validation | Missing required elements | No | No |
| url | Malformed URLs | No | No |
| encoding | Text encoding issues | No | No |

In addition to the common error types:

| Error Type | Description | Transient | Retry |
|------------|-------------|-----------|-------|
| network | Network connectivity issues | Yes | Yes |
| timeout | Request timeout errors | Yes | Yes |
| rate_limit | Rate limiting errors | Yes | Yes |
| not_found | Resource not found (e.g., 404) | No | No |
| server | Server-side errors (e.g., 500) | Yes | Yes |
| validation | Client-side validation errors | No | No |
| unknown | Unknown or unexpected errors | No | No |

## Error Handling Decorators

The system provides these decorators for error handling:

1. `@handle_rss_service`: For service-level RSS functions
   - Catches and classifies exceptions
   - Provides automatic retries for transient errors
   - Adds context information to errors

2. `@handle_rss_cli`: For CLI command functions
   - Displays user-friendly error messages
   - Adds troubleshooting hints for specific error types
   - Shows detailed context in verbose mode
   - Sets appropriate exit codes

## Error Classification

Errors are classified using a multi-step approach:

1. Type-based checks first (using `isinstance()`)
2. Content-based checks second (using string matching)
3. Default classification as fallback

This ensures robust classification even when exceptions come from different libraries.

## Example Usage

### Service Layer

```python
from local_newsifier.errors.rss import handle_rss_service

@handle_rss_service
def fetch_rss_feed(url):
    # Code that might raise exceptions
    response = requests.get(url)
    response.raise_for_status()
    # Parse response...
    return parsed_data
```

### CLI Layer

```python
from local_newsifier.errors.rss import handle_rss_cli

@click.command()
@click.argument("url")
@handle_rss_cli
def fetch_command(url):
    result = fetch_rss_feed(url)
    click.echo(f"Found {len(result)} entries")
```

### Raising Errors

```python
from local_newsifier.errors.error import ServiceError

def validate_feed(feed):
    if not feed.get("entries"):
        raise ServiceError(
            service="rss",
            error_type="feed_validation",
            message="Feed has no entries",
            context={"feed_url": feed.get("url")}
        )
```

## Import Order

The import order in error handling modules is critical to prevent circular dependencies:

1. First, import core error components from `error.py`
2. Then import service-specific components
3. Register service-specific error types with `ERROR_TYPES`
4. Finally, import handlers that might depend on both error and service components

The module's `__init__.py` handles this order automatically.

## Best Practices

1. Always use appropriate decorators for error handling
2. Provide detailed context when raising `ServiceError` directly
3. Let the error handling system handle classification when possible
4. Don't catch `ServiceError` unless you plan to reclassify it
5. Use explicit import order to avoid circular dependencies

## CLI Error Messages

When errors occur in CLI commands, users are presented with:

1. A clear error message showing the service and error type
2. A troubleshooting hint for the specific error type
3. Detailed context information in verbose mode

Example output:

```
Error: rss.xml_parse: XML parsing error: Syntax error at line 3
Hint: Failed to parse XML content. The feed may have syntax errors.
```

In verbose mode (with `--verbose` flag):

```
Error: rss.xml_parse: XML parsing error: Syntax error at line 3
Hint: Failed to parse XML content. The feed may have syntax errors.
Context:
  function: parse_rss_feed
  url: https://example.com/feed.xml
  args: ['https://example.com/feed.xml']
Original error: ParseError: syntax error at line 3, column 10
```
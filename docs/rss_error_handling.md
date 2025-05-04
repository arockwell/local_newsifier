# RSS Feed Error Handling

This document describes the error handling approach for RSS feed operations in the Local Newsifier system.

## Overview

The RSS feed service has been enhanced with streamlined error handling that:

1. Categorizes errors into specific types
2. Provides consistent error messages with troubleshooting hints
3. Automatically retries transient errors
4. Preserves error context for debugging
5. Presents user-friendly error messages in the CLI

## Error Types

The system classifies RSS feed errors into the following categories:

| Error Type       | Description                                   | Transient | Retryable | Exit Code |
|------------------|-----------------------------------------------|-----------|-----------|-----------|
| network          | Network connectivity issues                   | Yes       | Yes       | 2         |
| timeout          | Connection or request timeouts                | Yes       | Yes       | 3         |
| rate_limit       | Rate limiting or throttling                   | Yes       | Yes       | 4         |
| auth             | Authentication or authorization errors        | No        | No        | 5         |
| parse            | General response parsing errors               | No        | No        | 6         |
| xml_parse        | XML syntax errors in feed                     | No        | No        | 10        |
| feed_format      | Invalid feed structure                        | No        | No        | 11        |
| feed_validation  | Missing required feed elements                | No        | No        | 12        |
| url              | Malformed or invalid URLs                     | No        | No        | 13        |
| encoding         | Character encoding issues                     | No        | No        | 14        |
| validation       | Input validation errors                       | No        | No        | 7         |
| not_found        | Resource not found (404)                      | No        | No        | 8         |
| server           | Server-side errors (5xx)                      | Yes       | Yes       | 9         |
| unknown          | Unclassified errors                          | No        | No        | 1         |

## Usage

### Service Layer

The RSS feed service uses the `@handle_rss_service` decorator to apply error handling:

```python
from local_newsifier.errors.rss import handle_rss_service

@handle_rss_service
def process_feed(self, feed_id: int) -> Dict[str, Any]:
    # This method will have automatic error handling:
    # - Errors are classified into types
    # - Transient errors are retried automatically
    # - Context is captured for debugging
    # - All errors are converted to ServiceError
```

### CLI Layer

The CLI commands use the `@handle_rss_cli` decorator to provide user-friendly error presentation:

```python
from local_newsifier.errors.rss import handle_rss_cli

@feeds_group.command(name="add")
@click.argument("url", required=True)
@handle_rss_cli
def add_feed(url, name, description):
    # This command will have user-friendly error presentation:
    # - Errors include troubleshooting hints
    # - Debug info shown in verbose mode
    # - Proper exit codes returned
```

## Error Message Examples

Examples of user-facing error messages:

- Network error: "Could not connect to RSS feed. Check the feed URL and your internet connection."
- XML parsing error: "Failed to parse XML content. The feed may have syntax errors."
- Feed format error: "Feed structure doesn't match expected RSS or Atom format. Verify it's a valid feed."
- URL error: "Feed URL is malformed or invalid. Check the URL format."

## Exception Flow

1. Low-level errors (e.g., requests.ConnectionError) are caught by `@handle_rss_service`
2. Errors are classified into error types (network, parse, etc.) with `_classify_rss_error`
3. Original exception and context are preserved in ServiceError
4. Transient errors may be retried automatically
5. CLI decorator `@handle_rss_cli` presents user-friendly errors

## Implementation

Key files:
- `errors/rss.py`: RSS-specific error handling
- `errors/handlers.py`: Generic service handlers
- `errors/error.py`: Core error components
- `errors/cli.py`: CLI error presentation

## Debugging

To get detailed error information in the CLI, use the `--verbose` flag:

```
$ nf feeds add http://invalid-url --verbose
```

This will show:
- Error message and hint
- Service and error type
- Function and parameters that failed
- Original exception details
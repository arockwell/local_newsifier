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

| Type         | Description              | Transient | Exit Code |
|--------------|--------------------------|-----------|-----------|
| `network`    | Network connectivity     | Yes       | 2         |
| `timeout`    | Request timed out        | Yes       | 3         |
| `rate_limit` | Rate limit exceeded      | Yes       | 4         |
| `auth`       | Authentication failed    | No        | 5         |
| `parse`      | Failed to parse response | No        | 6         |
| `validation` | Input validation failed  | No        | 7         |
| `not_found`  | Resource not found       | No        | 8         |
| `server`     | Server-side error        | Yes       | 9         |
| `connection` | Database connection issue| Yes       | 10        |
| `integrity`  | Database constraint issue| No        | 11        |
| `multiple`   | Multiple results found   | No        | 12        |
| `transaction`| Database transaction error| Yes      | 13        |
| `unknown`    | Unknown error            | No        | 1         |

## Using Error Handling

### Service Methods

```python
from local_newsifier.errors import handle_apify, handle_database

class ApifyService:
    
    @handle_apify
    def run_actor(self, actor_id, run_input):
        """Run an Apify actor with full error handling.
        
        Errors will be automatically transformed, retried, and timed.
        """
        return self.client.actor(actor_id).call(run_input=run_input)

class ArticleService:
    
    @handle_database
    def get_article(self, article_id: int):
        """Get an article with database error handling.
        
        Database errors like connection issues or constraint violations
        will be properly classified and handled.
        """
        with self.session_factory() as session:
            return self.article_crud.get(session, id=article_id)
```

### Database Error Handling and Retry Behavior

The `@handle_database` decorator provides robust error handling for database operations:

- **Classification**: Automatically classifies SQLAlchemy exceptions into appropriate error types
- **Error Messages**: Provides descriptive error messages with troubleshooting hints
- **Retry Logic**: Automatically retries transient errors with backoff

#### Retry Behavior for Database Errors

| Error Type    | Is Retried | Retry Attempts | Description                                      |
|---------------|------------|----------------|--------------------------------------------------|
| `connection`  | Yes        | 3 (default)    | Database connection issues, server unavailable   |
| `timeout`     | Yes        | 3 (default)    | Query timeout, long-running operations          |
| `transaction` | Yes        | 3 (default)    | Transaction errors, deadlocks                   |
| `integrity`   | No         | N/A            | Constraint violations (unique, foreign key)     |
| `validation`  | No         | N/A            | Input validation failures                       |
| `not_found`   | No         | N/A            | Record not found (business logic issue)         |
| `multiple`    | No         | N/A            | Multiple records when one expected              |

Each retry uses exponential backoff (1s, 2s, 4s) to allow temporary issues to resolve.
```

### CLI Commands

```python
from local_newsifier.errors import handle_apify_cli, handle_database_cli
import click

@click.command()
@handle_apify_cli
def test_apify_command():
    """CLI command with Apify error handling."""
    # Run code that might raise Apify exceptions
    # Errors will be presented in user-friendly format
    
@click.command()
@handle_database_cli
def database_command():
    """CLI command with database error handling."""
    with session_factory() as session:
        # Database operations with user-friendly error messages
        results = session.exec(select(User)).all()
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
- `@handle_database` - For database operations
- `@handle_apify_cli` - For Apify CLI commands
- `@handle_rss_cli` - For RSS CLI commands
- `@handle_database_cli` - For database CLI commands

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
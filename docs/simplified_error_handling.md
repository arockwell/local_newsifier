# Simplified Error Handling

This guide explains the streamlined error handling framework with reduced line count.

## Core Concepts

The simplified error handling system maintains the same key principles as the original:

1. **Unified Error Type**: A single `ServiceError` class
2. **Descriptive Errors**: Context-rich errors with troubleshooting info
3. **Consistent Patterns**: Same approach across all services

The primary improvements are:

1. **Reduced Line Count**: Combined decorators and simplified classifications
2. **Simplified API**: Fewer functions with more focused responsibilities
3. **Consolidated Error Messages**: Unified error message dictionary

## Using Error Handling

### Basic Usage

```python
from local_newsifier.errors.simplified_init import handle_apify, handle_database, ServiceError

class ApifyService:
    @handle_apify
    def run_actor(self, actor_id, run_input):
        """Run an Apify actor with full error handling.
        
        All error handling, retry, and timing is handled automatically.
        """
        return self.client.actor(actor_id).call(run_input=run_input)

class ArticleService:
    @handle_database
    def get_article(self, article_id: int):
        """Get an article with database error handling.
        """
        with self.session_factory() as session:
            return self.article_crud.get(session, id=article_id)
```

### CLI Commands

```python
from local_newsifier.errors.simplified_init import handle_apify_cli, handle_database_cli
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

### Custom Error Handlers

You can create custom service handlers using the `create_handler` function:

```python
from local_newsifier.errors.simplified_init import create_handler

# Create a custom handler for a new service
handle_custom_service = create_handler(
    service="custom_service",
    retry_attempts=2,
    include_timing=True
)

class CustomService:
    @handle_custom_service
    def custom_operation(self):
        # This operation gets automatic error handling, retry, and timing
        pass
```

### Manual Error Handling

```python
from local_newsifier.errors.simplified_init import ServiceError

try:
    # Some operation that might fail
    result = service.operation()
except ServiceError as e:
    if e.error_type == "not_found":
        # Handle not found case
        return None
    elif e.transient:
        # Log transient errors
        logger.warning(f"Transient error: {e}")
        raise
    else:
        # Handle other errors
        raise
```

## Line Count Comparison

| Component | Original | Simplified | Reduction |
|-----------|----------|------------|-----------|
| error.py  | ~340 lines | ~210 lines | ~38% |
| handlers.py | ~120 lines | ~55 lines | ~54% |
| cli.py | ~75 lines | ~58 lines | ~23% |
| **Total** | **~535 lines** | **~323 lines** | **~40%** |

## Key Improvements

1. **Combined Decorators**: The `create_handler` function combines error handling, retry, and timing in a single decorator
2. **Simplified Classification**: Error classification is more concise with lookup tables
3. **Reduced Boilerplate**: Removed redundant code patterns and combined similar functions
4. **Consolidated Error Messages**: All error messages are in a single nested dictionary
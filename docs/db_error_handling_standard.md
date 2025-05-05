# Database Error Handling Standard

This document outlines the standard approach for handling database errors in the Local Newsifier application.

## Core Principle

We use a **decorator-based approach** for consistent error handling across all database operations. The `@handle_database` decorator should be applied to service methods that interact with the database.

## Advantages of this Approach

1. **Separation of concerns**:
   - CRUD operations focus purely on data access
   - Services handle error handling and business logic
   - Error handling logic is centralized in one place

2. **Simplified code**:
   - Consistent error handling pattern across services
   - Error handling is visible at the call site via decorator
   - No need for parallel class hierarchies

3. **Rich error context**:
   - Automatically captures function name, arguments, and context
   - Converts SQL errors to domain-specific error types
   - Provides user-friendly error messages

4. **Automatic retry**:
   - Transient errors are automatically retried with backoff
   - Configurable retry attempts
   - Only retries appropriate error types (connection, timeout, etc.)

## Standard Pattern

### Service Methods

```python
from local_newsifier.errors import handle_database

class ArticleService:
    
    @handle_database
    def get_article(self, article_id: int):
        """Get article by ID with database error handling.
        
        Args:
            article_id: ID of the article
            
        Returns:
            Article if found
            
        Raises:
            ServiceError: On database errors with appropriate classification
        """
        with self.session_factory() as session:
            article = self.article_crud.get(session, id=article_id)
            if not article:
                # No need to handle this case - returning None is appropriate
                return None
            return article
            
    @handle_database
    def create_article(self, article_data):
        """Create a new article with database error handling.
        
        Args:
            article_data: Data for the new article
            
        Returns:
            Created article
            
        Raises:
            ServiceError: On database errors with appropriate classification
              - "integrity" type for duplicate entries
              - "validation" type for validation errors
              - "connection" type for connection issues
        """
        with self.session_factory() as session:
            article = self.article_crud.create(session, obj_in=article_data)
            return article
```

### Error Classification

All database errors are classified into these types:

| Error Type    | Transient | Description                                      |
|---------------|-----------|--------------------------------------------------|
| `connection`  | Yes       | Database connection issues, server unavailable   |
| `timeout`     | Yes       | Query timeout, long-running operations           |
| `transaction` | Yes       | Transaction errors, deadlocks                    |
| `integrity`   | No        | Constraint violations (unique, foreign key)      |
| `validation`  | No        | Input validation failures                        |
| `not_found`   | No        | Record not found (business logic issue)          |
| `multiple`    | No        | Multiple records when one expected               |

### Retry Behavior

Transient errors are automatically retried with exponential backoff:

```python
# This method will retry automatically for connection issues
@handle_database
def get_article(self, article_id: int):
    with self.session_factory() as session:
        return self.article_crud.get(session, id=article_id)
```

Each retry uses exponential backoff (1s, 2s, 4s) to allow temporary issues to resolve.

## API Integration

For API endpoints, catch `ServiceError` and convert to appropriate HTTP responses:

```python
from fastapi import APIRouter, Depends, HTTPException
from local_newsifier.errors import ServiceError

router = APIRouter()

@router.get("/articles/{article_id}")
def get_article(
    article_id: int,
    article_service: ArticleService = Depends(get_article_service)
):
    try:
        article = article_service.get_article(article_id)
        if not article:
            raise HTTPException(status_code=404, detail="Article not found")
        return article
    except ServiceError as e:
        # Map error types to status codes
        status_code_map = {
            "not_found": 404,
            "integrity": 409,
            "validation": 422,
            "connection": 503,
            "timeout": 504,
        }
        status_code = status_code_map.get(e.error_type, 500)
        raise HTTPException(
            status_code=status_code,
            detail={"error": str(e), "type": e.error_type}
        )
```

## CLI Integration

For CLI commands, use the CLI-specific decorators that format errors for the command line:

```python
from local_newsifier.errors import handle_database_cli
import click

@click.command()
@click.argument("article_id", type=int)
@handle_database_cli
def get_article_command(article_id: int):
    """CLI command that accesses the database."""
    with session_factory() as session:
        article = article_crud.get(session, id=article_id)
        if article:
            click.echo(f"Article: {article.title}")
        else:
            click.echo("Article not found")
```

## Best Practices

1. **Apply decorator at service layer**:
   - Decorate methods in service classes, not CRUD classes
   - Each service method that uses the database should have the decorator

2. **Don't double-wrap**:
   - If a service method calls another decorated method, no need to decorate both

3. **Use appropriate session management**:
   - Always use context managers for database sessions
   - Pass session to CRUD operations, don't create new ones

4. **Document error behavior**:
   - Add docstrings that mention possible error types
   - Document how different database errors are handled

5. **Consistent error handling**:
   - Use the same pattern across all services
   - Ensure API endpoints handle ServiceError consistently
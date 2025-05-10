# Error Handling Standards for Local Newsifier

This document outlines the standardized approach for error handling across the Local Newsifier application, focusing on the decorator-based error handling pattern that has been adopted project-wide.

## Core Architecture 

The Local Newsifier project uses a **decorator-based approach** for consistent error handling. This approach has been chosen over parallel class hierarchies (like `ErrorHandledCRUD`) to simplify the codebase and create clearer separation of concerns.

### Key Components

1. **Service-Level Decorators**:
   - `@handle_database` - For database operations 
   - `@handle_apify` - For Apify API operations
   - `@handle_rss` - For RSS feed operations
   - `@handle_web_scraper` - For web scraping operations

2. **Error Classification System**:
   - Classifies errors by type (connection, integrity, validation, etc.)
   - Determines which errors are transient (can be retried)
   - Generates user-friendly error messages

3. **Automatic Retry Logic**:
   - Transparently retries operations for transient errors
   - Uses exponential backoff (1s, 2s, 4s) to allow temporary issues to resolve
   - Only retries appropriate error types (connection, timeout, etc.)

## Error Types

All errors are classified into these types:

| Error Type    | Transient | Description                                      |
|---------------|-----------|--------------------------------------------------|
| `connection`  | Yes       | Connection issues (database, API, network)       |
| `timeout`     | Yes       | Query/request timeout, long-running operations   |
| `transaction` | Yes       | Transaction errors, deadlocks                    |
| `integrity`   | No        | Constraint violations (unique, foreign key)      |
| `validation`  | No        | Input validation failures                        |
| `not_found`   | No        | Resource not found (business logic issue)        |
| `auth`        | No        | Authentication/authorization failures            |
| `multiple`    | No        | Multiple records when one expected               |
| `format`      | No        | Invalid format in response or request            |

## Standard Pattern

### Database Operations

```python
from local_newsifier.errors import handle_database

class ArticleService:
    
    @handle_database
    def get_article(self, article_id: int):
        """Get article by ID with database error handling.
        
        Returns:
            Article if found
            
        Raises:
            ServiceError: On database errors with appropriate classification
        """
        with self.session_factory() as session:
            article = self.article_crud.get(session, id=article_id)
            if not article:
                return None
            return article
```

### API Operations

```python
from local_newsifier.errors import handle_apify

class ApifyService:
    
    @handle_apify
    def run_actor(self, actor_id: str, run_input: dict):
        """Run an Apify actor with error handling.
        
        Raises:
            ServiceError: On API errors with appropriate classification
        """
        return self.client.actor(actor_id).call(run_input=run_input)
```

### RSS Operations

```python
from local_newsifier.errors import handle_rss

class RSSFeedService:
    
    @handle_rss
    def parse_feed(self, feed_url: str):
        """Parse RSS feed with error handling.
        
        Raises:
            ServiceError: On RSS parsing errors with appropriate classification
        """
        feed = feedparser.parse(feed_url)
        if feed.bozo:
            raise ValueError(f"Invalid RSS feed: {feed.bozo_exception}")
        return feed
```

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

## Implementation Details

Each service that interacts with external systems should use the appropriate decorator:

1. **Database Services**: 
   - AnalysisService, ArticleService, EntityService - `@handle_database`

2. **API Services**:
   - ApifyService - `@handle_apify`

3. **Feed Services**:
   - RSSFeedService - `@handle_rss` and `@handle_database`

4. **Pipeline Services**:
   - NewsPipelineService - `@handle_database` and `@handle_web_scraper`

For each decorated method, an undecorated implementation method is provided to support existing tests:

```python
@handle_database
def get_articles_by_date(self, start_date, end_date):
    """Get articles within date range with error handling."""
    return self._get_articles_by_date_impl(start_date, end_date)
    
def _get_articles_by_date_impl(self, start_date, end_date):
    """Implementation method without error handling for testing."""
    with self.session_factory() as session:
        return self.article_crud.get_by_date_range(session, start_date, end_date)
```

## Benefits of Decorator-based Approach

1. **Simpler architecture**:
   - No need for parallel class hierarchies
   - Single, centralized error handling mechanism
   - Error handling clearly visible at the call site

2. **Better separation of concerns**:
   - CRUD classes handle data access only
   - Services handle business logic and error handling
   - Clearer responsibility boundaries

3. **Reduced code duplication**:
   - One unified error handling mechanism
   - Consistent error messaging
   - Central place for improvements

4. **Better integration with the architecture**:
   - Aligns better with the service-oriented architecture
   - Services can customize retry behavior as needed
   - More consistent with FastAPI error handling approach

## Best Practices

1. **Apply decorator at service layer**:
   - Decorate methods in service classes, not CRUD classes
   - Each service method that uses external systems should have the appropriate decorator

2. **Don't double-wrap**:
   - If a service method calls another decorated method, no need to decorate both

3. **Use appropriate session management**:
   - Always use context managers for database sessions
   - Pass session to CRUD operations, don't create new ones

4. **Document error behavior**:
   - Add docstrings that mention possible error types
   - Document how different errors are handled

5. **Consistent error handling**:
   - Use the same pattern across all services
   - Ensure API endpoints handle ServiceError consistently
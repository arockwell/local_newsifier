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

Using decorators at the service layer makes API error handling much simpler and more consistent. When all service methods properly classify their errors, API endpoints can handle them uniformly:

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

The benefit here is that the same error handling code works for multiple services and error types:

```python
@router.post("/articles")
def create_article(
    article_data: ArticleCreate,
    article_service: ArticleService = Depends(get_article_service)
):
    try:
        # @handle_database decorator handles all possible database errors
        article_id = article_service.create_article(article_data)
        return {"id": article_id}
    except ServiceError as e:
        # Same error handling code works for all error types
        # The decorator has already classified the error correctly
        status_code_map = {
            "not_found": 404,
            "integrity": 409,  # Duplicate article URLs return 409 Conflict
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

This unified error handling approach can be further simplified with a custom exception handler:

```python
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI()

@app.exception_handler(ServiceError)
async def service_error_handler(request: Request, exc: ServiceError):
    """Unified error handler for all ServiceErrors."""
    status_code_map = {
        "not_found": 404,
        "integrity": 409,
        "validation": 422,
        "connection": 503,
        "timeout": 504,
        "auth": 401,
        "rate_limit": 429,
    }
    status_code = status_code_map.get(exc.error_type, 500)

    return JSONResponse(
        status_code=status_code,
        content={
            "error": str(exc),
            "type": exc.error_type,
            "service": exc.service,
            "transient": exc.transient
        }
    )
```

With this handler registered, your API endpoints become much simpler:

```python
@router.get("/articles/{article_id}")
def get_article(
    article_id: int,
    article_service: ArticleService = Depends(get_article_service)
):
    # ServiceErrors are automatically caught and handled
    # with the appropriate status code
    article = article_service.get_article(article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return article
```

## CLI Integration

For CLI commands, specialized decorators provide user-friendly error handling:

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

The CLI-specific decorator translates errors into user-friendly messages with appropriate exit codes:

```
# Without decorator, raw SQLAlchemy errors:
$ nf db article 123
Traceback (most recent call last):
  File "/app/venv/lib/python3.10/site-packages/sqlalchemy/engine/base.py", line 1900, in _execute_context
    self.dialect.do_execute(
  File "/app/venv/lib/python3.10/site-packages/sqlalchemy/engine/default.py", line 736, in do_execute
    cursor.execute(statement, parameters)
psycopg2.OperationalError: could not connect to server: Connection refused

# With decorator, user-friendly message and exit code:
$ nf db article 123
Error: Could not connect to the database. Check database connection settings.
```

Similarly for RSS feed operations:

```python
@click.command()
@click.argument("feed_url")
@handle_rss_cli
def process_feed_command(feed_url: str):
    """Process an RSS feed."""
    feed_service = get_feed_service()
    results = feed_service.process_feed(feed_url)
    click.echo(f"Processed {len(results)} articles from {feed_url}")
```

If the RSS feed is unreachable:

```
# Without decorator:
$ nf feeds process https://example.com/rss
Traceback (most recent call last):
  File "/app/venv/lib/python3.10/site-packages/urllib3/connectionpool.py", line 703, in urlopen
    httplib_response = self._make_request(
  File "/app/venv/lib/python3.10/site-packages/urllib3/connectionpool.py", line 386, in _make_request
    self._validate_conn(conn)
  File "/app/venv/lib/python3.10/site-packages/urllib3/connectionpool.py", line 1042, in _validate_conn
    conn.connect()
ConnectionError: Connection refused

# With decorator:
$ nf feeds process https://example.com/rss
Error: Could not connect to RSS feed. Check the feed URL and your internet connection.
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

## Practical Benefits

Here are specific benefits that the decorator-based approach provides:

1. **Automatic retry logic for transient errors**:
   ```python
   # Without decorator:
   def get_article(self, article_id):
       max_attempts = 3
       for attempt in range(max_attempts):
           try:
               with self.session_factory() as session:
                   article = self.article_crud.get(session, id=article_id)
                   return article
           except OperationalError as e:
               if "connection" in str(e).lower() and attempt < max_attempts - 1:
                   time.sleep(2 ** attempt)  # Exponential backoff
                   continue
               raise

   # With decorator:
   @handle_database
   def get_article(self, article_id):
       with self.session_factory() as session:
           article = self.article_crud.get(session, id=article_id)
           return article
   ```

2. **Rich error classification and context**:
   ```python
   # Raw database error:
   sqlalchemy.exc.IntegrityError: (psycopg2.errors.UniqueViolation) duplicate key value violates unique constraint "ix_articles_url"

   # With decorator, becomes:
   ServiceError: database.integrity: Database constraint violation. The operation violates database rules.
   # With additional context:
   {
     "function": "create_article",
     "args": ["ArticleService"],
     "kwargs": {"url": "https://example.com/news/1"},
     "original": "IntegrityError: duplicate key value violates unique constraint"
   }
   ```

3. **Performance monitoring**:
   ```
   # Automatically logs timing info:
   INFO: database.get_article succeeded in 0.342s
   INFO: database.create_article failed in 0.156s
   ```

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

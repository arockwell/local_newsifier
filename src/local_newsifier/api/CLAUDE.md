# Local Newsifier API Guide

## Overview
The API module provides a web interface for the Local Newsifier system using FastAPI. It includes both HTML user interfaces (using Jinja2 templates) and JSON API endpoints for programmatic access.

## Key Components

### Main Application
- **main.py**: Configures and initializes the FastAPI application
- Sets up templates, static files, middleware, and exception handlers
- Includes routes for the root path and health check

### Routers
- **system.py**: Database exploration and system status endpoints
- **tasks.py**: Task management and monitoring endpoints
- **auth.py**: Authentication and authorization (currently basic)

### Templates
- Located in `templates/` directory
- Uses Jinja2 for dynamic rendering
- Base template (`base.html`) extends Bootstrap styling
- Specialized templates for different views (tables, detail pages, etc.)

## Key Patterns

### Dependency Injection
The API uses **fastapi-injectable** for all dependencies. Provider functions expose the required components and are injected using FastAPI's `Depends()` pattern:

#### Injectable Pattern
```python
from typing import Annotated
from fastapi import Depends
from local_newsifier.di.providers import get_session, get_entity_service
from local_newsifier.services.entity_service import EntityService

@router.get("/entities/{entity_id}")
async def get_entity(
    entity_id: int,
    request: Request,
    entity_service: Annotated[EntityService, Depends(get_entity_service)]
):
    entity = entity_service.get_entity(entity_id)
    return templates.TemplateResponse(...)
```

### Hybrid Response Model
The API supports both UI (HTML) and API (JSON) responses:

1. **HTML Responses** - For human interaction:
```python
@router.get("/tables", response_class=HTMLResponse)
async def get_tables(request: Request, session: Session = Depends(get_session)):
    tables_info = get_tables_info(session)
    return templates.TemplateResponse(
        "tables.html",
        {"request": request, "tables_info": tables_info}
    )
```

2. **JSON Responses** - For programmatic access:
```python
@router.get("/tables/api", response_model=List[Dict])
async def get_tables_api(session: Session = Depends(get_session)):
    return get_tables_info(session)
```

### Template Path Configuration
The template path is dynamically determined based on the environment:

```python
# Get the templates directory path
if os.path.exists("src/local_newsifier/api/templates"):
    # Development environment
    templates_dir = "src/local_newsifier/api/templates"
else:
    # Production environment - use package-relative path
    templates_dir = str(pathlib.Path(__file__).parent / "templates")
```


## SQLModel Parameter Binding
When using SQLModel for database queries, remember to bind parameters to the query:

```python
# Correct approach for parameter binding
query = select([column_name]).where(table_name == table)
query = query.bindparams(table_name=table_name)
columns = session.exec(query).all()
```

## Exception Handling
The API includes exception handlers for common errors:

```python
@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    return templates.TemplateResponse(
        "404.html",
        {"request": request, "detail": exc.detail},
        status_code=404
    )
```

## Best Practices

### Session Management
- Always use the `get_session` dependency for database operations
- Don't pass database objects between request handlers
- Use IDs to reference database objects across requests

### Response Model Validation
- Use Pydantic models for response validation with `response_model`
- Keep response models separate from database models

### URL Path Structure
- Use semantic URLs (e.g., `/tables/{table_name}` instead of `/table?name={table_name}`)
- Maintain consistency in URL naming (plural nouns for collections)
- Include API-specific endpoints with `/api` suffix

### Common Patterns for Endpoint Development
1. Get dependencies (session and services)
2. Validate inputs
3. Delegate business logic to services
4. Transform response data as needed
5. Return appropriate response (HTML or JSON)

## Async Endpoints

The API now includes async endpoints for handling I/O-intensive operations, particularly webhooks and concurrent data processing.

### Async Webhook Handling

The webhook router demonstrates async patterns:

```python
from typing import Annotated
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from local_newsifier.database.async_engine import get_async_session
from local_newsifier.services.apify_webhook_service_async import ApifyWebhookServiceAsync

@router.post("/webhooks/apify", status_code=202)
async def apify_webhook(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_async_session)],
    apify_webhook_signature: Annotated[str | None, Header()] = None
):
    # Get raw body for signature validation
    body = await request.body()
    data = await request.json()

    # Create async service
    service = ApifyWebhookServiceAsync(
        session=session,
        webhook_secret=settings.APIFY_WEBHOOK_SECRET
    )

    # Validate signature if provided
    if apify_webhook_signature:
        if not service.validate_signature(body.decode(), apify_webhook_signature):
            raise HTTPException(status_code=401, detail="Invalid signature")

    # Process webhook asynchronously
    result = await service.process_webhook(data)

    return {"status": "accepted", "webhook_id": result["webhook_id"]}
```

### Async Database Operations in Endpoints

Use async sessions for database operations:

```python
@router.get("/articles/{article_id}")
async def get_article_async(
    article_id: int,
    session: Annotated[AsyncSession, Depends(get_async_session)]
):
    # Use async query syntax
    stmt = select(Article).where(Article.id == article_id)
    result = await session.execute(stmt)
    article = result.scalar_one_or_none()

    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    return article.model_dump()
```

### When to Use Async Endpoints

**Use Async Endpoints For:**
- Webhook handlers that process external notifications
- Endpoints that make multiple database queries
- Integration with async external APIs
- File upload/download operations
- Real-time data streaming

**Use Sync Endpoints For:**
- Simple CRUD operations
- Template rendering without complex queries
- Legacy code integration
- CPU-bound operations (consider background tasks instead)

## Injectable Services in Endpoints

All endpoints now use fastapi-injectable for dependency injection:

### Service Injection Pattern

```python
from typing import Annotated
from fastapi import Depends
from local_newsifier.di.providers import get_entity_service
from local_newsifier.services.entity_service import EntityService

@router.get("/entities/{entity_id}")
async def get_entity(
    entity_id: int,
    entity_service: Annotated[EntityService, Depends(get_entity_service)]
):
    entity = entity_service.get_entity(entity_id)
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    return entity
```

### Testing Endpoints

Test endpoints by overriding dependencies:

```python
from fastapi.testclient import TestClient

def test_webhook_endpoint(test_client: TestClient):
    # Mock the async session dependency
    async def mock_session():
        return MagicMock()

    app.dependency_overrides[get_async_session] = mock_session

    # Test the endpoint
    response = test_client.post(
        "/webhooks/apify",
        json={"eventType": "ACTOR.RUN.SUCCEEDED"}
    )
    assert response.status_code == 202
```

## Best Practices for Async Endpoints

1. **Always await async operations**: Forgetting `await` will return a coroutine instead of a result
2. **Use async context managers**: For database sessions and other resources
3. **Handle exceptions properly**: Use try/except with proper error responses
4. **Avoid blocking operations**: Don't use sync I/O in async endpoints
5. **Consider timeouts**: For external API calls and long operations

For more information on dependency injection patterns, see `docs/dependency_injection.md`.

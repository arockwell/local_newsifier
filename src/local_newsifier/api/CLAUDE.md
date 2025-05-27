# Local Newsifier API Guide

## Overview
The API module provides a web interface for the Local Newsifier system using FastAPI. It includes both HTML user interfaces (using Jinja2 templates) and JSON API endpoints for programmatic access. All endpoints use synchronous patterns - no async/await code.

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
def get_entity(
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
def get_tables(request: Request, session: Session = Depends(get_session)):
    tables_info = get_tables_info(session)
    return templates.TemplateResponse(
        "tables.html",
        {"request": request, "tables_info": tables_info}
    )
```

2. **JSON Responses** - For programmatic access:
```python
@router.get("/tables/api", response_model=List[Dict])
def get_tables_api(session: Session = Depends(get_session)):
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
def not_found_handler(request: Request, exc: HTTPException):
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

## Sync-Only Endpoints

> **CRITICAL**: This project uses ONLY synchronous patterns. No async/await code is allowed.

### Why Sync-Only?
- Simpler debugging and error handling
- Easier to understand execution flow
- Better compatibility with existing tools
- Reduced complexity in testing

### Implementing Sync Endpoints

Here's how to implement endpoints using synchronous patterns:

```python
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from local_newsifier.di.providers import get_session
from local_newsifier.models.article import Article

@router.post("/webhooks/apify", status_code=202)
def apify_webhook(
    request: Request,
    session: Annotated[Session, Depends(get_session)],
    apify_webhook_signature: Annotated[str | None, Header()] = None
):
    # Get body for signature validation
    body = request.body()
    data = request.json()

    # Use sync service
    from local_newsifier.services.apify_webhook_service import ApifyWebhookService
    service = ApifyWebhookService(
        session=session,
        webhook_secret=settings.APIFY_WEBHOOK_SECRET
    )

    # Process webhook synchronously
    result = service.process_webhook(data)
    return {"status": "accepted", "webhook_id": result["webhook_id"]}

@router.get("/articles/{article_id}")
def get_article(
    article_id: int,
    session: Annotated[Session, Depends(get_session)]
):
    # Use sync query
    stmt = select(Article).where(Article.id == article_id)
    article = session.exec(stmt).first()

    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    return article.model_dump()
```

## Injectable Services in Endpoints

All endpoints now use fastapi-injectable for dependency injection:

### Service Injection Pattern

```python
from typing import Annotated
from fastapi import Depends
from local_newsifier.di.providers import get_entity_service
from local_newsifier.services.entity_service import EntityService

@router.get("/entities/{entity_id}")
def get_entity(
    entity_id: int,
    entity_service: Annotated[EntityService, Depends(get_entity_service)]
):
    entity = entity_service.get_entity(entity_id)
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    return entity
```

### Testing Sync Endpoints

Test endpoints by overriding dependencies:

```python
from fastapi.testclient import TestClient
from unittest.mock import Mock

def test_webhook_endpoint(test_client: TestClient):
    # Mock the session dependency
    mock_session = Mock()

    app.dependency_overrides[get_session] = lambda: mock_session

    # Test the endpoint
    response = test_client.post(
        "/webhooks/apify",
        json={"eventType": "ACTOR.RUN.SUCCEEDED"}
    )
    assert response.status_code == 202
```

## Best Practices for Sync Endpoints

1. **Use dependency injection**: Always inject services and sessions via `Depends()`
2. **Handle exceptions properly**: Use try/except with proper error responses
3. **Return IDs not objects**: Avoid passing SQLModel objects between requests
4. **Keep endpoints focused**: Delegate business logic to services
5. **Use appropriate HTTP status codes**: 200 for success, 404 for not found, etc.

For more information on dependency injection patterns, see `docs/dependency_injection.md`.

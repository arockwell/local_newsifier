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
from fastapi_injectable import injectable
from local_newsifier.di.providers import get_session

@router.get("/entities/{entity_id}")
async def get_entity(
    entity_id: int,
    request: Request,
    entity_service: Annotated[EntityService, Depends()]
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

## Injectable Endpoints

The project is migrating to fastapi-injectable for dependency injection. This section describes how to create FastAPI endpoints using the new pattern.

### Injectable Dependency Resolution

With fastapi-injectable, dependencies are automatically resolved:

```python
from typing import Annotated
from fastapi import Depends
from fastapi_injectable import injectable
from local_newsifier.services.injectable_entity_service import InjectableEntityService

@router.get("/entities/{entity_id}")
async def get_entity(
    entity_id: int,
    request: Request,
    entity_service: Annotated[InjectableEntityService, Depends()]
):
    entity = entity_service.get_entity(entity_id)
    return templates.TemplateResponse(
        "entity_detail.html",
        {"request": request, "entity": entity}
    )
```

### API Endpoint with Injectable Dependencies

For JSON API endpoints:

```python
from typing import Annotated
from fastapi import Depends
from pydantic import BaseModel
from local_newsifier.services.injectable_entity_service import InjectableEntityService

class EntityResponse(BaseModel):
    id: int
    name: str
    entity_type: str
    
@router.get("/api/entities/{entity_id}", response_model=EntityResponse)
async def get_entity_api(
    entity_id: int,
    entity_service: Annotated[InjectableEntityService, Depends()]
):
    return entity_service.get_entity(entity_id)
```

### Testing Injectable Endpoints

Testing endpoints with injectable dependencies:

```python
def test_get_entity_endpoint(test_client_with_mocks):
    # The client has all dependencies mocked via dependency overrides
    response = test_client_with_mocks.get("/entities/1")
    assert response.status_code == 200
```

For more information on fastapi-injectable usage, see `docs/fastapi_injectable.md`.

# Simplified Error Handling for CRUD Operations

This document provides an overview of the simplified approach to error handling for CRUD operations in the Local Newsifier application.

## Overview

The simplified error handling approach provides standardized error handling for database operations while maintaining compatibility with the fastapi-injectable dependency injection system. It focuses on core functionality with a minimal implementation that's easy to understand and extend.

## Components

The implementation consists of the following components:

1. **`ErrorHandledCRUD` class** - A base class for CRUD operations with standardized error handling.
2. **Error handling decorator** - A decorator for API endpoints that converts CRUD errors to HTTP exceptions.
3. **Provider functions** - Factory functions for creating error-handled CRUD objects with fastapi-injectable.

## Simplified Approach

This implementation simplifies the error handling in several ways:

1. **Focused scope** - It only implements the core CRUD operations (get, create, update, delete, get_multi).
2. **Direct integration with fastapi-injectable** - It uses fastapi-injectable's dependency injection system directly.
3. **Factory pattern** - It uses a factory function to create CRUD objects for different models.
4. **Clean separation of concerns** - Error handling, CRUD operations, and API endpoint behaviors are clearly separated.

## Usage

### Creating a CRUD Object

```python
from fastapi_injectable import Inject, injectable
from local_newsifier.crud.simple_error_handled_crud import ErrorHandledCRUD
from local_newsifier.di.crud_providers import get_error_handled_crud_factory
from local_newsifier.models.article import Article

@injectable
def get_article_crud(crud_factory=Inject(get_error_handled_crud_factory)):
    return crud_factory(Article)
```

### Using in an API Endpoint

```python
from fastapi import APIRouter, Depends, Path
from fastapi_injectable import Inject
from sqlmodel import Session

from local_newsifier.api.dependencies import get_session
from local_newsifier.crud.simple_error_handling import handle_crud_errors

@router.get("/{article_id}")
@handle_crud_errors
async def get_article(
    article_id: int = Path(...),
    db: Session = Depends(get_session),
    article_crud: get_article_crud = Inject(get_article_crud)
):
    return article_crud.get(db, article_id)
```

### Error Handling

The `handle_crud_errors` decorator will catch any CRUD errors and convert them to appropriate HTTP exceptions with standardized error responses:

- `EntityNotFoundError` -> 404 Not Found
- `DuplicateEntityError` -> 409 Conflict
- `ValidationError` -> 422 Unprocessable Entity
- `DatabaseConnectionError` -> 503 Service Unavailable
- `CRUDError` -> 500 Internal Server Error

## Benefits

1. **Simplicity** - Easy to understand and maintain
2. **Standardized error handling** - Consistent error responses across the application
3. **Type safety** - Full type annotation support
4. **Compatible with fastapi-injectable** - Works well with the new DI system
5. **Extensible** - Easy to add new CRUD operations or error types

## Example Implementation

- **Simple ErrorHandledCRUD**: `src/local_newsifier/crud/simple_error_handled_crud.py`
- **Error Handling for API Endpoints**: `src/local_newsifier/crud/simple_error_handling.py`
- **Provider Functions**: `src/local_newsifier/di/crud_providers.py`
- **Example API Router**: `src/local_newsifier/api/routers/simple_articles.py`
- **Tests**: `tests/crud/test_simple_error_handled_crud.py`

## How to Extend

To extend this implementation for a specific model:

1. Create a new CRUD class that inherits from `ErrorHandledCRUD`
2. Add model-specific methods with the `@handle_crud_error` decorator
3. Create a provider function for the new CRUD class
4. Use the CRUD class in your API endpoints with the `@handle_crud_errors` decorator

```python
class ArticleCRUD(ErrorHandledCRUD):
    @handle_crud_error
    def get_by_url(self, db: Session, *, url: str) -> Article:
        statement = select(Article).where(Article.url == url)
        result = db.exec(statement).first()
        
        if result is None:
            raise EntityNotFoundError(
                f"Article with URL '{url}' not found",
                context={"url": url, "model": self.model.__name__},
            )
        
        return result

@injectable(use_cache=True)
def get_article_crud():
    return ArticleCRUD(Article)
```
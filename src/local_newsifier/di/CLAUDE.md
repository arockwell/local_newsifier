# DI (Dependency Injection) Module

This module contains the fastapi-injectable configuration and provider functions for Local Newsifier.

## Migration Context

Local Newsifier has completed the transition from a custom DIContainer to fastapi-injectable. fastapi-injectable is now the sole dependency injection system.

## Key Components

### Provider Functions

These functions define how dependencies are created and their lifecycle:

```python
@injectable(use_cache=False)
def get_entity_crud():
    """Provide the entity CRUD component."""
    from local_newsifier.crud.entity import entity
    return entity

@injectable(use_cache=False)
def get_session() -> Generator[Session, None, None]:
    """Provide a database session."""
    from local_newsifier.database.engine import get_session as get_db_session

    session = next(get_db_session())
    try:
        yield session
    finally:
        session.close()
```

### Cache Management

The fastapi-injectable framework uses the `use_cache` parameter to control instance reuse:

- `use_cache=False` (Project Standard):
  - **Used for ALL providers in Local Newsifier**
  - Creates a fresh instance every time the dependency is injected
  - Prevents state leakage between operations
  - Required for components that interact with databases or maintain state
  - Examples: CRUD components, services, tools, parsers, database sessions

- `use_cache=True` (Not Used):
  - Would reuse the same instance across injections
  - Could be used for purely functional utilities with no state
  - Currently not used in the project to maintain consistency

The project has standardized on `use_cache=False` for all providers to ensure safety
and prevent subtle bugs from shared state.

## Usage Patterns

### Injecting Dependencies

Use the `@injectable` decorator and `Annotated` with `Depends()`:

```python
@injectable(use_cache=False)
def get_entity_service(
    entity_crud: Annotated["CRUDEntity", Depends(get_entity_crud)],
    canonical_entity_crud: Annotated["CRUDCanonicalEntity", Depends(get_canonical_entity_crud)],
    session: Annotated[Session, Depends(get_session)]
):
    """Provide the entity service.

    Uses use_cache=False to create new instances for each injection,
    preventing state leakage between operations.
    """
    from local_newsifier.services.entity_service import EntityService

    return EntityService(
        entity_crud=entity_crud,
        canonical_entity_crud=canonical_entity_crud,
        session_factory=lambda: session
    )
```

### FastAPI Endpoint Usage

In endpoints, use `Depends()` to inject services:

```python
@app.get("/entities/{entity_id}")
def get_entity(
    entity_id: int,
    entity_service: Annotated[EntityService, Depends()]
):
    return entity_service.get_entity(entity_id)
```

## Testing

For testing injectable components:

```python
# In test file
def test_entity_service(patch_injectable_dependencies):
    # Get mocks from fixture
    mocks = patch_injectable_dependencies

    # Create service with mocked dependencies
    service = EntityService(
        entity_crud=mocks["entity_crud"],
        session=mocks["session"]
    )

    # Test logic
    result = service.get_entity(1)
    assert result is not None
```

## Async Providers

The `async_providers.py` module provides async versions of key dependencies:

```python
async def get_async_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get an async database session.

    Yields:
        AsyncSession: Async database session
    """
    async for session in get_async_session():
        yield session
```

### Using Async Providers in Endpoints

```python
from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from local_newsifier.di.async_providers import get_async_db_session

@router.post("/webhook")
async def handle_webhook(
    data: WebhookData,
    session: Annotated[AsyncSession, Depends(get_async_db_session)]
):
    # Use async session for database operations
    service = ApifyWebhookServiceAsync(session=session)
    await service.process_webhook(data)
```

### Async Service Providers

While async services can be created directly in endpoints, you can also define providers:

```python
@injectable(use_cache=False)
async def get_async_webhook_service(
    session: Annotated[AsyncSession, Depends(get_async_db_session)]
):
    """Provide async webhook service."""
    from local_newsifier.services.apify_webhook_service_async import ApifyWebhookServiceAsync

    return ApifyWebhookServiceAsync(session=session)
```

## Migration Notes

- All components now use fastapi-injectable directly
- The legacy adapter layer has been removed
- Project standardized on `use_cache=False` for all providers
- Async providers available for async endpoints and operations
- See `docs/fastapi_injectable.md` for more provider examples

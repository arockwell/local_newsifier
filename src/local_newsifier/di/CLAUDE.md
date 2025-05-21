# DI (Dependency Injection) Module

This module contains the fastapi-injectable configuration and provider functions for Local Newsifier.

## Migration Context

Local Newsifier has completed the transition from a custom DIContainer to fastapi-injectable. fastapi-injectable is now the sole dependency injection system.

## Key Components

### Provider Functions

These functions define how dependencies are created and their lifecycle:

```python
@injectable(scope=Scope.SINGLETON)
def get_entity_crud():
    """Provide the entity CRUD component."""
    from local_newsifier.crud.entity import entity
    return entity

@injectable(scope=Scope.REQUEST)
def get_session() -> Session:
    """Provide a database session."""
    from local_newsifier.database.engine import get_session as get_db_session
    return next(get_db_session())
```

### Scope Management

fastapi-injectable uses three scopes with the following guidelines for Local Newsifier:

- `Scope.SINGLETON`: 
  - Use ONLY for completely stateless and thread-safe components
  - Examples: Configuration providers, constants, pure utility functions
  - Use with extreme caution to avoid shared state issues
  - Never use for components that interact with database

- `Scope.TRANSIENT`: 
  - **Default choice** for almost all components
  - Creates a fresh instance every time the dependency is injected
  - Required for all components that interact with database
  - Examples: CRUD components, entity services, analysis services, processing tools
  
- `Scope.REQUEST`: 
  - Used for request-scoped resources in HTTP context
  - Example: Database sessions in FastAPI endpoints

Always prefer TRANSIENT over SINGLETON when in doubt, particularly for any component
that interacts with databases or maintains internal state.

## Usage Patterns

### Injecting Dependencies

Use the `@injectable` decorator with scope and `Annotated` with `Depends()`:

```python
@injectable(scope=Scope.TRANSIENT)  # Explicitly use TRANSIENT scope for safety
class EntityService:
    """Entity service with injected dependencies.
    
    Uses TRANSIENT scope to ensure a fresh instance for each usage,
    preventing state leakage between operations.
    """
    def __init__(
        self,
        entity_crud: Annotated[EntityCRUD, Depends(get_entity_crud)],
        session: Annotated[Session, Depends(get_session)]
    ):
        self.entity_crud = entity_crud
        self.session = session
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

## Migration Notes

- All components now use fastapi-injectable directly
- The legacy adapter layer has been removed
- See `docs/fastapi_injectable.md` for provider examples

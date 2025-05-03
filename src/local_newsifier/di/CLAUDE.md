# DI (Dependency Injection) Module

This module contains the fastapi-injectable configuration and provider functions for Local Newsifier.

## Migration Context

The project is transitioning from a custom DIContainer to fastapi-injectable. During this migration, both systems will coexist to allow for incremental changes.

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

fastapi-injectable uses three scopes:
- `Scope.SINGLETON`: One instance shared across the application
- `Scope.TRANSIENT`: New instance created on each injection
- `Scope.REQUEST`: Instance is scoped to the current request

## Usage Patterns

### Injecting Dependencies

Use the `@injectable` decorator and `Annotated` with `Depends()`:

```python
@injectable
class EntityService:
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

- New components should use fastapi-injectable directly
- Existing components will be gradually migrated
- Use the adapter layer when interacting with legacy DIContainer components
- See `docs/fastapi_injectable.md` for the full migration guide
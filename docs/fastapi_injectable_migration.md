# FastAPI-Injectable Migration Plan

## Research and Analysis

### Initial Findings

1. **Dependency Conflict**:
   - Local Newsifier uses FastAPI 0.110.0
   - fastapi-injectable requires FastAPI >=0.112.4
   - This will require updating the FastAPI version

2. **Current DI System**:
   - Custom `DIContainer` in `src/local_newsifier/di_container.py`
   - Container singleton in `src/local_newsifier/container.py`
   - FastAPI dependencies in `src/local_newsifier/api/dependencies.py`
   - Services registered with factory methods

3. **API Integration**:
   - Current endpoints use `Depends(get_session)` and similar dependency functions
   - Session management is handled via a session factory from the container
   - Services are retrieved from the container in dependency functions

### About fastapi-injectable

fastapi-injectable is a dependency injection library for FastAPI that:

- Uses decorators to mark injectable components
- Provides instance reuse control (with `use_cache` parameter)
- Supports auto-discovery of injectable components
- Integrates directly with FastAPI's dependency system
- Handles circular dependencies

### Key Differences

| Feature | Current DIContainer | fastapi-injectable |
|---------|---------------------|-------------------|
| Registration | Explicit registration with container.register() | Decorator-based (@injectable) |
| Resolution | container.get("service_name") | Direct injection via type hints |
| Instance Reuse | Controlled by custom scope settings | Controlled by use_cache parameter |
| Integration | Manual integration with FastAPI dependencies | Direct FastAPI integration |
| Discovery | Manual registration | Auto-discovery with scanning |

## Migration Strategy

### 1. Update Dependencies

- Update FastAPI to required version (>=0.112.4)
- Add fastapi-injectable
- Test core application functionality after updates

### 2. Create Adapter Layer

- Create an adapter pattern to bridge between systems during migration
- Allow both DI systems to coexist during transition
- Gradually migrate components from DIContainer to fastapi-injectable

### 3. Injectable Service Pattern

Convert services to use the injectable pattern:

```python
from fastapi_injectable import injectable

@injectable(use_cache=False)  # Create new instance for each injection
class EntityService:
    def __init__(self, entity_crud: EntityCRUD, session_factory: SessionFactory):
        self.entity_crud = entity_crud
        self.session_factory = session_factory
```

### 4. Update API Dependencies

Replace current dependency functions with injectable versions:

```python
# Current approach
def get_article_service() -> ArticleService:
    return container.get("article_service")

# New approach with fastapi-injectable
from typing import Annotated
from fastapi import Depends
from fastapi_injectable import injectable

@injectable(use_cache=False)  # Stateful service, needs new instances
def get_article_service(entity_service: Annotated[EntityService, Depends()]):
    return ArticleService(entity_service=entity_service)
```

### 5. Session Management Updates

Update session management to use fastapi-injectable with `use_cache=False`:

```python
@injectable(use_cache=False)  # New session for each request
def get_session() -> Generator[Session, None, None]:
    """Provide a database session."""
    from local_newsifier.database.engine import get_session as get_db_session
    
    session = next(get_db_session())
    try:
        yield session
    finally:
        session.close()
```

### 6. CRUD Modules Conversion

Convert CRUD modules to use injectable pattern:

```python
@injectable(use_cache=False)  # Database interactions require fresh instances
class EntityCRUD:
    def get(self, session: Session, id: int):
        # Implementation
```

### 7. Container Initialization

Update application startup to use fastapi-injectable initialization:

```python
from fastapi_injectable import register_app
from local_newsifier.fastapi_injectable_adapter import migrate_container_services

# Register app with fastapi-injectable
await register_app(app)

# Register all services in DIContainer with fastapi-injectable
await migrate_container_services(app)
```

## Compatibility Challenges

- Current code references container directly in some places
- State-based flows may need special handling
- CLI commands use container directly
- Celery tasks use container for service resolution

## Testing Strategy

- Create tests for both DI systems working together
- Verify services can be resolved through both mechanisms
- Test FastAPI endpoints with new DI system
- Ensure CLI commands continue working during transition
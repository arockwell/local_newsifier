# FastAPI Injectable Guide

Local Newsifier now uses **fastapi-injectable** exclusively. For a high-level overview of the architecture, see the [DI Architecture Guide](di_architecture.md).
>
> **NEW**: For comprehensive examples and practical patterns, check out the new [Injectable Patterns Guide](injectable_patterns.md).
>

## Overview

Local Newsifier uses **fastapi-injectable** as its dependency injection framework. This guide provides information on provider conventions, implementation details, and best practices.

## Background and Motivation

Local Newsifier previously used a custom DI container implementation that had some limitations:

1. **Inconsistent Patterns**: Different approaches to accessing dependencies across the codebase
2. **Testing Complexity**: Each test required custom mocking strategies
3. **Manual Resolution**: Flow and service classes had to manually resolve dependencies
4. **Direct Container References**: Many components referenced the container directly

The migration to fastapi-injectable provides these benefits:

1. **Simplified Dependencies**: Consistent `Depends()` pattern for all components
2. **Better Testing**: Easier to override dependencies for testing
3. **Type Safety**: Better type hints with `Annotated` types
4. **Less Boilerplate**: Automatic dependency resolution with decorators
5. **Framework Alignment**: Better integration with FastAPI's dependency system

## Migration Summary (Completed)

The project previously used a custom container but has fully migrated to fastapi-injectable.
All components rely on provider functions and the adapter has been removed.

## Implementation Components

### 1. Core DI Configuration

All provider functions live in
`src/local_newsifier/di/providers.py`. Dependency injection is
initialized when creating the FastAPI application:

```python
from fastapi import FastAPI
from fastapi_injectable import init_injection_dependency

app = FastAPI()
init_injection_dependency(app)
```

### 2. Provider Functions

Provider functions in `di/providers.py` expose dependencies to be injected:

```python
from typing import Annotated, Generator
from fastapi import Depends
from fastapi_injectable import injectable
from sqlmodel import Session

@injectable(use_cache=False)  # Create a new session for each injection
def get_session() -> Generator[Session, None, None]:
    """Provide a database session."""
    from local_newsifier.database.engine import get_session as get_db_session

    session = next(get_db_session())
    try:
        yield session
    finally:
        session.close()

@injectable(use_cache=False)  # Create new instances for data access components
def get_entity_crud():
    """Provide the entity CRUD component.

    Uses use_cache=False to create new instances for each injection, as CRUD
    components interact with the database and should not share state.
    """
    from local_newsifier.crud.entity import entity
    return entity
```

### 3. Service Migration Pattern

Services can be migrated using the `@injectable` decorator:

```python
@injectable
class InjectableEntityService:
    def __init__(
        self,
        entity_crud: Annotated[EntityCRUD, Depends(get_entity_crud)],
        session: Annotated[Session, Depends(get_session)],
    ):
        self.entity_crud = entity_crud
        self.session = session
```

### 5. Testing Framework

Test utilities in `conftest_injectable.py` provide fixtures for testing with fastapi-injectable.

## Step-by-Step Migration Guide

### Step 1: Install Dependencies

```toml
[tool.poetry.dependencies]
python = ">=3.10,<3.13"
fastapi-injectable = "^0.7.0"
```

### Step 2: Configure FastAPI Application

```python
from fastapi import FastAPI
from fastapi_injectable import init_injection_dependency

app = FastAPI()
init_injection_dependency(app)
```

### Step 3: Define Provider Functions

Create provider functions for commonly used dependencies:

```python
# For simple utility functions with no state, caching might be appropriate
@injectable(use_cache=True)  # Cache instance for performance
def get_config_provider():
    """Provide application configuration."""
    from local_newsifier.config.settings import get_settings
    return get_settings()

# For CRUD components that interact with database, no caching is required
@injectable(use_cache=False)  # Create new instance each time
def get_article_crud():
    """Provide the article CRUD component."""
    from local_newsifier.crud.article import article
    return article

# For database sessions, never cache them
@injectable(use_cache=False)  # Create a new session each time
def get_session() -> Generator[Session, None, None]:
    """Provide a database session."""
    from local_newsifier.database.engine import get_session as get_db_session

    session = next(get_db_session())
    try:
        yield session
    finally:
        session.close()

# For services with state or database interaction, disable caching
@injectable(use_cache=False)  # Create a new instance each time
def get_article_service(
    article_crud: Annotated[ArticleCRUD, Depends(get_article_crud)],
    session: Annotated[Session, Depends(get_session)]
):
    """Provide the article service."""
    from local_newsifier.services.article_service import ArticleService

    return ArticleService(
        article_crud=article_crud,
        session_factory=lambda: session
    )
```

### Step 4: Migrate Services

Convert services to use the `@injectable` decorator with appropriate scope:

```python
@injectable(use_cache=False)  # Prevent caching to ensure fresh instances
class InjectableEntityService:
    """Injectable entity service with explicitly defined dependencies.

    Uses use_cache=False to create new instances for each injection,
    preventing state leakage between operations.
    """
    def __init__(
        self,
        entity_crud: Annotated[EntityCRUD, Depends(get_entity_crud)],
        canonical_entity_crud: Annotated[CanonicalEntityCRUD, Depends(get_canonical_entity_crud)],
        session: Annotated[Session, Depends(get_session)],
    ):
        self.entity_crud = entity_crud
        self.canonical_entity_crud = canonical_entity_crud
        self.session = session
```

### Step 5: Update API Endpoints

Use injectable dependencies in FastAPI endpoints:

```python
@app.get("/entities/{entity_id}")
async def get_entity(
    entity_id: int,
    entity_service: Annotated[InjectableEntityService, Depends()]
):
    return entity_service.get_entity(entity_id)
```

### Step 6: Set Up Testing

Create test fixtures for injectable components:

```python
@pytest.fixture
def patch_injectable_dependencies(monkeypatch):
    """Patch injectable dependencies for non-API tests."""
    mock_entity_crud = Mock()
    monkeypatch.setattr("local_newsifier.di.providers.get_entity_crud", lambda: mock_entity_crud)

    return {
        "entity_crud": mock_entity_crud,
    }
```

## Usage Examples

### Service Definition

```python
@injectable
class InjectableEntityService:
    def __init__(
        self,
        entity_crud: Annotated[EntityCRUD, Depends(get_entity_crud)],
        session: Annotated[Session, Depends(get_session)],
    ):
        self.entity_crud = entity_crud
        self.session = session
```

### Method Injection

```python
@injectable
def process_entity(
    self,
    entity_id: int,
    extra_service: Annotated[ExtraService, Depends(get_extra_service)]
):
    # Implementation using injected dependency
    return extra_service.process(entity_id)
```

### Testing

```python
def test_service(patch_injectable_dependencies):
    mocks = patch_injectable_dependencies
    service = InjectableEntityService(
        entity_crud=mocks["entity_crud"],
        session=mocks["session"]
    )
    result = service.process_article_entities(1, "content", "title", datetime.now())
    assert len(result) == 1
```

## Best Practices

### Service Definition
- Always use `@injectable` decorator for classes that will be injected
- Use `Annotated[Type, Depends()]` for dependency parameters
- Avoid circular dependencies by using provider functions
- Keep provider functions in a central location

### Instance Reuse Management

fastapi-injectable v0.7.0 doesn't have a Scope enum or scope parameter, but it does control
instance reuse with the `use_cache` parameter:

- **use_cache=True** (default in fastapi-injectable):
  - Reuses the same instance for identical dependency requests
  - Only safe for completely stateless and thread-safe components
  - Can lead to subtle concurrency issues and state leakage

- **use_cache=False**:
  - Creates a fresh instance for each dependency injection
  - Prevents shared state and potential leakage between operations
  - More predictable behavior in asynchronous environments

**Our project decision**: We use **`use_cache=False` for ALL components** for consistency and safety.

This decision:
- Eliminates an entire class of potential bugs related to shared state
- Makes the system more predictable in concurrent environments
- Simplifies the development model (no need to decide which components are truly stateless)
- Prevents unexpected side effects when modifying components
- Provides isolation between different parts of the application

While there might be a minor performance cost to creating fresh instances, the improved
reliability and maintainability outweigh this concern for our application.

### Testing
- Create mock fixtures for common dependencies
- Use `monkeypatch` to override provider functions in tests
- Consider creating a custom fixture to patch multiple dependencies at once
- Test both with direct instantiation and through the DI system


## Troubleshooting

### Common Issues

#### Circular Dependencies
**Problem**: Two services depend on each other.
**Solution**: Use provider functions or lazy loading.

```python
@injectable
def get_service_a(
    # Use a lambda to delay import/resolution
    service_b: Annotated[ServiceB, Depends(lambda: get_service_b())]
):
    return ServiceA(service_b)
```

#### Session Management
**Problem**: Database session closes before usage.
**Solution**: Use request-scoped session management.

```python
@injectable(use_cache=False)  # Always create new session
def get_session() -> Generator[Session, None, None]:
    session = next(get_db_session())
    try:
        yield session
    finally:
        session.close()
```

#### Testing Errors
**Problem**: Tests fail with "No provider found for dependency".
**Solution**: Patch provider functions for tests.

```python
@pytest.fixture
def patch_injectable_dependencies(monkeypatch):
    mock_service = Mock()
    monkeypatch.setattr("local_newsifier.di.providers.get_service", lambda: mock_service)
    return {"service": mock_service}
```

## References

- [FastAPI-Injectable Documentation](https://fastapi-injectable.readme.io/)
- [FastAPI Dependency Injection](https://fastapi.tiangolo.com/tutorial/dependencies/)
- [Python Type Annotations](https://docs.python.org/3/library/typing.html)

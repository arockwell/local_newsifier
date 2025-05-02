# Migration Guide: Custom DI Container to fastapi-injectable

This guide documents the process of migrating from Local Newsifier's custom DI container to fastapi-injectable.

## Table of Contents

1. [Background](#background)
2. [Migration Phases](#migration-phases)
3. [Step 1: Project Setup](#step-1-project-setup)
4. [Step 2: Defining Providers](#step-2-defining-providers)
5. [Step 3: Migrating Services](#step-3-migrating-services)
6. [Step 4: Testing with Injectable](#step-4-testing-with-injectable)
7. [Best Practices](#best-practices)
8. [Common Issues](#common-issues)

## Background

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

## Migration Phases

The migration follows a phased approach:

1. **Foundation (Current Phase)**:
   - Set up basic infrastructure
   - Create provider functions for core dependencies
   - Configure testing utilities

2. **Gradual Migration**:
   - Migrate individual services incrementally
   - Update tests to use the new pattern
   - Keep both systems working during transition

3. **Complete Migration**:
   - Fully migrate all components
   - Remove the legacy DI container
   - Update documentation

## Step 1: Project Setup

### Installing Dependencies

fastapi-injectable is already included in the project dependencies:

```toml
[tool.poetry.dependencies]
python = ">=3.10,<3.13"
# Other dependencies...
fastapi-injectable = "^0.7.0"
```

### DI Configuration Module

We've created a dedicated module for DI configuration:

```python
# src/local_newsifier/config/di.py
from fastapi_injectable import configure_logging, setup_graceful_shutdown

# Configure logging
configure_logging(level=logging.INFO)

# Enable graceful shutdown
setup_graceful_shutdown()

# Scope converter function
def scope_converter(scope: str) -> Scope:
    """Convert DIContainer scope to fastapi-injectable scope."""
    scope_map = {
        DIContainerScope.SINGLETON.value: Scope.SINGLETON,
        DIContainerScope.TRANSIENT.value: Scope.TRANSIENT,
        DIContainerScope.SCOPED.value: Scope.REQUEST,  # Map scoped to request
    }
    return scope_map.get(scope.lower(), Scope.SINGLETON)
```

## Step 2: Defining Providers

Provider functions expose dependencies to be used by components:

```python
# src/local_newsifier/di/providers.py
from typing import Annotated, Generator
from fastapi import Depends
from fastapi_injectable import injectable
from sqlmodel import Session

@injectable(scope=Scope.REQUEST)
def get_session() -> Generator[Session, None, None]:
    """Provide a database session."""
    from local_newsifier.database.engine import get_session as get_db_session
    
    session = next(get_db_session())
    try:
        yield session
    finally:
        session.close()

@injectable(scope=Scope.SINGLETON)
def get_article_crud():
    """Provide the article CRUD component."""
    from local_newsifier.crud.article import article
    return article

# Service providers
@injectable(scope=Scope.SINGLETON)
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

## Step 3: Migrating Services

Services can be migrated individually using the `@injectable` decorator:

```python
# src/local_newsifier/services/injectable_entity_service.py
from typing import Annotated
from fastapi import Depends
from fastapi_injectable import injectable
from sqlmodel import Session

@injectable
class InjectableEntityService:
    """Entity service using fastapi-injectable."""
    
    def __init__(
        self,
        entity_crud: Annotated[EntityCRUD, Depends(get_entity_crud)],
        canonical_entity_crud: Annotated[CanonicalEntityCRUD, Depends(get_canonical_entity_crud)],
        session: Annotated[Session, Depends(get_session)],
    ):
        """Initialize with injected dependencies."""
        self.entity_crud = entity_crud
        self.canonical_entity_crud = canonical_entity_crud
        self.session = session
        
    @injectable
    def process_entity(self, entity_id: int):
        """Process an entity."""
        # Implementation here
```

## Step 4: Testing with Injectable

Testing components that use fastapi-injectable requires overriding the dependencies:

```python
# tests/conftest_injectable.py
import pytest
from unittest.mock import Mock

@pytest.fixture
def mock_entity_crud():
    """Provide a mock entity CRUD component."""
    mock = Mock()
    mock.create.return_value = Mock(id=1, text="Test Entity", entity_type="PERSON")
    return mock

@pytest.fixture
def patch_injectable_dependencies(monkeypatch):
    """Patch injectable dependencies for non-API tests."""
    # Create mocks
    mock_entity_crud = Mock()
    
    # Patch the providers
    monkeypatch.setattr("local_newsifier.di.providers.get_entity_crud", lambda: mock_entity_crud)
    
    # Return mocks for use in tests
    return {"entity_crud": mock_entity_crud}

# In your test:
def test_service(patch_injectable_dependencies):
    mocks = patch_injectable_dependencies
    service = InjectableEntityService(
        entity_crud=mocks["entity_crud"],
        # Other dependencies...
    )
    # Test implementation
```

## Best Practices

### Type Annotations

Always use specific types instead of `Any`:

```python
# Bad
entity_crud: Annotated[Any, Depends(get_entity_crud)]

# Good
entity_crud: Annotated[EntityCRUD, Depends(get_entity_crud)]
```

### Method Injection

Methods can also be decorated to inject dependencies:

```python
@injectable
def process_article(
    self,
    article_id: int,
    article_service: Annotated[ArticleService, Depends(get_article_service)]
):
    """Process with injected dependencies."""
    return article_service.get_article(article_id)
```

### Circular Dependencies

Handle circular imports with string type annotations:

```python
# When you have circular imports
entity_service: Annotated["EntityService", Depends(get_entity_service)]

# With TYPE_CHECKING
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from local_newsifier.services.entity_service import EntityService
```

### Scopes

Match dependency scopes to their usage patterns:

- `Scope.SINGLETON`: Use for stateless components (most services, tools)
- `Scope.TRANSIENT`: Use for components that should be recreated on each use
- `Scope.REQUEST`: Use for request-scoped resources (database sessions)

## Common Issues

### Multiple Session Handling

Be careful with database sessions to prevent "Session is not bound" errors:

```python
# Issue: Using session across boundaries
@injectable
def process_with_session(self, article_id: int):
    article = self.article_crud.get(self.session, id=article_id)
    # Don't return the article object directly if it will be used after
    # this function returns! Instead, return IDs or processed data
    return {"id": article.id, "title": article.title}  # Safe
```

### Dependency Override Cleanup

Always clean up dependency overrides in tests:

```python
@pytest.fixture
def test_client_with_mocks():
    app = FastAPI()
    app.dependency_overrides = {...}  # Set overrides
    client = TestClient(app)
    yield client
    app.dependency_overrides = {}  # Clean up
```

### Type Checking

Use `TYPE_CHECKING` for circular imports:

```python
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from local_newsifier.services.entity_service import EntityService
```
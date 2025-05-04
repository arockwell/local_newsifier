# Migrating from DIContainer to fastapi-injectable

## Overview

This document outlines the plan for fully migrating from our custom DIContainer to fastapi-injectable. The goal is to eliminate the DIContainer system completely and standardize all dependency injection through fastapi-injectable.

## Current Status

- Both DI systems are running in parallel
- An adapter layer exists in `fastapi_injectable_adapter.py` to bridge the systems
- All flow classes now have both base classes (for testing) and injectable versions
- All providers have been implemented with `use_cache=False` for consistency
- Circular dependencies are a challenge in the current architecture

## Migration Strategy

### 1. Eliminate Direct DIContainer Usage

#### Services with Container Injection

- **ArticleService** and **RSSFeedService** directly inject the container for lazy loading
- Replace these with proper dependency injection through constructor parameters
- Use forward references and runtime imports to solve circular dependencies

```python
# Before
class ArticleService:
    def __init__(self, container):
        self.container = container
        
    def _get_entity_service(self):
        return self.container.get("entity_service")

# After
@injectable(use_cache=False)
class ArticleService:
    def __init__(
        self, 
        article_crud: Annotated[Any, Depends(get_article_crud)],
        # Forward reference for circular dependency
        entity_service_factory: Annotated[Callable[[], "EntityService"], Depends(get_entity_service_factory)]
    ):
        self.article_crud = article_crud
        self._entity_service_factory = entity_service_factory
        
    def _get_entity_service(self):
        return self._entity_service_factory()
```

#### Provider Strategies for Circular Dependencies

Create factory providers to resolve circular dependencies:

```python
@injectable(use_cache=False)
def get_entity_service_factory() -> Callable[[], "EntityService"]:
    """Provide a factory for lazy loading EntityService to break circular dependencies."""
    def factory():
        # Runtime import prevents circular imports
        from local_newsifier.di.providers import get_entity_service
        return get_entity_service()
    return factory
```

### 2. Update Service Classes for Direct Dependency Injection

Modify all service classes to:
1. Remove DIContainer dependency
2. Use constructor injection with `@injectable` decorator
3. Explicitly receive all dependencies via constructor
4. Use factory patterns for circular dependencies

### 3. Implement Lifecycle Management

Create a lifespan middleware for FastAPI that manages lifecycle events:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize resources
    from local_newsifier.di.lifecycle import initialize_resources
    await initialize_resources()
    
    yield
    
    # Shutdown: Cleanup resources
    from local_newsifier.di.lifecycle import cleanup_resources
    await cleanup_resources()

# Usage in FastAPI app
app = FastAPI(lifespan=lifespan)
```

Implement a lifecycle registry system:

```python
# In di/lifecycle.py
_cleanup_handlers = []

def register_cleanup(handler: Callable[[], None]):
    """Register a cleanup handler to be called on app shutdown."""
    _cleanup_handlers.append(handler)

async def cleanup_resources():
    """Call all registered cleanup handlers."""
    for handler in _cleanup_handlers:
        try:
            if inspect.iscoroutinefunction(handler):
                await handler()
            else:
                handler()
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
```

### 4. Unified Initialization Strategy

Create a central initialization function in `di/init.py`:

```python
def init_injectable(app: FastAPI = None):
    """Initialize all injectable providers with default parameters.
    
    This provides a centralized place to configure all providers with 
    default parameters and register lifecycle handlers.
    
    Args:
        app: Optional FastAPI app to register with
    """
    # Register the app if provided
    if app:
        from fastapi_injectable import register_app
        asyncio.run(register_app(app))
    
    # Configure providers with defaults
    from local_newsifier.di.config import configure_providers
    configure_providers()
    
    # Register lifecycle handlers
    from local_newsifier.di.lifecycle import register_lifecycle_handlers
    register_lifecycle_handlers()
```

### 5. Adapter Removal Strategy

1. Update all imports to use fastapi-injectable directly
2. Replace container access with Depends injection
3. Remove the adapter module

#### Import Updates

```python
# Before
from local_newsifier.container import container

service = container.get("entity_service")

# After
from fastapi_injectable import Depends
from local_newsifier.di.providers import get_entity_service

def my_function(
    entity_service: Annotated[Any, Depends(get_entity_service)]
):
    # Use entity_service directly
```

### 6. Cleanup the Old System

Once all direct DIContainer usage is eliminated:

1. Remove `container.py`
2. Remove `di_container.py`
3. Remove `fastapi_injectable_adapter.py`
4. Update documentation and tests

## Testing Strategy

1. Create mock providers for testing:

```python
# In tests/conftest.py
@pytest.fixture
def mock_entity_service():
    """Provide a mock entity service for testing."""
    from unittest.mock import MagicMock
    return MagicMock()

@pytest.fixture(autouse=True)
def patch_get_entity_service(monkeypatch, mock_entity_service):
    """Patch the entity service provider to return a mock."""
    from local_newsifier.di.providers import get_entity_service
    monkeypatch.setattr(
        "local_newsifier.di.providers.get_entity_service", 
        lambda: mock_entity_service
    )
```

2. Use the base classes for testing without DI:

```python
# In tests/flows/test_entity_tracking_flow.py
from local_newsifier.flows.entity_tracking_flow import EntityTrackingFlowBase

def test_entity_tracking_flow():
    flow = EntityTrackingFlowBase(
        entity_service=mock_entity_service,
        entity_tracker=mock_entity_tracker
    )
    # Test the flow
```

## Migration Steps

1. Create the centralized initialization system in `di/init.py`
2. Update services to use constructor injection instead of container
3. Implement the lifecycle management system
4. Update imports to use fastapi-injectable directly
5. Test thoroughly at each step
6. Remove the adapter and old DIContainer code
7. Update documentation

## Special Cases

### Session Management

Replace the session_factory pattern with direct session injection:

```python
# Before (used throughout codebase)
with self.session_factory() as session:
    # Use session

# After with fastapi-injectable
@injectable(use_cache=False)
def get_db_session():
    """Provide a database session."""
    from local_newsifier.database.engine import get_session as get_db_session
    session = next(get_db_session())
    try:
        yield session
    finally:
        session.close()

# In services
def some_method(self, session: Annotated[Session, Depends(get_db_session)]):
    # Use session directly
```

### Service Factory With Parameters

Replace parameterized factories with multiple specialized providers:

```python
# Before
web_scraper = container.get("web_scraper_tool", user_agent="Custom UA")

# After
@injectable(use_cache=False)
def get_web_scraper_with_custom_ua():
    from local_newsifier.tools.web_scraper import WebScraperTool
    return WebScraperTool(user_agent="Custom UA")
```

## Timeline

1. **Phase 1 (Current PR)**: Complete flow updates, implement providers
2. **Phase 2**: Implement lifecycle management and central initialization
3. **Phase 3**: Update services to use constructor injection
4. **Phase 4**: Remove container references and update imports
5. **Phase 5**: Remove adapter code and DIContainer
6. **Phase 6**: Update documentation and final testing

## Risks and Mitigations

- **Risk**: Breaking changes to API endpoints using container
  - **Mitigation**: Incremental updates with thorough testing

- **Risk**: Missing lifecycle handlers
  - **Mitigation**: Audit all cleanup handlers and ensure they're registered

- **Risk**: Circular dependencies becoming unresolvable
  - **Mitigation**: Factory pattern to defer initialization

- **Risk**: Session management issues
  - **Mitigation**: Standardize on a single session management pattern

## Conclusion

This migration plan provides a comprehensive approach to fully transitioning from our custom DIContainer to fastapi-injectable. By following this strategy, we will have a more standardized, maintainable dependency injection system that leverages the capabilities of FastAPI's built-in dependency injection mechanisms.
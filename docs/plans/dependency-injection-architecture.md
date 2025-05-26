# Dependency Injection Architecture Knowledge Base

## Overview
This document consolidates all knowledge about the dependency injection migration from custom DIContainer to fastapi-injectable, including patterns, anti-patterns, and migration strategies.

## Architecture Evolution

### Legacy System (DIContainer)
The original system used a custom DIContainer with global instance management:
```python
# Legacy pattern - DEPRECATED
container = DIContainer()
container.register(DatabaseService, get_database_service)
service = container.resolve(DatabaseService)
```

### Current System (fastapi-injectable)
The new system uses fastapi-injectable with explicit provider functions:
```python
# Current pattern
@injectable(use_cache=False)
def get_article_service(
    article_crud: Annotated[Any, Depends(get_article_crud)],
    session: Annotated[Session, Depends(get_session)]
):
    return ArticleService(article_crud=article_crud, session_factory=lambda: session)
```

## Core Principles

### 1. No Caching by Default
**Why**: Prevents stale data and session management issues
```python
@injectable(use_cache=False)  # Always use this
```

### 2. Provider Functions Pattern
**Why**: Explicit dependencies, better testability, lazy loading
```python
# Provider function pattern
def get_service_name(
    dependency1: Annotated[Type1, Depends(get_dependency1)],
    dependency2: Annotated[Type2, Depends(get_dependency2)]
) -> ServiceType:
    from local_newsifier.services.service_module import ServiceClass
    return ServiceClass(dependency1, dependency2)
```

### 3. Session Factory Pattern
**Why**: Avoids session lifecycle issues
```python
class Service:
    def __init__(self, session_factory: Callable[[], Session]):
        self.session_factory = session_factory

    def method(self):
        with self.session_factory() as session:
            # Use session
```

## Anti-Patterns to Avoid

### 1. Global Container Instance
**Problem**: Creates hidden dependencies and testing issues
```python
# BAD - Don't do this
container = DIContainer()  # Global instance

# GOOD - Use provider functions
@injectable(use_cache=False)
def get_service(...):
    return Service(...)
```

### 2. Mixed DI Access Patterns
**Problem**: Inconsistent dependency resolution
```python
# BAD - Mixing patterns
service = container.resolve(Service)  # Old way
service = Depends(get_service)  # New way in same codebase

# GOOD - Use only one pattern
service: Annotated[Service, Depends(get_service)]
```

### 3. Circular Dependencies
**Problem**: Import cycles and initialization issues
```python
# BAD - Circular imports
# In service_a.py
from .service_b import ServiceB

# In service_b.py
from .service_a import ServiceA

# GOOD - Use runtime imports in providers
@injectable(use_cache=False)
def get_service_a():
    from .service_b import ServiceB  # Import inside function
    return ServiceA(...)
```

### 4. Long-Lived Sessions
**Problem**: Database connection issues, stale data
```python
# BAD - Storing session
class Service:
    def __init__(self, session: Session):
        self.session = session  # Session stored

# GOOD - Session factory
class Service:
    def __init__(self, session_factory: Callable[[], Session]):
        self.session_factory = session_factory
```

## Migration Strategy

### Phase 1: Identify Dependencies
1. Find all DIContainer usage:
   ```bash
   rg "DIContainer|container\." --type python
   ```
2. Map service dependencies
3. Identify circular dependencies

### Phase 2: Create Provider Functions
1. Create provider module: `di/providers.py`
2. Implement provider for each service:
   ```python
   @injectable(use_cache=False)
   def get_service_name(...) -> ServiceType:
       from local_newsifier.services import Service
       return Service(...)
   ```

### Phase 3: Update Usage Points
1. Replace container.resolve() with Depends()
2. Update FastAPI endpoints:
   ```python
   # Old
   service = container.resolve(Service)

   # New
   service: Annotated[Service, Depends(get_service)]
   ```

### Phase 4: Update Tests
1. Mock provider functions:
   ```python
   @pytest.fixture
   def mock_service():
       return Mock(spec=Service)

   @pytest.fixture
   def mock_get_service(mock_service):
       with patch("module.get_service", return_value=mock_service):
           yield mock_service
   ```

### Phase 5: Remove Legacy Code
1. Delete DIContainer class
2. Remove container registrations
3. Clean up imports

## Common Patterns

### Service with Dependencies
```python
@injectable(use_cache=False)
def get_complex_service(
    crud: Annotated[CRUDBase, Depends(get_crud)],
    analyzer: Annotated[Analyzer, Depends(get_analyzer)],
    session: Annotated[Session, Depends(get_session)]
) -> ComplexService:
    from local_newsifier.services.complex_service import ComplexService
    return ComplexService(
        crud=crud,
        analyzer=analyzer,
        session_factory=lambda: session
    )
```

### CLI Command with Dependencies
```python
@cli.command()
def process(
    ctx: typer.Context,
    service: Annotated[Service, Depends(get_service)]
):
    # Use service
    pass
```

### Testing with Mocked Dependencies
```python
def test_endpoint(client, mock_get_service):
    mock_service = Mock()
    mock_get_service.return_value = mock_service

    response = client.get("/endpoint")
    assert response.status_code == 200
```

## Best Practices

### 1. Explicit Dependencies
Always declare dependencies explicitly in function signatures:
```python
def get_service(
    dep1: Annotated[Type1, Depends(get_dep1)],
    dep2: Annotated[Type2, Depends(get_dep2)]
):
    # NOT: magically getting dependencies from somewhere
```

### 2. Type Annotations
Use proper type hints for better IDE support:
```python
from typing import Annotated
from fastapi import Depends

service: Annotated[ServiceType, Depends(get_service)]
```

### 3. Lazy Imports
Import inside provider functions to avoid circular dependencies:
```python
@injectable(use_cache=False)
def get_service():
    from local_newsifier.services import Service  # Import here
    return Service()
```

### 4. Consistent Naming
Use consistent naming for providers:
- `get_<service_name>` for service providers
- `get_<model>_crud` for CRUD providers
- `get_<tool_name>` for tool providers

### 5. Documentation
Document complex provider functions:
```python
@injectable(use_cache=False)
def get_complex_service(...) -> Service:
    """
    Provides ComplexService with configured dependencies.

    Note: Requires DATABASE_URL to be set.
    """
```

## Troubleshooting

### "Instance is not bound to a Session"
**Cause**: SQLModel object used outside its session
**Fix**: Return IDs instead of objects, refetch in new session

### Circular Import Error
**Cause**: Services importing each other at module level
**Fix**: Use runtime imports in provider functions


### Dependency Not Found
**Cause**: Provider not registered or imported
**Fix**: Ensure provider is in `di/providers.py` and imported

## Future Improvements

### 1. Dependency Graph Visualization
Create tool to visualize dependency relationships:
```python
# Potential implementation
def generate_dependency_graph():
    # Analyze provider functions
    # Generate graph visualization
```

### 2. Automatic Provider Generation
Generate providers from service signatures:
```python
# Potential decorator
@auto_injectable
class Service:
    def __init__(self, dep1: Dep1, dep2: Dep2):
        pass
```

### 3. Validation Layer
Add runtime validation for dependencies:
```python
@injectable(use_cache=False, validate=True)
def get_service(...):
    # Validates dependencies exist
```

### 4. Performance Monitoring
Track dependency resolution performance:
```python
@injectable(use_cache=False, profile=True)
def get_service(...):
    # Logs resolution time
```

## Migration Checklist

- [ ] Identify all DIContainer usage
- [ ] Create provider functions for all services
- [ ] Update FastAPI endpoints to use Depends()
- [ ] Update CLI commands to use providers
- [ ] Update all tests to mock providers
- [ ] Remove DIContainer class
- [ ] Update documentation
- [ ] Verify no circular dependencies
- [ ] Performance test the new system

## References

- [fastapi-injectable documentation](https://github.com/fastapi-injectable/fastapi-injectable)
- [FastAPI Dependency Injection](https://fastapi.tiangolo.com/tutorial/dependencies/)
- Project Issues: #67, #69, #156, #211, #213, #295, #380, #425, #481, #521, #535, #541, #615, #648, #681

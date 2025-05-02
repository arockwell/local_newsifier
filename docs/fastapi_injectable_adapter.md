# FastAPI Injectable Adapter

This document explains how to use the adapter that bridges between our custom DIContainer and fastapi-injectable. The adapter allows for an incremental migration path while maintaining compatibility with existing code.

## Background

The Local Newsifier project is transitioning from a custom DIContainer to use fastapi-injectable for dependency injection. This adapter enables both systems to coexist during migration.

## Components

### 1. Adapter Module (`fastapi_injectable_adapter.py`)

The adapter module provides utilities for:
- Registering DIContainer services with fastapi-injectable
- Converting between scope types
- Adapting decorator patterns

Key functions include:

#### `scope_converter(scope: str) -> Scope`

Converts DIContainer scope strings to fastapi-injectable Scope enum values:

```python
def scope_converter(scope: str) -> Scope:
    """Convert DIContainer scope to fastapi-injectable scope."""
    scope_map = {
        "singleton": Scope.SINGLETON,
        "transient": Scope.TRANSIENT,
        "scoped": Scope.REQUEST  # Map scoped to request in fastapi-injectable
    }
    return scope_map.get(scope.lower(), Scope.SINGLETON)
```

#### `register_with_injectable(service_name: str, service_class: Type[T]) -> None`

Registers a service from DIContainer with fastapi-injectable:

```python
def register_with_injectable(service_name: str, service_class: Type[T]) -> None:
    """Register a service from DIContainer with fastapi-injectable."""
    # Get the service scope from DIContainer
    di_scope = di_container._scopes.get(service_name, "singleton")
    injectable_scope = scope_converter(di_scope)
    
    # Create an injectable factory that gets the service from DIContainer
    @injectable(scope=injectable_scope)
    class ServiceWrapper(Injectable):
        """Wrapper for service from DIContainer."""
        
        def __new__(cls, *args, **kwargs):
            """Create a new instance by getting from DIContainer."""
            return di_container.get(service_name)
```

#### `inject_adapter(func: Callable) -> Callable`

Decorator that adapts between fastapi-injectable's Inject and DIContainer:

```python
def inject_adapter(func: Callable) -> Callable:
    """Decorator to adapt between fastapi-injectable's Inject and DIContainer."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Get type hints from function signature
        hints = get_type_hints(func)
        
        # Look for parameters with Inject dependency
        for param_name, param_type in hints.items():
            # ...logic to resolve dependencies...
            
        return func(*args, **kwargs)
        
    return wrapper
```

#### `migrate_container_services() -> None`

Registers all DIContainer services with fastapi-injectable:

```python
def migrate_container_services() -> None:
    """Register all DIContainer services with fastapi-injectable."""
    # Register services and factories with fastapi-injectable
    for name, service in di_container._services.items():
        if service is not None:
            service_class = service.__class__
            register_with_injectable(name, service_class)
```

### 2. Testing Components

The adapter includes test endpoints and utilities to verify correct operation:

- `scripts/test_fastapi_injectable.py`: Standalone test application
- `src/local_newsifier/api/injectable_test.py`: Injectable test endpoints
- `scripts/test_injectable_adapter.sh`: Test script for verification

## Usage Instructions

### Initializing the Adapter

Add the following to your FastAPI application:

```python
from fastapi_injectable import init_injection_dependency
from local_newsifier.fastapi_injectable_adapter import migrate_container_services

# Create FastAPI app
app = FastAPI()

# Initialize fastapi-injectable
init_injection_dependency(app)

# Register DIContainer services with fastapi-injectable
migrate_container_services()
```

### Using Injectable Services

1. **Define an Injectable Service**:

```python
from typing import Annotated
from fastapi_injectable import Inject, Injectable, Scope, injectable

@injectable(scope=Scope.SINGLETON)
class MyService:
    def __init__(
        self,
        article_service: Annotated[ArticleService, Inject()],
    ):
        self.article_service = article_service
```

2. **Use in FastAPI Endpoints**:

```python
@app.get("/my-endpoint")
@inject_adapter  # Add this decorator
async def my_endpoint(
    my_service: Annotated[MyService, Inject()],
):
    # Use the service
    return my_service.some_method()
```

### Testing the Adapter

Run the test script to verify adapter functionality:

```bash
./scripts/test_injectable_adapter.sh
```

## Migration Strategy

The adapter supports an incremental migration path:

1. **Phase 1**: Register all DIContainer services with fastapi-injectable
2. **Phase 2**: Create new services using fastapi-injectable directly
3. **Phase 3**: Gradually migrate existing services to fastapi-injectable
4. **Phase 4**: Remove DIContainer once migration is complete

## Troubleshooting

- **Service not found**: Ensure the service is registered in DIContainer
- **Scope mismatch**: Check that service lifetimes are compatible
- **Circular dependencies**: Use lazy loading patterns or refactor dependencies
- **Type errors**: Ensure type annotations are correct with Annotated[Type, Inject()]

## Best Practices

- Always use the `@inject_adapter` decorator with FastAPI endpoints using injected services
- Keep service registration in a centralized location
- Test both DIContainer and fastapi-injectable during migration
- Document service dependencies clearly with type annotations
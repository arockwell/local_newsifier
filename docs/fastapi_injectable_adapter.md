# FastAPI Injectable Adapter

This document explains how to use the adapter that bridges between our custom DIContainer and fastapi-injectable. The adapter allows for an incremental migration path while maintaining compatibility with existing code.

## Background

The Local Newsifier project is transitioning from a custom DIContainer to use fastapi-injectable for dependency injection. This adapter enables both systems to coexist during migration.

## Components

### 1. Adapter Module (`fastapi_injectable_adapter.py`)

The adapter module provides utilities for:
- Registering DIContainer services with fastapi-injectable
- Determining appropriate caching behavior
- Adapting decorator patterns

Key functions include:

#### `get_service_factory(service_name: str) -> Callable`

Creates factory functions that delegate to DIContainer with proper caching behavior:

```python
def get_service_factory(service_name: str) -> Callable:
    """Create a factory function that gets a service from DIContainer."""
    # Determine appropriate caching behavior based on service type
    stateful_patterns = [
        "_service", "tool", "analyzer", "parser", "extractor", "resolver", "_crud"
    ]
    
    # Components that interact with state or databases should use use_cache=False
    use_cache = True  # Default to caching for performance
    
    # For stateful components or those interacting with databases, disable caching
    for pattern in stateful_patterns:
        if pattern in service_name:
            use_cache = False
            break
    
    @injectable(use_cache=use_cache)
    def service_factory():
        """Factory function to get service from DIContainer."""
        return di_container.get(service_name)
    
    # Set better function name for debugging
    service_factory.__name__ = f"get_{service_name}"
    
    return service_factory
```

#### `register_with_injectable(service_name: str, service_class: Type[T]) -> Callable`

Registers a service from DIContainer with fastapi-injectable:

```python
def register_with_injectable(service_name: str, service_class: Type[T]) -> Callable:
    """Register a service from DIContainer with fastapi-injectable."""
    factory = get_service_factory(service_name)
    return factory
```

#### `inject_adapter(func: Callable) -> Callable`

Decorator that adapts between fastapi-injectable and DIContainer:

```python
def inject_adapter(func: Callable) -> Callable:
    """Decorator to adapt between fastapi-injectable and DIContainer."""
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        # For async functions
        result = await get_injected_obj(func, args=list(args), kwargs=kwargs.copy())
        return result
        
    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        # For sync functions
        result = get_injected_obj(func, args=list(args), kwargs=kwargs.copy())
        return result
    
    # Choose the right wrapper based on whether the function is async
    if inspect.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper
```

#### `migrate_container_services(app: FastAPI) -> None`

Registers all DIContainer services with fastapi-injectable:

```python
async def migrate_container_services(app: FastAPI) -> None:
    """Register all DIContainer services with fastapi-injectable."""
    # Register the FastAPI app with fastapi-injectable
    await register_app(app)
    
    # Register direct service instances
    for name, service in di_container._services.items():
        if service is not None:
            try:
                service_class = service.__class__
                factory = get_service_factory(name)  # This handles caching behavior
                logger.info(f"Registered service {name} with fastapi-injectable")
            except Exception as e:
                logger.error(f"Error registering service {name}: {str(e)}")
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
from fastapi_injectable import register_app
from local_newsifier.fastapi_injectable_adapter import migrate_container_services, lifespan_with_injectable

# Use the adapter-provided lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database
    create_db_and_tables()
    
    # Use the adapter's lifespan function
    async with lifespan_with_injectable(app):
        # Let FastAPI handle requests
        yield
```

### Using Injectable Services

1. **Define an Injectable Service**:

```python
from typing import Annotated
from fastapi import Depends
from fastapi_injectable import injectable

@injectable(use_cache=False)  # Create new instance for each injection
class MyService:
    def __init__(
        self,
        article_service: Annotated[ArticleService, Depends(get_article_service)],
    ):
        self.article_service = article_service
```

2. **Use in FastAPI Endpoints**:

```python
@app.get("/my-endpoint")
async def my_endpoint(
    my_service: Annotated[MyService, Depends()],
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
- **Instance state issues**: Check that service is using appropriate `use_cache` setting
- **Circular dependencies**: Use lazy loading patterns or refactor dependencies
- **Type errors**: Ensure type annotations are correct with Annotated[Type, Depends()]

## Best Practices

- Use `use_cache=False` for components that interact with the database or maintain state
- Keep service dependencies explicit with type annotations
- Test both DIContainer and fastapi-injectable during migration
- Document service dependencies clearly with type annotations
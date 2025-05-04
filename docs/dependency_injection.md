# Dependency Injection System

> **IMPORTANT NOTICE**: Local Newsifier is currently migrating from this custom DIContainer to fastapi-injectable.
> For comprehensive guidance on the current DI architecture and transition strategy, please refer to the
> [DI Architecture Guide](di_architecture.md). This document is maintained for reference purposes.

This document explains the original dependency injection (DI) container implementation in the Local Newsifier project.

## Overview

The DI container provides a centralized way to manage service dependencies, making it easier to:

- Test individual components in isolation
- Manage service lifecycles
- Handle circular dependencies
- Replace implementations without changing client code

## Key Components

### DIContainer

The core `DIContainer` class in `src/local_newsifier/di_container.py` provides:

- Service registration and resolution
- Factory method support for lazy loading
- Parameterized factory methods for dynamic dependency creation
- Service lifetime management (Singleton, Transient, Scoped)
- Circular dependency detection and resolution
- Child container support for request scoping
- Service cleanup handlers

### Container Instance

The singleton container instance is created in `src/local_newsifier/container.py`, which:

- Registers all application services
- Configures environment-specific settings
- Manages service dependencies

## Service Lifetimes

The DI container supports three service lifetimes:

1. **Singleton** (default): One instance for the entire application
2. **Transient**: New instance every time it's requested
3. **Scoped**: One instance per scope (e.g., per request)

```python
from local_newsifier.di_container import DIContainer, Scope

container = DIContainer()

# Register with different lifetimes
container.register("singleton_service", service, scope=Scope.SINGLETON)
container.register("transient_service", service, scope=Scope.TRANSIENT)
container.register("scoped_service", service, scope=Scope.SCOPED)
```

## Usage Examples

### Basic Service Registration and Resolution

```python
from local_newsifier.di_container import DIContainer

container = DIContainer()

# Register a service instance
container.register("service_name", service_instance)

# Get the service
service = container.get("service_name")
```

### Factory Registration for Lazy Loading

```python
# Register a factory function
container.register_factory("service_name", 
    lambda c: ServiceClass(dependency=c.get("other_service")))
```

### Parameterized Factory Methods

```python
# Register a factory that accepts parameters
container.register_factory_with_params("entity_service_with_params",
    lambda c, **kwargs: kwargs.get("entity_service") or c.get("entity_service")
)

# Call with parameters
service = container.get("entity_service_with_params", 
                        custom_param="value")
```

### Circular Dependency Resolution

```python
# These services depend on each other
container.register_factory("service_a", 
    lambda c: ServiceA(dependency=c.get("service_b")))

container.register_factory("service_b", 
    lambda c: ServiceB(dependency=c.get("service_a")))

# Works without causing infinite recursion
service_a = container.get("service_a")
```

### Cleanup Handlers

```python
# Register a cleanup function for resource management
container.register_cleanup("database", 
    lambda db: db.close())
```

### Child Containers

```python
# Create a child container for a request scope
request_container = container.create_child_scope()

# Register request-specific services
request_container.register("request_context", context)
```

## Integration Points

The DI container is integrated with:

1. **API Routes**: Uses container for service dependencies
2. **CLI Commands**: Gets services from container with fallbacks
3. **Celery Tasks**: Uses container services with graceful degradation
4. **Test Suite**: Supports mocking services for isolation

## Best Practices

1. **Register services at startup**: Initialize all services in `container.py`
2. **Use factory methods for complex services**: Avoids circular dependencies
3. **Consider service lifetime**: Use appropriate scope for each service
4. **Provide fallbacks**: For optional services, use fallback patterns to gracefully handle missing dependencies
5. **Use parameterized factories sparingly**: For dynamic dependency injection needs

## Testing with the Container

The DI container makes testing easier by allowing service mocking:

```python
def test_with_mock_service():
    # Create a test container
    test_container = DIContainer()
    
    # Register a mock service
    mock_service = MagicMock()
    test_container.register("service_name", mock_service)
    
    # Test component that uses the service
    component = ComponentUnderTest(container=test_container)
    component.do_something()
    
    # Verify mock was called correctly
    mock_service.method.assert_called_once()
```

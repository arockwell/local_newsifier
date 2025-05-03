# FastAPI-Injectable Migration Plan

This document outlines the plan and implementation details for migrating the Local Newsifier project from the custom DIContainer to the fastapi-injectable framework.

## Migration Goals

1. Provide a smooth transition path from our custom DIContainer to fastapi-injectable
2. Maintain backward compatibility during the migration phase
3. Ensure proper lifecycle management for all components
4. Simplify the dependency injection system
5. Improve compatibility with FastAPI's built-in dependency injection

## Implementation Strategy

The migration is being implemented in phases:

### Phase 1: Foundation (Current Phase)

- Create an adapter layer between DIContainer and fastapi-injectable
- Establish patterns for provider function implementation
- Set up appropriate caching behavior for different component types
- Update documentation and service definitions

### Phase 2: Component Migration

- Gradually migrate individual components to native fastapi-injectable providers
- Update service tests to work with both systems
- Refactor endpoints to use the new injection patterns

### Phase 3: Complete Migration

- Remove the adapter layer when no longer needed
- Fully transition to fastapi-injectable native patterns
- Remove the custom DIContainer

## Key Components

### Adapter Layer

The `fastapi_injectable_adapter.py` file serves as the bridge between our custom DIContainer and fastapi-injectable. It:

1. Registers DIContainer services with fastapi-injectable
2. Provides compatibility functions for both systems
3. Manages lifecycle appropriately through caching settings

### Service Provider Functions

Provider functions in `di/providers.py` follow these patterns:

```python
@injectable(use_cache=False)  # For stateful components or those with DB interactions
def get_article_service(
    article_crud: Annotated[Any, Depends(get_article_crud)],
    entity_crud: Annotated[Any, Depends(get_entity_crud)],
    session: Annotated[Session, Depends(get_session)]
):
    """Provide the article service."""
    from local_newsifier.services.article_service import ArticleService
    
    return ArticleService(
        article_crud=article_crud,
        entity_crud=entity_crud,
        session_factory=lambda: session
    )
```

### Caching Strategy

fastapi-injectable v0.7.0 doesn't have a Scope enum or scope parameter, but it does have the `use_cache` parameter that controls instance reuse:

- `use_cache=True` (default): Dependencies are cached and reused
- `use_cache=False`: New instances are created for each dependency request

Our strategy:
- `use_cache=False` for:
  - CRUD components (interact with database)
  - Services (maintain state)
  - Tools (parsers, analyzers, etc. with potential state)
- `use_cache=True` (default) could be used for:
  - Purely functional utilities with no state
  - Transformation functions that just convert inputs to outputs

For safety, we bias toward `use_cache=False` for most components to prevent potential state leakage issues.

### Component Registration

The migration process automatically registers existing DIContainer services with fastapi-injectable for compatibility:

```python
# Register app with fastapi-injectable
await register_app(app)

# Register all services in DIContainer with fastapi-injectable
await migrate_container_services(app)
```

## Implementation Details

### Detecting Component Types

The adapter automatically detects component types to determine appropriate caching behavior:

```python
stateful_patterns = [
    "_service", "tool", "analyzer", "parser", "extractor", "resolver", "_crud"
]

use_cache = True  # Default to caching for performance
    
# For stateful components or those interacting with databases, disable caching
for pattern in stateful_patterns:
    if pattern in service_name:
        use_cache = False
        break
```

### API Integration

FastAPI endpoints can use both the DIContainer and fastapi-injectable:

```python
@app.get("/entities/{entity_id}")
async def get_entity(
    entity_id: int,
    entity_service: Annotated[Any, Depends(get_entity_service)]
):
    """Get entity by ID."""
    return await entity_service.get_entity(entity_id)
```

### Testing Strategy

Tests are updated to work with both injection systems:
- Use pytest fixtures for compatibility
- Test with both DIContainer and fastapi-injectable
- Ensure proper cleanup between tests

## Best Practices

1. Always use `use_cache=False` for components that:
   - Interact with the database
   - Maintain state between calls
   - Require fresh instances for each operation

2. Provider function naming:
   - Use `get_` prefix for clarity (e.g., `get_article_service`)
   - Match the service name in the DIContainer

3. Keep dependencies explicit:
   - Use Annotated + Depends to clearly show dependencies
   - Avoid hiding dependencies

4. Session handling:
   - Use request-scoped sessions where appropriate
   - Pass session factory to services that need it

## Future Enhancements

1. Consider adopting more advanced scope management if added to fastapi-injectable
2. Reduce adapter code as migration progresses
3. Consider transitioning to fully native fastapi-injectable patterns
4. Improve fastapi-injectable documentation and examples

## References

- [FastAPI Dependency Injection](https://fastapi.tiangolo.com/tutorial/dependencies/)
- [fastapi-injectable GitHub](https://github.com/JasperSui/fastapi-injectable)
- [fastapi-injectable PyPI](https://pypi.org/project/fastapi-injectable/)
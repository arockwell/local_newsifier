# Instance Reuse Strategy with fastapi-injectable

This document outlines the instance reuse strategy used with fastapi-injectable in the Local Newsifier project. Understanding when to cache component instances and when to create fresh ones is critical for proper application behavior.

## Background

fastapi-injectable v0.7.0 provides a `use_cache` parameter to control whether instances are reused between dependency injections:

- `use_cache=True` (default): The same instance is reused for identical dependency injection requests
- `use_cache=False`: A new instance is created for each dependency injection request

This parameter determines the lifecycle of components within the application.

## Our Strategy

In Local Newsifier, we follow a conservative approach to instance reuse:

### Components that use `use_cache=False` (new instance each time)

1. **All CRUD components** that interact with the database
   - Entity CRUD, Article CRUD, etc.
   - These components execute database queries and shouldn't share state

2. **All services** that contain business logic
   - ArticleService, EntityService, etc.
   - Services often have internal state or work with database sessions

3. **All tools and processors** that analyze or transform data
   - Parsers, analyzers, extractors, resolvers, etc.
   - These often maintain processing state during operations

4. **Database sessions**
   - Each request needs its own fresh database session
   - Sessions must be properly closed when done

### Components that could potentially use `use_cache=True` (reused instances)

1. **Pure utility functions** without state
   - Functions that just transform inputs to outputs in a deterministic way
   - No side effects or state changes

2. **Configuration providers**
   - Settings objects that only provide read-only information
   - No state changes during application lifetime

## Implementation

The adapter automatically determines the appropriate `use_cache` setting based on component name patterns:

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

## Decision Guidelines

When creating new components, use these guidelines to determine the appropriate `use_cache` setting:

### Use `use_cache=False` when the component:

- Interacts with a database
- Maintains internal state
- Has side effects
- Uses database sessions
- Should be isolated per request/operation
- Holds resources that need proper cleanup

### Consider `use_cache=True` only when the component:

- Is completely stateless
- Has no side effects
- Does not interact with databases
- Contains only read-only operations
- Has expensive initialization that benefits from reuse

## Default Behavior

For safety, when in doubt, use `use_cache=False`. This ensures proper isolation between requests and operations, preventing subtle bugs related to shared state.

## Examples

### Service Provider with `use_cache=False`

```python
@injectable(use_cache=False)  # Database-interacting service needs fresh instances
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

### Database Session Provider

```python
@injectable(use_cache=False)  # Create new session for each injection
def get_session() -> Generator[Session, None, None]:
    """Provide a database session."""
    from local_newsifier.database.engine import get_session as get_db_session
    
    session = next(get_db_session())
    try:
        yield session
    finally:
        session.close()
```

## Troubleshooting

If you encounter issues related to component state or database interactions, check the `use_cache` setting:

1. **State leaking between requests**: Component is likely using `use_cache=True` when it should be using `use_cache=False`

2. **Database session errors**: Session might be closed or invalid; ensure you're using `use_cache=False` for database-interacting components

3. **Unexpected behavior**: Component might be sharing state when it shouldn't; switch to `use_cache=False`
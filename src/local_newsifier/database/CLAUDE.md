# Local Newsifier Database Guide

## Overview
The database module manages database connections, sessions, and transaction handling for the Local Newsifier system. It provides a consistent interface for working with the PostgreSQL database.

## Key Components

### Database Engine
- **engine.py**: Creates and manages database engines
- Handles connection pools, URL generation, and engine configuration
- Supports multiple database instances through environment variables

### Session Utilities
- Legacy `session_utils.py` module has been removed
- Use the `get_session` provider via FastAPI-Injectable for session management

## Database Connection Patterns

### Engine Creation
The system creates database engines based on configuration:

```python
def get_engine(database_url=None):
    """Get or create a database engine.
    
    Args:
        database_url: Optional database URL override
        
    Returns:
        SQLAlchemy engine instance
    """
    global _engines
    
    # Get database URL
    if database_url is None:
        from local_newsifier.config.settings import get_settings
        settings = get_settings()
        database_url = str(settings.DATABASE_URL)
    
    # Check if engine exists in cache
    if database_url in _engines:
        return _engines[database_url]
    
    # Create new engine
    engine = create_engine(
        database_url,
        echo=False,
        pool_pre_ping=True,
        pool_recycle=300
    )
    
    # Cache engine
    _engines[database_url] = engine
    
    return engine
```

### Session Management
Session management uses context managers:

```python
class SessionManager:
    """Session manager for database operations.
    
    Usage:
        with SessionManager() as session:
            # Use session for database operations
    """
    
    def __init__(self, database_url=None):
        """Initialize the session manager.
        
        Args:
            database_url: Optional database URL override
        """
        self.database_url = database_url
        self.session = None
    
    def __enter__(self):
        """Enter the context manager."""
        engine = get_engine(self.database_url)
        self.session = Session(engine)
        return self.session
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the context manager.
        
        If an exception occurred, rollback the session.
        Otherwise, commit the session.
        """
        if self.session:
            if exc_type:
                self.session.rollback()
            else:
                self.session.commit()
            self.session.close()
```

### FastAPI-Injectable Session Provider (Preferred)

The recommended approach for session management is using FastAPI-Injectable:

```python
@injectable(use_cache=False)
def get_session() -> Generator[Session, None, None]:
    """Provide a database session.
    
    Returns a session from the session factory and ensures
    it's properly closed when done.
    
    Yields:
        Database session
    """
    from local_newsifier.database.engine import get_session as get_db_session
    
    session = next(get_db_session())
    try:
        yield session
    finally:
        session.close()
```

This provider is used in services and components through dependency injection:

```python
@injectable(use_cache=False)
def get_entity_service(
    entity_crud: Annotated["CRUDEntity", Depends(get_entity_crud)],
    canonical_entity_crud: Annotated["CRUDCanonicalEntity", Depends(get_canonical_entity_crud)],
    session: Annotated[Session, Depends(get_session)]
):
    """Provide the entity service.
    
    Uses use_cache=False to create new instances for each injection,
    preventing state leakage between operations.
    """
    from local_newsifier.services.entity_service import EntityService
    
    return EntityService(
        entity_crud=entity_crud,
        canonical_entity_crud=canonical_entity_crud,
        session_factory=lambda: session
    )
```

### Multiple Cursor Support
The system supports multiple database instances:

```python
def get_database_url():
    """Get the database URL based on cursor ID.
    
    Returns:
        Database URL string
    """
    # Get base database URL from settings
    base_url = settings.POSTGRES_URL
    
    # Get cursor ID from environment
    cursor_id = os.environ.get("CURSOR_DB_ID")
    
    if cursor_id:
        # Parse URL components
        url_parts = urlparse(base_url)
        path = url_parts.path.rstrip('/')
        
        # Add cursor ID to database name
        if path:
            new_path = f"{path}_{cursor_id}"
        else:
            new_path = f"/{cursor_id}"
        
        # Reconstruct URL with modified path
        new_url = url_parts._replace(path=new_path).geturl()
        return new_url
    
    return base_url
```

## Best Practices

### Session Usage
- For components using the FastAPI-Injectable pattern:
  ```python
  @injectable(use_cache=False)
  class MyService:
      def __init__(self, session: Annotated[Session, Depends(get_session)]):
          self.session_factory = lambda: session
  
      def my_method(self):
          with self.session_factory() as session:
              # Use session for database operations
  ```


### Transaction Management
- By default, sessions are committed at the end of the context manager
- For explicit transaction control:
```python
with SessionManager() as session:
    try:
        # Database operations
        session.commit()
    except Exception:
        session.rollback()
        raise
```

### Connection Management
- Don't create database engines directly, use `get_engine()`
- Don't create sessions directly, use `SessionManager` or the FastAPI-Injectable provider
- Always close sessions after use (done automatically by context manager or injectable provider)

### SQLModel Best Practices
- Use `session.exec()` for SQLModel queries
- Bind parameters to queries before execution:
```python
query = query.bindparams(param=value)
result = session.exec(query).all()
```

- Don't pass SQLModel objects between sessions
- Return IDs rather than SQLModel objects from functions

### Error Handling
- Proper error handling for database operations:
```python
try:
    with SessionManager() as session:
        # Database operations
except sqlalchemy.exc.IntegrityError as e:
    # Handle integrity errors (e.g., unique constraint violations)
    logger.error(f"Integrity error: {e}")
except sqlalchemy.exc.OperationalError as e:
    # Handle operational errors (e.g., connection issues)
    logger.error(f"Operational error: {e}")
except Exception as e:
    # Handle other errors
    logger.exception(f"Unexpected database error: {e}")
```

### Connection Pooling
- The system uses connection pooling for efficiency
- Parameters are configured for optimal performance:
  - `pool_pre_ping=True`: Check connection validity before use
  - `pool_recycle=300`: Recycle connections every 5 minutes
  - `pool_size=5`: Default pool size (can be adjusted)

### Testing Considerations
- Use separate test databases for isolation
- Set `CURSOR_DB_ID` environment variable in tests
- Use `Session.begin()` for transactional tests:
```python
with Session(engine) as session:
    with session.begin():
        # Test operations are rolled back automatically
```

## Common Issues and Solutions

### "Instance is not bound to a Session" Error
This occurs when trying to access SQLModel objects after the session is closed.

**Solutions:**
1. Keep all operations within the session context
2. Return IDs or data dictionaries instead of SQLModel objects
3. Use eager loading with `selectinload()` for relationships
4. Set `expire_on_commit=False` for specific use cases

### "Session already has a transaction in progress" Error
This happens when trying to start a new transaction inside an existing one.

**Solution:**
Ensure your transaction contexts don't overlap:
```python
# Correct:
with SessionManager() as session:
    # All operations in one transaction

# Incorrect:
with SessionManager() as session:
    with session.begin():  # Error - session already has a transaction
        # Operations
```

### Connection Pool Exhaustion
This occurs when all connections in the pool are in use.

**Solutions:**
1. Ensure sessions are properly closed (context managers help)
2. Increase pool size for high-concurrency scenarios
3. Use shorter-lived sessions
4. Look for connection leaks in background tasks
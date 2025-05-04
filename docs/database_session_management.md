# Database Session Management Guide

This document outlines the standardized approach to database session management in the Local Newsifier project. This is the reference implementation following the changes made in Issue #231.

## Overview

The Local Newsifier project has standardized on a container-based session management approach. This approach provides several benefits:

- **Centralized Configuration**: Session parameters can be configured in one place
- **Testability**: Easier to mock for testing
- **Consistency**: Single pattern across the codebase
- **Flexibility**: Can be easily extended or modified in the future
- **Performance**: Optimized session management for tests and production
- **Dependency Resolution**: Proper integration with the DI container

## Standard Approach

### Getting a Database Session

The standard way to obtain a database session is:

```python
from local_newsifier.database.session_utils import get_db_session

with get_db_session() as session:
    # Database operations
    result = session.query(Model).filter(Model.id == 1).first()
    # ...
```

If you need to specify a container instance:

```python
with get_db_session(container=my_container) as session:
    # Database operations
```

### Using the Session Decorator

For functions that may receive a session from a caller:

```python
from local_newsifier.database.session_utils import with_db_session

@with_db_session
def my_function(session=None):
    # Use session for database operations
    result = session.query(Model).filter(Model.id == 1).first()
    return result
```

The decorator will:
1. Use the provided session if one is passed
2. Create a new session if none is provided
3. Handle session lifecycle (commit/rollback) automatically

## Migration Guide

### From SessionManager

Before:
```python
from local_newsifier.database.engine import SessionManager

with SessionManager() as session:
    # Database operations
```

After:
```python
from local_newsifier.database.session_utils import get_db_session

with get_db_session() as session:
    # Database operations
```

### From get_session()

Before:
```python
from local_newsifier.database.engine import get_session

for session in get_session():
    # Database operations
```

After:
```python
from local_newsifier.database.session_utils import get_db_session

with get_db_session() as session:
    # Database operations
```

### From with_session Decorator

Before:
```python
from local_newsifier.database.engine import with_session

@with_session
def my_function(session=None):
    # Database operations
```

After:
```python
from local_newsifier.database.session_utils import with_db_session

@with_db_session
def my_function(session=None):
    # Database operations
```

## Legacy Support

The legacy session management methods (`SessionManager`, `get_session()`, and `with_session`) are marked as deprecated. They emit deprecation warnings when used and should be replaced with the standardized utilities.

These legacy methods use the standardized approach internally, so they will continue to work correctly during the transition period. However, all code should be updated to use the new standardized utilities as soon as possible.

## Implementation Notes

The new standardized session management is implemented using a wrapper around the container-based session factory, which provides the following benefits:

1. **Circular Dependency Handling**: Uses deferred imports to avoid circular dependencies
2. **Container Integration**: Properly retrieves the session factory from the container
3. **Performance Optimization**: Includes special handling for test environments
4. **Error Handling**: Robust error handling and logging for failed operations
5. **Decorator Support**: Simplified decorator interface for database operations

The wrapper functions are implemented in `local_newsifier.database.session_utils`, and the container is configured to use these utilities in `local_newsifier.container`.

## Testing with the Standardized Approach

### Mocking Sessions

```python
def test_entity_service(mocker):
    # Mock the session
    mock_session = mocker.MagicMock()
    
    # Mock get_db_session to return the mock session
    mock_context = mocker.MagicMock()
    mock_context.__enter__.return_value = mock_session
    mock_context.__exit__.return_value = None
    
    mocker.patch('local_newsifier.database.session_utils.get_db_session', return_value=mock_context)
    
    # Test code that uses sessions
    # ...
```

### Testing with the Session Decorator

```python
@with_db_session
def function_to_test(session=None):
    # Function implementation
    
def test_decorated_function(mocker):
    # Create a mock session
    mock_session = mocker.MagicMock()
    
    # Call the function with the mock session
    result = function_to_test(session=mock_session)
    
    # Assert that the function used the session correctly
    mock_session.query.assert_called_once()
    # ...
```

## Best Practices

1. **Always use context managers**: This ensures proper session cleanup
2. **Handle exceptions appropriately**: Let the context manager handle commits and rollbacks
3. **Keep transactions focused**: Don't keep sessions open longer than necessary
4. **Use the decorator for functions that need sessions**: This makes the code more testable
5. **Pass sessions explicitly when possible**: This makes dependencies clearer

## Implementation Details

The standardized approach is implemented in `local_newsifier.database.session_utils`. The key components are:

- `get_db_session()`: Gets a session from the container
- `with_db_session`: Decorator that provides a session to a function

These functions handle session lifecycle management, error handling, and integration with the dependency injection container.

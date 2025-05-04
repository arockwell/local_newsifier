# Simplified Database Error Handling Approach

## Issues with Current PR

The current PR (#173) adds significant code (+695 lines, -6 lines) to implement database error handling, including:
- A new `database.py` module (211 lines)
- A new `ErrorHandledCRUDBase` class (126 lines)
- Extensive tests
- Documentation

This goes against the goal of streamlining and simplifying error handling.

## Proposed Simplified Approach

### 1. Enhance Existing Error Classification

Update `_classify_error` in `error.py` to handle database errors:

```python
def _classify_error(error: Exception, service: str) -> tuple:
    """Classify an exception into an appropriate error type."""
    
    # Database-specific errors (applies to any service)
    if isinstance(error, sqlalchemy.exc.IntegrityError):
        if "unique constraint" in str(error).lower():
            return "integrity", f"Unique constraint violation: {error}"
        elif "foreign key constraint" in str(error).lower():
            return "integrity", f"Foreign key constraint violation: {error}"
        return "integrity", f"Database integrity error: {error}"
    
    elif isinstance(error, sqlalchemy.orm.exc.NoResultFound):
        return "not_found", "Record not found in the database"
    
    elif isinstance(error, sqlalchemy.orm.exc.MultipleResultsFound):
        return "multiple", "Multiple records found where only one was expected"
    
    # Rest of existing classification logic...
```

### 2. Use the Generic Service Handler

Instead of creating a new `ErrorHandledCRUDBase`, simply use the existing decorator:

```python
# In crud/base.py

from local_newsifier.errors import handle_service_error

class CRUDBase(Generic[ModelType]):
    
    @handle_service_error("database")
    def get(self, db: Session, id: int) -> Optional[ModelType]:
        # ...
    
    @handle_service_error("database")
    def create(self, db: Session, *, obj_in: Union[Dict[str, Any], ModelType]) -> ModelType:
        # ...

    # ... Other methods with decorators
```

### 3. Add Database Error Messages

Add database-specific error messages to the existing `ERROR_MESSAGES`:

```python
# In handlers.py

ERROR_MESSAGES = {
    # ... existing messages
    
    "database": {
        "connection": "Could not connect to the database. Check database connection settings.",
        "timeout": "Database operation timed out. The database may be overloaded.",
        "integrity": "Database constraint violation. The operation violates database rules.",
        "not_found": "Requested record not found in the database.",
        "multiple": "Multiple records found where only one was expected.",
        "validation": "Invalid database request. Check input parameters.",
        "transaction": "Transaction error. The operation could not be completed."
    }
}
```

### 4. Add a Convenience Function (Optional)

A lightweight helper function could be added if needed:

```python
# In __init__.py

handle_database = lambda func: handle_service_error("database")(func)
```

## Benefits of This Approach

1. **Code Reduction**: Only adds ~20-30 lines to existing files, rather than 200+ new lines
2. **Consistency**: Uses the same error handling pattern throughout the codebase
3. **Simplicity**: No new inheritance hierarchies or complex interactions
4. **Maintainability**: Changes isolated to a few key places
5. **Testing**: Existing tests can be extended with a few additional cases

## Implementation Plan

1. Close current PR
2. Create a new PR with the simplified approach
3. Update documentation to show how to use the generic error handler for database operations
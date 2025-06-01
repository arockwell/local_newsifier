# Analysis: SQLAlchemy Session Rollback Error

## Issue Overview

After a duplicate key violation occurs, the SQLAlchemy session enters an invalid state and all subsequent operations fail with `PendingRollbackError`. This creates a cascading failure that affects the entire request lifecycle.

## Technical Details

### Error Signature
```
sqlalchemy.exc.PendingRollbackError: This Session's transaction has been rolled back due to a previous exception during flush. To begin a new transaction with this Session, first issue Session.rollback().
```

### Stack Trace Analysis
The error occurs in the session cleanup phase:
```python
File "/app/src/local_newsifier/api/dependencies.py", line 78, in get_session
    session.commit()
File "/opt/venv/lib/python3.12/site-packages/sqlalchemy/orm/session.py", line 2032, in commit
    trans.commit(_to_root=True)
```

## Root Cause Analysis

### 1. Session Lifecycle Issue
The session is being used after a failed transaction:
- Initial INSERT fails with IntegrityError
- Session automatically marks transaction for rollback
- Code continues trying to use the session
- Cleanup code tries to commit a rolled-back transaction

### 2. Error in Dependency Cleanup
The `get_session` dependency appears to have a finally block that commits:
```python
def get_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.commit()  # This fails after rollback
        session.close()
```

This pattern is problematic because:
- Commit is called even after errors
- No check for rollback state
- No proper error handling

### 3. Missing Error Boundaries
The webhook service doesn't properly handle transaction boundaries:
- No explicit rollback on errors
- Session state not cleaned up
- Error propagates to dependency cleanup

## Code Flow Analysis

1. **Request Start**
   - `get_session` creates new session
   - Session yielded to endpoint

2. **Processing**
   - Webhook processing begins
   - INSERT fails with duplicate key
   - Session marks transaction for rollback

3. **Error Propagation**
   - Exception bubbles up
   - No rollback called
   - Session in invalid state

4. **Cleanup Attempt**
   - `get_session` finally block executes
   - Tries to commit rolled-back transaction
   - `PendingRollbackError` thrown

5. **Double Error**
   - Original IntegrityError lost
   - PendingRollbackError masks real issue
   - Confusing error messages

## Impact

1. **Error Masking**: Real error (duplicate key) hidden by rollback error
2. **Debugging Difficulty**: Stack traces are confusing
3. **Session Corruption**: Session unusable after error
4. **Resource Leaks**: Potential connection pool issues

## Best Practices Violated

1. **Always rollback on error**: Not rolling back explicitly
2. **Check session state**: Not checking if rollback needed
3. **Separate concerns**: Mixing business logic with transaction management
4. **Error handling**: Not catching and handling specific errors

## Proposed Solutions

### Immediate Fix
```python
def get_session():
    session = SessionLocal()
    try:
        yield session
        session.commit()  # Only commit on success
    except Exception:
        session.rollback()  # Explicit rollback
        raise
    finally:
        session.close()  # Always close
```

### Better Pattern
```python
def get_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        if session.in_transaction():
            session.rollback()
        session.close()
```

### Service-Level Fix
```python
try:
    # Processing logic
    self.session.commit()
except IntegrityError:
    self.session.rollback()
    # Handle specific error
except Exception:
    self.session.rollback()
    raise
```

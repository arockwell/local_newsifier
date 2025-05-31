# Gameplan: Fix Webhook Async Error

## Objective
Fix the webhook endpoint crash that occurs when raising HTTPException within a session context, preventing proper error responses and causing session cleanup failures.

## Root Cause
The webhook endpoint raises HTTPException inside a database session context manager, which causes FastAPI's async-to-sync adapter to fail during cleanup with "generator didn't stop after throw()".

## Implementation Steps

### 1. Fix Session Exception Handling in engine.py
- Modify `get_session()` to properly handle exceptions during yield
- Ensure the generator can be properly closed even when exceptions occur
- Add explicit exception handling that doesn't interfere with context manager cleanup

### 2. Refactor Webhook Error Handling
- Move HTTPException raises outside of the session context
- Store error information and raise after session is closed
- Ensure proper error responses without breaking session management

### 3. Alternative: Use Try/Finally Pattern
- Replace context manager yield with explicit try/finally blocks
- Ensure session cleanup happens regardless of exceptions
- Maintain compatibility with FastAPI's dependency injection

## Specific Changes

### Option A: Fix Context Manager (Preferred)
```python
# In database/engine.py
@contextmanager
def get_session():
    engine = get_engine()
    if engine is None:
        logger.warning("Cannot create session - database engine is None")
        yield None
        return

    session = Session(engine)
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
```

### Option B: Refactor Webhook Endpoint
```python
# In webhooks.py
def apify_webhook(...):
    error_to_raise = None

    try:
        # Process webhook
        result = webhook_service.handle_webhook(...)

        # Store error for later if needed
        if result["status"] == "error":
            error_to_raise = HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["message"]
            )

    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        error_to_raise = HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

    # Raise error outside of session context
    if error_to_raise:
        raise error_to_raise

    return ApifyWebhookResponse(...)
```

## Testing Plan

1. Create test that reproduces the error:
   - Send webhook request with missing fields
   - Verify 400 response (not 500)
   - Check session cleanup

2. Test edge cases:
   - Multiple concurrent webhook requests
   - Database connection failures
   - Webhook validation failures

3. Verify no session leaks:
   - Monitor database connections
   - Stress test with many failed requests

## Success Criteria

- Webhook returns proper 400 Bad Request for validation errors
- No "generator didn't stop after throw()" errors in logs
- Database sessions properly cleaned up on all code paths
- All existing tests continue to pass

## Implementation Order

1. First implement the context manager fix (Option A)
2. Test thoroughly
3. If issues persist, implement webhook refactoring (Option B)
4. Add comprehensive error handling tests
5. Update documentation if API behavior changes

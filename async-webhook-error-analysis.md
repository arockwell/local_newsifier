# Async Webhook Error Analysis

## Error Summary

The error occurs when hitting the `/webhooks/apify` endpoint. Despite removing all async code from the application, we're getting an async-related error:

```
RuntimeError: There is no current event loop in thread 'AnyIO worker thread'.
```

## Root Cause Analysis

The error is coming from `fastapi-injectable` version 0.7.0, specifically from the `get_session` provider function. Here's the problematic flow:

1. The webhook endpoint is correctly defined as sync (`def apify_webhook`, not `async def`)
2. It depends on `get_session` from `api/dependencies.py`
3. `api/dependencies.py:get_session()` delegates to `di/providers.py:get_session()`
4. The `get_session` provider is decorated with `@injectable(use_cache=False)`
5. Inside `fastapi-injectable`, when resolving dependencies for a sync function, it tries to run async code synchronously
6. This fails because there's no event loop in the current thread (AnyIO worker thread)

## Stack Trace Analysis

Looking at the stack trace:
- Line 89: `fastapi_injectable/decorator.py:68` in `sync_wrapper` calls `run_coroutine_sync(resolve_dependencies(...))`
- Line 95: `fastapi_injectable/concurrency.py:154` in `run_coroutine_sync` calls `loop_manager.run_in_loop(coro)`
- Line 107: `fastapi_injectable/concurrency.py:74` in `get_loop` calls `asyncio.get_event_loop()`
- Line 117: This fails with `RuntimeError: There is no current event loop in thread 'AnyIO worker thread'`

## The Problem

The `fastapi-injectable` library appears to have an issue when:
1. A sync endpoint depends on an injectable provider
2. The provider is being resolved within FastAPI's thread pool (via `run_in_threadpool`)
3. The library tries to get an event loop in a thread that doesn't have one

## Potential Solutions

### Solution 1: Remove Injectable from Session Provider
Instead of using `@injectable` for the session provider, we could use a standard FastAPI dependency:

```python
# In api/dependencies.py
def get_session() -> Generator[Session, None, None]:
    """Get a database session."""
    from local_newsifier.database.engine import get_session as get_db_session

    session = next(get_db_session())
    try:
        yield session
    finally:
        session.close()
```

### Solution 2: Use FastAPI's Depends Directly
Modify the webhook endpoint to use the database session directly without going through the injectable system.

### Solution 3: Downgrade or Upgrade fastapi-injectable
The issue might be specific to version 0.7.0. We could try:
- Downgrading to an earlier version
- Checking if there's a newer version with a fix

### Solution 4: Create a Sync-Only Injectable Wrapper
Create a wrapper that ensures the injectable resolution happens in a sync context without trying to access an event loop.

## Recommended Approach

The safest immediate fix is **Solution 1**: Remove the `@injectable` decorator from the `get_session` provider and use it as a regular FastAPI dependency. This bypasses the problematic async-to-sync conversion in `fastapi-injectable`.

The session management is a fundamental dependency that doesn't need the complexity of the injectable system. Using FastAPI's built-in dependency injection for database sessions is a common and well-tested pattern.

## Next Steps

1. Remove `@injectable` from `get_session` in `di/providers.py`
2. Update `api/dependencies.py` to use the database session directly
3. Test the webhook endpoint to ensure it works
4. Consider migrating other critical dependencies away from `fastapi-injectable` if similar issues arise

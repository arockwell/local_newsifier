# FastAPI Async/Sync Context Crash Analysis

## Issue Summary

The application is crashing due to mixing async and sync patterns in FastAPI endpoints. The stack trace shows a failure in `contextmanager_in_threadpool` when FastAPI attempts to manage synchronous dependencies within async endpoints.

## Root Cause

The crash occurs because:
1. Endpoints are defined as `async def` (asynchronous)
2. Dependencies use synchronous database sessions via `yield from`
3. FastAPI attempts to bridge this gap using `contextmanager_in_threadpool`
4. The context manager fails when entering the async context

## Stack Trace Analysis

```
File "/opt/venv/lib/python3.12/site-packages/fastapi/concurrency.py", line 35, in contextmanager_in_threadpool
    raise e
File "/opt/venv/lib/python3.12/site-packages/fastapi/concurrency.py", line 27, in contextmanager_in_threadpool
    yield await run_in_threadpool(cm.__enter__)
```

This shows FastAPI trying to run a synchronous context manager (`cm.__enter__`) in a thread pool to make it compatible with async code, but failing.

## Affected Components

### 1. API Dependencies (`src/local_newsifier/api/dependencies.py`)
- `get_session()` uses `yield from` (sync pattern)
- Service getters use `with next(get_session())` (sync context manager)

### 2. System Router (`src/local_newsifier/api/routers/system.py`)
- All endpoints marked as `async def`
- Using sync `Session` dependency
- Incompatible async/sync mix

### 3. Tasks Router (`src/local_newsifier/api/routers/tasks.py`)
- Async endpoints with sync service dependencies
- Same pattern causing crashes

### 4. Inconsistent Implementation
- `webhooks.py` correctly uses `AsyncSession`
- Other routers still use sync patterns
- Mixed implementation across codebase

## Impact

- Application crashes on any API request
- Complete service unavailability
- Deployment failures
- Cannot handle concurrent requests properly

## Technical Details

The issue stems from Python's event loop restrictions:
- Async functions run in an event loop
- Sync I/O operations block the event loop
- FastAPI's `contextmanager_in_threadpool` is a workaround that's failing
- The failure suggests deeper architectural issues with session management

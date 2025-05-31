# Webhook Async Error Analysis

## Issue Summary

The application is crashing with a `RuntimeError: generator didn't stop after throw()` when processing webhook requests to the `/webhooks/apify` endpoint. This error occurs when an HTTPException is raised within the webhook handler and the session context manager fails to properly clean up.

## Root Cause

The error chain shows two fundamental issues:

1. **Primary Issue**: The webhook endpoint is raising an HTTPException (400: Missing required fields) at line 74 in `webhooks.py`
2. **Secondary Issue**: When this exception is raised, the session context manager in `database/engine.py` cannot properly clean up, leading to the "generator didn't stop after throw()" error

## Technical Details

### Error Flow:

1. Webhook request comes in to `/webhooks/apify`
2. The webhook service processes the request and returns an error result with `status = "error"`
3. The endpoint raises an HTTPException at line 74:
   ```python
   if result["status"] == "error":
       raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result["message"])
   ```
4. This exception interrupts the session context manager yielding at `engine.py:157`
5. FastAPI's async context management tries to clean up the session using `contextmanager_in_threadpool`
6. The cleanup fails because the generator (session context manager) is in an inconsistent state

### The Async/Sync Mismatch

The core issue is that the application is mixing async and sync patterns:
- The endpoint is defined as a sync function (`def apify_webhook`)
- But it's using a sync session dependency (`get_session`)
- FastAPI is running this sync code in a thread pool via `run_in_threadpool`
- When an exception occurs, the async cleanup mechanism conflicts with the sync generator

## Impact

- 500 Internal Server Error returned to clients instead of proper 400 Bad Request
- Database sessions may not be properly closed, leading to connection leaks
- The actual validation error message is lost in the crash

## Solution Requirements

1. Fix the session management to handle exceptions properly
2. Ensure the webhook endpoint returns proper HTTP status codes
3. Prevent the generator cleanup error
4. Maintain sync-only architecture (per project requirements)

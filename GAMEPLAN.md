# FastAPI Async to Sync Conversion Gameplan

## Overview
This document outlines the systematic approach to convert all FastAPI routes and dependencies from async to sync patterns. The conversion will be done in phases to ensure stability and testability at each step.

## Phase 1: Remove Async Services and Dependencies

### 1.1 Convert Async Service Classes
- [x] ~~Convert `apify_webhook_service_async.py` to sync~~ (Removed - sync version already exists)
  - ~~Remove all `async/await` keywords~~
  - ~~Replace `AsyncSession` with `Session`~~
  - ~~Update method signatures~~
- [x] ~~Convert `apify_service_async.py` to sync~~ (Removed - sync version already exists)
- [x] ~~Remove/convert `async_article.py` CRUD module~~ (Removed - sync version already exists)
- [x] ~~Update `async_base.py` if still in use~~ (Removed - no longer needed)

### 1.2 Update Async Providers
- [x] ~~Check `di/async_providers.py` and convert any async providers to sync~~ (Removed - no longer needed)
- [x] ~~Update provider functions to return sync instances~~ (Not applicable - async providers removed)

### 1.3 Database Engine Updates
- [x] ~~Review `database/async_engine.py` and ensure all async patterns are removed~~ (Removed - no longer needed)
- [x] ~~Update any async session factories to sync~~ (Not applicable - async engine removed)

## Phase 2: Convert Application Lifecycle

### 2.1 Main Application File (`api/main.py`)
- [x] Keep `lifespan` context manager as async (FastAPI requirement)
  - FastAPI requires lifespan to be async
  - Keep `await register_app(app)` call
- [x] Update exception handler (`not_found_handler`) to sync
- [x] Convert main route handlers (`root`, `health_check`, `get_config`) to sync
- [x] Update tests to handle async lifespan properly

## Phase 3: Convert Route Handlers

### 3.1 Authentication Routes (`routers/auth.py`)
- [x] Convert `login_page()` to sync
- [x] Convert `login()` to sync
- [x] Convert `logout()` to sync

### 3.2 System Routes (`routers/system.py`)
- [x] Convert `get_tables()` to sync
- [x] Convert `get_tables_api()` to sync
- [x] Convert `get_table_details()` to sync
- [x] Convert `get_table_details_api()` to sync

### 3.3 Task Routes (`routers/tasks.py`)
- [x] Convert `tasks_dashboard()` to sync
- [x] Convert `process_article_endpoint()` to sync
- [x] Convert `fetch_rss_feeds_endpoint()` to sync
- [x] Convert `get_task_status()` to sync
- [x] Convert `cancel_task()` to sync

### 3.4 Webhook Routes (`routers/webhooks.py`)
- [x] Keep `apify_webhook()` as async (required for `await request.body()`)
- [x] Keep `await request.body()` (FastAPI requirement)
- [x] Update webhook service calls to use sync version

### 3.5 Main Routes (`api/main.py`)
- [x] Convert `root()` to sync
- [x] Convert `health_check()` to sync
- [x] Convert `get_config()` to sync

## Phase 4: Update Tests

### 4.1 API Tests
- [x] Update `tests/api/test_auth.py` to remove async patterns
- [x] Update `tests/api/test_system.py` to remove async patterns
- [x] Update `tests/api/test_tasks.py` to remove async patterns
- [x] Update `tests/api/test_webhooks.py` to remove async patterns
- [x] Update `tests/api/test_main.py` to remove async patterns

### 4.2 Service Tests
- [x] Update tests for converted async services (all async services removed)
- [x] Remove any async test fixtures (removed event_loop fixture)

## Phase 5: Cleanup and Optimization

### 5.1 Remove Async Dependencies
- [x] Remove `httpx` async client usage (no httpx usage found)
- [x] Remove `asyncio` imports (only in main.py lifespan, which is required)
- [x] Update `requirements.txt` if needed (removed pytest-asyncio, aiosqlite, asyncpg)

### 5.2 Update Documentation
- [x] Update API documentation to reflect sync patterns (already sync-only)
- [x] Update CLAUDE.md files in affected directories (removed async references)
- [x] Update any example code in docs (already shows async as WRONG examples)

## Implementation Order

1. **Start with services** (Phase 1) - Convert underlying async services first
2. **Update lifecycle** (Phase 2) - Convert app startup/shutdown
3. **Convert routes bottom-up** (Phase 3) - Start with simple routes, move to complex
4. **Update tests incrementally** (Phase 4) - Test each converted component
5. **Final cleanup** (Phase 5) - Remove unused async code

## Testing Strategy

After each phase:
1. Run the full test suite: `make test`
2. Test the API manually with key endpoints
3. Check for any deprecation warnings
4. Verify no async runtime errors

## Rollback Plan

- Create a new branch for this work: `convert-fastapi-to-sync`
- Commit after each successful phase
- Tag stable points for easy rollback
- Keep async versions temporarily with `_async` suffix until fully migrated

## Success Criteria

- [x] All `async def` converted to `def` in API routes (except lifespan which is required)
- [x] No `await` keywords in API code (except in lifespan and webhook body reading)
- [ ] All tests passing
- [ ] No async runtime warnings
- [ ] API performance maintained or improved
- [ ] Code coverage maintained at >90%

## Notes

- FastAPI supports both sync and async handlers natively
- Sync handlers may be more performant for I/O-bound database operations
- This aligns with the project's move away from async patterns
- Celery tasks remain unaffected as they're already sync
- During transition, duplicate sync services are created with "_sync" suffix to avoid conflicts:
  - `apify_webhook_service_sync.py` (duplicate of `apify_webhook_service.py` for clarity)

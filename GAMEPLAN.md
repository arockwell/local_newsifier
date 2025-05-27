# FastAPI Async to Sync Conversion Gameplan

## Overview
This document outlines the systematic approach to convert all FastAPI routes and dependencies from async to sync patterns. The conversion will be done in phases to ensure stability and testability at each step.

## Phase 1: Remove Async Services and Dependencies

### 1.1 Convert Async Service Classes
- [ ] Convert `apify_webhook_service_async.py` to sync
  - Remove all `async/await` keywords
  - Replace `AsyncSession` with `Session`
  - Update method signatures
- [ ] Convert `apify_service_async.py` to sync (or remove if duplicate of sync version)
- [ ] Remove/convert `async_article.py` CRUD module
- [ ] Update `async_base.py` if still in use

### 1.2 Update Async Providers
- [ ] Check `di/async_providers.py` and convert any async providers to sync
- [ ] Update provider functions to return sync instances

### 1.3 Database Engine Updates
- [ ] Review `database/async_engine.py` and ensure all async patterns are removed
- [ ] Update any async session factories to sync

## Phase 2: Convert Application Lifecycle

### 2.1 Main Application File (`api/main.py`)
- [ ] Convert `lifespan` context manager from async to sync
  - Remove `async` keyword
  - Update any startup/shutdown logic
- [ ] Convert `register_app` function to sync
- [ ] Update exception handler (`not_found_handler`) to sync

## Phase 3: Convert Route Handlers

### 3.1 Authentication Routes (`routers/auth.py`)
- [ ] Convert `login_page()` to sync
- [ ] Convert `login()` to sync
- [ ] Convert `logout()` to sync

### 3.2 System Routes (`routers/system.py`)
- [ ] Convert `get_tables()` to sync
- [ ] Convert `get_tables_api()` to sync
- [ ] Convert `get_table_details()` to sync
- [ ] Convert `get_table_details_api()` to sync

### 3.3 Task Routes (`routers/tasks.py`)
- [ ] Convert `tasks_dashboard()` to sync
- [ ] Convert `process_article_endpoint()` to sync
- [ ] Convert `fetch_rss_feeds_endpoint()` to sync
- [ ] Convert `get_task_status()` to sync
- [ ] Convert `cancel_task()` to sync

### 3.4 Webhook Routes (`routers/webhooks.py`)
- [x] Convert `apify_webhook()` to sync
- [x] Replace `await request.body()` with `request.body`
- [x] Update webhook service calls to use sync version

### 3.5 Main Routes (`api/main.py`)
- [ ] Convert `root()` to sync
- [ ] Convert `health_check()` to sync
- [ ] Convert `get_config()` to sync

## Phase 4: Update Tests

### 4.1 API Tests
- [ ] Update `tests/api/test_auth.py` to remove async patterns
- [ ] Update `tests/api/test_system.py` to remove async patterns
- [ ] Update `tests/api/test_tasks.py` to remove async patterns
- [ ] Update `tests/api/test_webhooks.py` to remove async patterns
- [ ] Update `tests/api/test_main.py` to remove async patterns

### 4.2 Service Tests
- [ ] Update tests for converted async services
- [ ] Remove any async test fixtures

## Phase 5: Cleanup and Optimization

### 5.1 Remove Async Dependencies
- [ ] Remove `httpx` async client usage (switch to `requests`)
- [ ] Remove `asyncio` imports
- [ ] Update `requirements.txt` if needed

### 5.2 Update Documentation
- [ ] Update API documentation to reflect sync patterns
- [ ] Update CLAUDE.md files in affected directories
- [ ] Update any example code in docs

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

- [ ] All `async def` converted to `def` in API routes
- [ ] No `await` keywords in API code
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

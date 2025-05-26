# Event Loop Stabilization Plan

## Overview

This document tracks the ongoing effort to stabilize event loop handling in the Local Newsifier codebase, particularly addressing issues with async/await patterns in tests and removing the problematic `event_loop_fixture`.

## Problem Statement

The codebase has been experiencing event loop-related issues, particularly in CI environments, due to:
1. Mixing sync and async patterns without proper handling
2. The `event_loop_fixture` creating conflicts with pytest-asyncio's event loop management
3. Flaky tests marked with `@ci_skip_async` that hide underlying event loop problems
4. Inconsistent async/await usage across the codebase

## Progress to Date

### Completed (as of PR fix-event-loop-stabilization)

1. **Removed Problematic Event Loop Fixture**
   - Deleted `tests/fixtures/event_loop.py` which was creating event loop conflicts
   - Removed all imports and usage of `event_loop_fixture` from test files

2. **Fixed Import Errors**
   - Updated all test files that were importing the removed fixture
   - Ensured tests run without the custom event loop management

3. **Removed Flaky CI Skip Decorators**
   - Removed `@ci_skip_async` decorators that were hiding event loop issues
   - Tests now run consistently in both local and CI environments

### Files Modified
- Removed: `tests/fixtures/event_loop.py`
- Updated imports in:
  - `tests/api/test_injectable_endpoints.py`
  - `tests/cli/test_injectable_cli.py`
  - `tests/cli/test_injectable_providers.py`
  - `tests/di/test_crud_providers.py`
  - `tests/di/test_db_inspect_command_provider.py`
  - `tests/di/test_file_writer_provider.py`
  - `tests/di/test_rss_parser_provider.py`
  - `tests/di/test_sentiment_analyzer_provider.py`
  - `tests/examples/test_injectable_flow_example.py`
  - `tests/examples/test_injectable_service_example.py`
  - `tests/examples/test_injectable_tool_example.py`
  - `tests/flows/test_entity_tracking_flow_service.py`
  - `tests/services/test_apify_service_impl.py`
  - `tests/services/test_entity_service_impl.py`
  - `tests/services/test_news_pipeline_service.py`
  - `tests/tools/test_injectable_sentiment_tracker.py`
  - `tests/tools/test_injectable_trend_reporter.py`
  - `tests/tools/test_opinion_visualizer_impl.py`
  - `tests/tools/test_web_scraper_impl.py`

## Remaining Work

### Documentation Updates Needed

1. **CLAUDE.md** - Remove the "Handling Event Loop Issues in Tests" section that recommends using `event_loop_fixture`

2. **Other Documentation Files** - Update the following files that reference event loop handling:
   - `docs/testing_injectable_dependencies.md`
   - `docs/injectable_patterns.md`
   - `docs/injectable_examples.md`
   - `docs/di_conversion_plan.md`
   - `tests/examples/README.md`

### Code Changes Still Required

1. **Async Pattern Consistency**
   - Many test files still mix sync and async patterns
   - Need to standardize on using `pytest.mark.asyncio` for async tests
   - Remove unnecessary `asyncio.run()` calls in favor of proper async test functions

2. **Service Layer Async Conversion**
   - Services that perform I/O operations should be converted to async
   - Update corresponding tests to use async patterns

3. **Dependency Injection Async Support**
   - Ensure all injectable providers properly handle async dependencies
   - Update provider functions to be async where appropriate

### Specific Files Needing Attention

Based on the codebase analysis, the following areas still need event loop improvements:

1. **Conditional Decorator Pattern Usage**
   - Several tools use the conditional decorator pattern to avoid event loop issues
   - Files like `tools/opinion_visualizer.py` and `tools/web_scraper.py`
   - This pattern should be removed once the root cause is addressed

2. **Mixed Sync/Async in Tests**
   - Tests that use `asyncio.run()` or `loop.run_until_complete()`
   - Should be converted to proper `@pytest.mark.asyncio` async tests
   - Particularly in integration tests and flow tests

3. **Injectable Components**
   - Components decorated with `@injectable` may still have event loop issues
   - Need systematic review and testing of all injectable components
   - Consider migrating away from fastapi-injectable as per the migration plan

4. **CLI Commands**
   - CLI commands that interact with async services
   - Need to properly handle the sync/async boundary
   - Consider using asyncio.run() at the CLI entry point only

5. **Celery Tasks**
   - Tasks that interact with async services
   - Need proper async handling in Celery workers
   - May require celery[asyncio] support

## Best Practices Going Forward

### For Writing Tests

1. **Use pytest-asyncio for Async Tests**
   ```python
   @pytest.mark.asyncio
   async def test_async_functionality():
       result = await async_function()
       assert result == expected
   ```

2. **Mock Async Dependencies Properly**
   ```python
   with patch("module.async_dependency", new_callable=AsyncMock) as mock:
       mock.return_value = expected_value
       # Test code here
   ```

3. **Avoid Mixing Sync/Async**
   - Don't use `asyncio.run()` inside tests
   - Use `@pytest.mark.asyncio` for async test functions
   - Keep async and sync code paths separate

### For Application Code

1. **Consistent Async Patterns**
   - I/O-bound operations should be async
   - CPU-bound operations can remain sync
   - Use `asyncio` utilities properly

2. **Proper Session Management**
   - Use async session managers for async operations
   - Don't mix sync and async database sessions

## Timeline

- **Phase 1** (Completed): Remove event_loop_fixture and fix immediate issues
- **Phase 2** (Current): Update documentation to reflect new patterns
- **Phase 3** (Next): Systematically convert remaining sync code to async where appropriate
- **Phase 4** (Future): Full async/await adoption for all I/O operations

## Related Issues

- Event loop conflicts in CI environments
- Flaky tests requiring `@ci_skip_async` decorator
- Import errors after removing custom fixtures
- Documentation promoting outdated patterns

## Success Criteria

1. All tests pass consistently in both local and CI environments
2. No custom event loop management code
3. Clear, consistent async/await patterns throughout the codebase
4. Updated documentation reflecting current best practices
5. No flaky tests hidden behind skip decorators

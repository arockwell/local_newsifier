# Event Loop Stabilization Plan

## Overview

This document tracks the ongoing effort to stabilize event loop handling in the Local Newsifier codebase, particularly addressing issues with async/await patterns in tests and removing the problematic `event_loop_fixture`.

## Problem Statement

The codebase has been experiencing event loop-related issues, particularly in CI environments, due to:
1. Mixing sync and async patterns without proper handling
2. The `event_loop_fixture` creating conflicts with pytest-asyncio's event loop management
3. Flaky tests marked with `@ci_skip_async` that hide underlying event loop problems
4. Inconsistent async/await usage across the codebase

> **📚 Related Documentation**: For a comprehensive catalog of async/sync antipatterns found in this codebase, see [async-migration/async-antipatterns-catalog.md](async-migration/async-antipatterns-catalog.md)

## Progress to Date

### Phase 1: Event Loop Fixture Simplification (Completed - Commit a0e3eee)

1. **Removed Problematic Event Loop Fixture**
   - Deleted `tests/fixtures/event_loop.py` which was creating event loop conflicts
   - Replaced complex thread-local storage approach with simple pytest fixture
   - Added simpler `run_async` helper for running async code in sync tests

2. **Removed Flaky CI Skip Decorators**
   - Eliminated `@ci_skip_async` and `@ci_skip_injectable` decorators that were hiding issues
   - Tests now run consistently in both local and CI environments
   - Updated pytest configuration to disable parallel execution by default

3. **Fixed Test Configuration**
   - Updated `conftest.py` to create proper event loops per test
   - Removed complex context manager patterns
   - Simplified async test execution

### Phase 2: Import Error Fixes (Completed - Commit 611552a)

1. **Fixed Broken Imports**
   - Removed references to deleted fixtures (`injectable_service_fixture`, old `event_loop`)
   - Corrected import paths (e.g., `src.local_newsifier` → `local_newsifier`)
   - Removed unused imports and fixed flake8 issues

2. **Files Modified**
   - Removed: `tests/fixtures/event_loop.py`
   - Updated imports in 19 test files across api, cli, di, flows, services, tools, and examples

### Phase 3: Documentation Updates (Completed - Commit cf3ac68)

1. **Updated CLAUDE.md**
   - Removed outdated "Handling Event Loop Issues in Tests" section
   - Added modern pytest-asyncio patterns and best practices
   - Updated async testing guidelines

2. **Updated Related Documentation**
   - Created this comprehensive plan document
   - Updated FastAPI-Injectable migration plans
   - Modified all docs that referenced old event loop patterns

3. **Documentation Files Updated**
   - `CLAUDE.md` (removed event loop fixture recommendations)
   - `docs/testing_injectable_dependencies.md`
   - `docs/injectable_patterns.md`
   - `docs/injectable_examples.md`
   - `docs/FastAPI-Injectable-Migration-Plan.md`
   - `tests/examples/README.md`

## Remaining Work

### Phase 4: Remove Remaining Event Loop Fixture Usage (🔄 In Progress)

Based on analysis, 28 test files still import or use the old event loop fixture pattern:

1. **Services (4 files)**
   - Need to convert to async patterns or remove event loop dependencies
   - Update corresponding tests

2. **DI Providers (4 files)**
   - Review and update provider functions for async compatibility
   - Ensure proper async dependency handling

3. **Tools (13 files)**
   - Remove event_loop_fixture imports
   - Convert to proper async patterns

4. **Flows (7 files)**
   - Update flow implementations to handle async properly
   - Remove sync/async mixing

5. **API (1 file)**
   - Ensure proper async handling in FastAPI endpoints

**📋 Detailed work breakdown:** See [event-loop-remaining-work.md](event-loop-remaining-work.md) for specific files and required changes.

### Phase 5: Full Async Conversion (Not Started)

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

> **🔍 See Also**: For correct async patterns and common pitfalls, refer to [async-migration/async-migration-patterns.md](async-migration/async-migration-patterns.md)

## Lessons Learned

1. **Simplicity is Key**
   - The complex thread-local event loop management was the root cause of CI failures
   - Simple, standard pytest-asyncio patterns eliminated all flaky behavior

2. **CI Skip Decorators Hide Problems**
   - `@ci_skip_async` and `@ci_skip_injectable` were masking real issues
   - Removing them forced us to address the underlying problems

3. **Documentation Debt is Real**
   - Multiple docs were promoting the problematic `event_loop_fixture`
   - Keeping docs synchronized with code changes is critical

4. **Incremental Migration Works**
   - The phased approach allowed us to fix critical issues first
   - Each phase built on the previous, making progress visible

5. **Mixed Async/Sync is Problematic**
   - The codebase still has many places mixing patterns
   - Clear boundaries between sync and async code are essential

## Timeline

- **Phase 1** (✅ Completed): Remove event_loop_fixture and fix immediate issues
- **Phase 2** (✅ Completed): Fix import errors from Phase 1
- **Phase 3** (✅ Completed): Update documentation to reflect new patterns
- **Phase 4** (🔄 In Progress): Remove remaining event loop fixture usage from 29 files
- **Phase 5** (📋 Planned): Full async conversion for I/O operations
- **Phase 6** (📋 Planned): Complete pytest.mark.asyncio adoption

## Related Issues

- Event loop conflicts in CI environments
- Flaky tests requiring `@ci_skip_async` decorator
- Import errors after removing custom fixtures
- Documentation promoting outdated patterns

## Progress Metrics

### Completed
- ✅ Event loop fixture removed (1 file deleted)
- ✅ CI skip decorators removed (2 decorators eliminated)
- ✅ Import errors fixed (19 test files updated)
- ✅ Documentation updated (6 docs modified)
- ✅ Tests passing in CI without flaky failures

### Remaining
- ❌ Event loop fixture usage still in 29 files
- ❌ Only 1 test file uses `@pytest.mark.asyncio`
- ❌ Conditional decorator workarounds in 13+ tool files
- ❌ Mixed sync/async patterns throughout codebase

## Success Criteria

1. ✅ All tests pass consistently in both local and CI environments
2. ✅ No custom event loop management code in test fixtures
3. ❌ Clear, consistent async/await patterns throughout the codebase
4. ✅ Updated documentation reflecting current best practices
5. ✅ No flaky tests hidden behind skip decorators
6. ❌ All async tests use `@pytest.mark.asyncio`
7. ❌ No remaining event_loop_fixture imports or usage

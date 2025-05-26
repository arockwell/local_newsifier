# Event Loop Stabilization - Remaining Work

## Overview

This document details the specific files and changes needed to complete the event loop stabilization effort. While the critical CI failures have been resolved, significant work remains to fully modernize async patterns throughout the codebase.

## Files Still Using Old Event Loop Patterns

### 1. Test Files Importing event_loop_fixture (28 files)

**API Tests (1 file)**
- `tests/api/test_main.py`

**Service Tests (4 files)**
- `tests/services/test_analysis_service.py`
- `tests/services/test_apify_service_schedules.py`
- `tests/services/test_entity_service.py`
- `tests/services/test_entity_service_extended.py`

**DI Provider Tests (4 files)**
- `tests/di/test_db_inspect_command_provider.py`
- `tests/di/test_file_writer_provider.py`
- `tests/di/test_rss_parser_provider.py`
- `tests/di/test_sentiment_analyzer_provider.py`

**Tool Tests (13 files)**
- `tests/tools/test_file_writer.py`
- `tests/tools/test_injectable_trend_reporter.py`
- `tests/tools/test_output_formatters.py`
- `tests/tools/test_rss_parser.py`
- `tests/tools/test_sentiment_analyzer.py`
- `tests/tools/test_sentiment_tracker.py`
- `tests/tools/test_trend_reporter.py`
- `tests/tools/test_web_scraper.py`
- `tests/tools/analysis/test_context_analyzer.py`
- `tests/tools/analysis/test_trend_analyzer.py`
- `tests/tools/extraction/test_entity_extractor.py`
- `tests/tools/resolution/test_entity_resolver.py`

**Flow Tests (7 files)**
- `tests/flows/entity_tracking_flow_test.py`
- `tests/flows/test_entity_tracking_flow_service.py`
- `tests/flows/test_news_pipeline_integration.py`
- `tests/flows/test_public_opinion_flow.py`
- `tests/flows/test_rss_scraping_flow.py`
- `tests/flows/test_trend_analysis_flow.py`
- `tests/flows/analysis/test_headline_trend_flow.py`

### 2. Current pytest.mark.asyncio Usage

**Only 1 file currently uses proper async marking:**
- `tests/tools/test_file_writer.py`

## Required Changes by File Type

### 1. Remove event_loop_fixture Imports

**Action Required:**
- Remove `from tests.fixtures.event_loop import event_loop_fixture`
- Remove `event_loop_fixture` from test function parameters
- For async tests, add `@pytest.mark.asyncio` decorator
- For sync tests that need to run async code, use `asyncio.run()` at the test level

**Example Transformation:**
```python
# Before
from tests.fixtures.event_loop import event_loop_fixture

def test_something(event_loop_fixture):
    with event_loop_fixture():
        result = some_sync_function()
        assert result == expected

# After
def test_something():
    result = some_sync_function()
    assert result == expected
```

### 2. Convert Mixed Sync/Async Tests

**Pattern to Find:**
- Tests using `event_loop_fixture` to run async code
- Tests with async operations but no `@pytest.mark.asyncio`

**Example Transformation:**
```python
# Before
def test_async_operation(event_loop_fixture):
    with event_loop_fixture():
        result = loop.run_until_complete(async_function())
        assert result == expected

# After
@pytest.mark.asyncio
async def test_async_operation():
    result = await async_function()
    assert result == expected
```

### 3. Update Mock Patterns

**For Async Dependencies:**
```python
# Use AsyncMock for async methods
from unittest.mock import AsyncMock

mock_service = MagicMock()
mock_service.async_method = AsyncMock(return_value=result)
```

## Priority Order

1. **High Priority - Core Components**
   - Service tests (4 files)
   - DI provider tests (4 files)
   - API tests (1 file)

2. **Medium Priority - Integration Tests**
   - Flow tests (7 files)
   - Tool integration tests

3. **Lower Priority - Unit Tests**
   - Individual tool tests (13 files)

## Testing Strategy

1. **Update One Component Type at a Time**
   - Start with services
   - Then DI providers
   - Then flows
   - Finally tools

2. **For Each File:**
   - Remove event_loop_fixture import
   - Identify async operations
   - Add @pytest.mark.asyncio where needed
   - Update mock patterns
   - Run tests to verify

3. **Validation:**
   - Run tests locally after each change
   - Check for any new warnings
   - Ensure CI passes

## Success Metrics

- [ ] 0 files importing event_loop_fixture
- [ ] All async tests use @pytest.mark.asyncio
- [ ] No asyncio.run() or loop.run_until_complete() in tests
- [ ] All tests pass in CI without warnings
- [ ] tests/fixtures/event_loop.py can be deleted

## Risks and Mitigation

1. **Risk:** Breaking existing tests
   - **Mitigation:** Update one file at a time and run tests immediately

2. **Risk:** Hidden async/sync boundary issues
   - **Mitigation:** Look for RuntimeError about event loops during testing

3. **Risk:** Mock compatibility issues
   - **Mitigation:** Use AsyncMock for async methods, regular Mock for sync

## Next Steps

1. Create a PR for Phase 4 focusing on service tests
2. Update 4 service test files to remove event_loop_fixture
3. Verify all service tests pass
4. Continue with DI provider tests
5. Repeat for remaining component types

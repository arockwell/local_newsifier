# Event Loop Stabilization - Next Steps

## Executive Summary

The event loop stabilization effort has successfully resolved the critical CI failures that were blocking development. The most problematic issues have been fixed, and tests now pass reliably in CI. However, significant cleanup work remains to fully modernize the async patterns throughout the codebase.

## What's Been Accomplished

### Phase 1-3: Critical Fixes ✅

1. **Removed Problematic Event Loop Fixture**
   - Deleted complex thread-local storage implementation
   - Replaced with simple, standard pytest fixture
   - CI tests now pass reliably

2. **Eliminated Flaky CI Skip Decorators**
   - Removed `@ci_skip_async` decorator
   - Removed `@ci_skip_injectable` decorator
   - All tests now run in CI without skipping

3. **Updated Documentation**
   - Removed outdated event loop fixture recommendations
   - Added modern pytest-asyncio best practices
   - Created comprehensive planning documents

## What Remains

### Phase 4: Complete Event Loop Fixture Removal 🔄

**28 test files** still import the old event_loop_fixture:
- 4 service tests
- 4 DI provider tests
- 13 tool tests
- 7 flow tests
- 1 API test

**Only 1 test file** currently uses `@pytest.mark.asyncio` properly.

### Phase 5: Full Async Pattern Adoption 📋

- Convert all async tests to use `@pytest.mark.asyncio`
- Remove all `asyncio.run()` and `loop.run_until_complete()` from tests
- Standardize async mock patterns using `AsyncMock`
- Update services and tools to be properly async

## Recommended Next Steps

### 1. Immediate Actions (This Week)

**Create PR for Service Tests (4 files):**
```bash
tests/services/test_analysis_service.py
tests/services/test_apify_service_schedules.py
tests/services/test_entity_service.py
tests/services/test_entity_service_extended.py
```

**For each file:**
1. Remove `from tests.fixtures.event_loop import event_loop_fixture`
2. Remove `event_loop_fixture` parameters
3. Add `@pytest.mark.asyncio` to async tests
4. Update mocks to use `AsyncMock` for async methods
5. Run tests to verify

### 2. Next Sprint (Week 2)

**Update DI Provider Tests (4 files):**
```bash
tests/di/test_db_inspect_command_provider.py
tests/di/test_file_writer_provider.py
tests/di/test_rss_parser_provider.py
tests/di/test_sentiment_analyzer_provider.py
```

### 3. Following Sprints

**Week 3:** Flow tests (7 files)
**Week 4:** Tool tests (13 files)
**Week 5:** Final cleanup and validation

## Success Metrics

- [ ] 0 imports of event_loop_fixture
- [ ] All async tests use @pytest.mark.asyncio
- [ ] No asyncio.run() in test code
- [ ] All tests pass without warnings
- [ ] Delete tests/fixtures/event_loop.py

## Risk Mitigation

1. **Test One Component Type at a Time**
   - Reduces risk of widespread breakage
   - Easier to identify and fix issues

2. **Run Tests After Each File Change**
   - Immediate feedback on changes
   - Prevents accumulation of errors

3. **Create Small, Focused PRs**
   - Easier to review
   - Simpler to revert if needed

## Long-term Benefits

1. **Simpler Test Code**
   - No complex event loop management
   - Standard pytest-asyncio patterns

2. **Better CI Reliability**
   - No flaky tests
   - Consistent behavior across environments

3. **Foundation for Async Migration**
   - Clean async test patterns
   - Ready for full async service conversion

## Resources

- [Event Loop Stabilization Plan](event-loop-stabilization.md)
- [Detailed Remaining Work](event-loop-remaining-work.md)
- [Async Migration Plan](convert_to_async.md)
- [Technical Debt Reduction](technical-debt-reduction.md)

## Questions?

If you encounter issues during the migration:
1. Check the pytest-asyncio documentation
2. Review the examples in CLAUDE.md
3. Ask in the team chat with specific error messages

# Test Consolidation Gameplan

## Objective
Reduce test duplication by 30-40% while maintaining or improving test coverage quality.

## Phase 1: Quick Wins (1-2 days)

### 1.1 Consolidate Entity Tracking Flow Tests
**Files to merge:**
- `tests/flows/entity_tracking_flow_test.py` (keep as main)
- `tests/flows/entity_tracking_flow_test_basic.py` (merge into main)
- `tests/flows/test_entity_tracking_flow_service.py` (extract unique tests)

**Actions:**
1. Keep error handling and state logging tests from service file
2. Use parameterized tests for variations
3. Remove duplicate initialization and process method tests
4. Expected reduction: ~400 lines

### 1.2 Merge CRUD Extended Tests
**Pattern to follow:**
```python
# Instead of separate files, use parameterized tests
@pytest.mark.parametrize("custom_params", [
    {"started_at": datetime.now() - timedelta(hours=2)},
    {"status": "failed", "error_message": "Test error"},
])
def test_create_processing_with_params(db_session, custom_params):
    # Single test handles all variations
```

**Files to merge:**
- `test_feed_processing_log_extended.py` → `test_feed_processing_log.py`
- `test_rss_feed_extended.py` → `test_rss_feed.py`

## Phase 2: Service Layer Consolidation (2-3 days)

### 2.1 Combine Service Test Files
**Priority targets:**
- Apify service tests (4 files → 1 file)
- Entity service tests (3 files → 1 file)
- News pipeline service tests (2 files → 1 file)

**Strategy:**
1. Create test classes for logical grouping:
```python
class TestApifyServiceCore:
    """Core functionality tests"""

class TestApifyServiceSchedules:
    """Schedule-specific tests"""

class TestApifyServiceEdgeCases:
    """Error handling and edge cases"""
```

### 2.2 Reduce Mock Complexity
**Create shared fixtures:**
```python
@pytest.fixture
def mock_entity_service_deps():
    """Standard mock setup for entity service."""
    return {
        "entity_crud": MagicMock(),
        "entity_extractor": MagicMock(),
        "context_analyzer": MagicMock(),
        # ... other common mocks
    }
```

## Phase 3: CLI Test Optimization (1-2 days)

### 3.1 Merge CLI Command Tests
**Consolidate:**
- `test_db.py` + `test_db_comprehensive.py` → `test_db_commands.py`
- `test_feeds.py` + `test_feeds_container.py` → `test_feed_commands.py`

### 3.2 Remove Injectable Tests
**As per migration plan:**
- Remove `test_injectable_*` files
- Replace with HTTP client tests
- Update conftest to remove injectable fixtures

## Phase 4: Tool Implementation Cleanup (1 day)

### 4.1 Merge Implementation Tests
**Pattern:**
- Keep main test file (e.g., `test_trend_analyzer.py`)
- Move unique tests from `_impl` files
- Use inheritance for shared test logic

## Phase 5: Integration Test Strategy (2 days)

### 5.1 Create Focused Integration Tests
**Replace heavily mocked tests with:**
```python
# tests/integration/test_article_processing.py
def test_full_article_processing_flow(test_db, test_article):
    """Test complete flow with real components."""
    # Minimal mocking, real database
```

### 5.2 Remove Redundant Unit Tests
- Identify tests that only verify mocking
- Keep tests that verify business logic
- Focus on behavior, not implementation

## Implementation Order

### Week 1:
1. **Day 1-2**: Phase 1 (Quick Wins)
   - Start with entity tracking flow consolidation
   - Merge CRUD extended tests

2. **Day 3-5**: Phase 2 (Service Layer)
   - Consolidate Apify service tests
   - Merge entity service tests
   - Create shared mock fixtures

### Week 2:
3. **Day 6-7**: Phase 3 (CLI Tests)
   - Merge CLI command tests
   - Remove injectable patterns

4. **Day 8**: Phase 4 (Tool Tests)
   - Consolidate tool implementation tests

5. **Day 9-10**: Phase 5 (Integration Tests)
   - Create integration test suite
   - Remove redundant unit tests

## Success Metrics

### Quantitative:
- [ ] Reduce test file count from 105 to ~75
- [ ] Decrease test execution time by 30%
- [ ] Maintain >90% code coverage
- [ ] Reduce total test LOC by ~2000 lines

### Qualitative:
- [ ] Clearer test organization
- [ ] Easier to find relevant tests
- [ ] Reduced maintenance burden
- [ ] Faster CI/CD pipeline

## Testing the Changes

After each consolidation:
1. Run full test suite: `make test`
2. Check coverage: `make test-coverage`
3. Verify CI passes on PR
4. Document any coverage gaps

## Rollback Strategy

1. Create feature branch for each phase
2. Keep original files until PR is merged
3. Tag repository before major changes
4. Document mapping of old → new test locations

## Notes

- Prioritize maintaining test coverage over reduction
- Keep tests that catch real bugs
- Consider test readability in consolidation
- Update CLAUDE.md files with new test patterns

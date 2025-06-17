# Code Redundancy Reduction Gameplan

## Overview

This gameplan outlines a systematic approach to reduce code redundancy and overtesting in the Local Newsifier codebase. The goal is to simplify from 5+ layers to 3 layers, reduce test count by 40-50%, and improve maintainability.

## Phase 1: Quick Wins (1-2 days)

### 1.1 Extract Common Utilities
Create `src/local_newsifier/utils/` module:

```python
# utils/url.py
def extract_source_from_url(url: str) -> str:
    """Extract source domain from URL."""
    parsed = urlparse(url)
    return parsed.netloc or "Unknown Source"

# utils/dates.py
def parse_date_safe(date_str: str) -> Optional[datetime]:
    """Safely parse various date formats."""
    # Consolidate date parsing logic
```

**Files to update:**
- `services/article_service.py` (remove duplicate URL parsing)
- `services/rss_feed_service.py` (use shared utilities)
- `cli/commands/feeds.py` (use shared utilities)

### 1.2 Create Generic State Model
Replace 5+ state models with one generic model:

```python
# models/processing_state.py
class ProcessingState(BaseState):
    processing_type: str  # "news_analysis", "entity_tracking", etc.
    status: ProcessingStatus
    data: Dict[str, Any]
    errors: List[str]
```

**Files to remove:**
- `models/state.py` (keep only base and generic)
- Individual state models in various modules

### 1.3 Remove Duplicate Error Handling
Create a single error handling context manager:

```python
# database/context.py
@contextmanager
def database_operation():
    """Handle common database errors."""
    try:
        yield
    except IntegrityError as e:
        # Handle
    except OperationalError as e:
        # Handle
```

Remove `@handle_database` decorator from individual services.

## Phase 2: CRUD Layer Simplification (2-3 days)

### 2.1 Eliminate Thin CRUD Wrappers

**Remove these CRUD classes entirely:**
- `CRUDAnalysisResult` (use `CRUDBase` directly)
- `CRUDEntityProfile` (use `CRUDBase` directly)
- `CRUDEntityMentionContext` (use `CRUDBase` directly)

**Merge into one EntityCRUD:**
- `CRUDEntity`
- `CRUDCanonicalEntity`
- `CRUDEntityRelationship`

### 2.2 Simplify CRUDArticle
Move timestamp logic to model default:

```python
# models/article.py
class Article(SQLModel, table=True):
    scraped_at: datetime = Field(default_factory=datetime.utcnow)
```

Remove custom `create()` method from `CRUDArticle`.

### 2.3 Update Tests
- Remove tests for deleted CRUD classes
- Update imports to use `CRUDBase` directly
- Reduce CRUD test coverage to only custom methods

## Phase 3: Service Layer Consolidation (3-4 days)

### 3.1 Merge Duplicate Processing Methods

In `EntityService`, remove `process_article_with_state()` and keep only `process_article_entities()`.

### 3.2 Remove Pass-through Methods

Delete these service methods that just wrap CRUD:
- `ArticleService.get_article()` - use CRUD directly
- `ArticleService.list_articles()` - use CRUD directly
- Similar methods in other services

### 3.3 Consolidate Article Creation

Create single article creation method:
```python
# services/article_service.py
def create_article(self, title: str, content: str, url: str,
                  source: Optional[str] = None, **kwargs) -> Article:
    """Single method for all article creation."""
    if not source:
        source = extract_source_from_url(url)
    # Common creation logic
```

Remove:
- `create_article_from_rss_entry()`
- `create_article_from_content()`
- Direct creation in CLI commands

## Phase 4: Remove Flow Layer (2-3 days)

### 4.1 Merge Flows into Services

Move useful logic from flows into services:
- `NewsPipelineFlow` → `NewsPipelineService`
- `EntityTrackingFlow` → `EntityService`
- `TrendAnalysisFlow` → `AnalysisService`

### 4.2 Delete Flow Files
Remove entire `flows/` directory after merging logic.

### 4.3 Update Imports
Update all imports from flows to services.

## Phase 5: Test Consolidation (3-4 days)

### 5.1 Remove Redundant Test Files

Delete test files for removed components:
- Tests for deleted CRUD classes
- Tests for removed flow layer
- Tests for pass-through service methods

### 5.2 Consolidate Integration Tests

Create focused integration tests that test full paths:
```python
# tests/integration/test_article_processing.py
def test_article_creation_and_processing():
    """Test complete article processing path."""
    # Test from API/CLI to database
    # Don't test each layer separately
```

### 5.3 Reduce Unit Test Granularity

For remaining components:
- Test only public interfaces
- Skip testing simple getters/setters
- Focus on business logic

## Phase 6: CLI/API Simplification (2 days)

### 6.1 Standardize Processing Paths

Remove duplicate processing in CLI:
- Delete `direct_process_article()` in `cli/commands/feeds.py`
- Use service methods consistently

### 6.2 Simplify Dependency Injection

For CLI migration to HTTP calls:
- Remove complex DI setup
- Use simple HTTP client calls to API

## Implementation Order

1. **Week 1**: Phases 1-2 (Quick wins + CRUD simplification)
2. **Week 2**: Phases 3-4 (Service consolidation + Flow removal)
3. **Week 3**: Phases 5-6 (Test consolidation + CLI/API cleanup)

## Success Metrics

### Code Metrics
- [ ] Reduce total source files by 30%
- [ ] Reduce lines of code by 35%
- [ ] Reduce number of classes by 40%

### Test Metrics
- [ ] Reduce test files by 40%
- [ ] Reduce test execution time by 30%
- [ ] Maintain 85%+ coverage on business logic

### Architecture Metrics
- [ ] From 5+ layers to 3 layers
- [ ] Single article processing path
- [ ] No duplicate error handling

## Risk Mitigation

1. **Create branch for each phase** - Easy rollback if needed
2. **Run full test suite after each change** - Catch regressions early
3. **Update documentation** - Keep architecture docs current
4. **Incremental deployment** - Deploy after each phase

## Rollback Plan

Each phase is designed to be atomic. If issues arise:
1. Revert the phase's commits
2. Analyze what went wrong
3. Adjust plan and retry

## Post-Implementation

After completion:
1. Update architecture documentation
2. Create coding guidelines to prevent future redundancy
3. Set up architecture decision records (ADRs)
4. Regular code review focus on avoiding new redundancy

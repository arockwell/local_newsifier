# Async Code Patterns Analysis - Local Newsifier

## Executive Summary

The Local Newsifier codebase exhibits significant architectural confusion around async/sync patterns, leading to event loop issues, particularly in tests. The primary issues stem from:

1. **Mixed Async/Sync Architecture**: FastAPI endpoints are async but call synchronous services and database operations
2. **Event Loop Conflicts**: fastapi-injectable requires event loops even for synchronous code, causing test failures
3. **Inconsistent Patterns**: No clear architectural decision on where async should be used
4. **Test Fragility**: Heavy reliance on CI skip decorators to avoid async issues

## Current State Analysis

### 1. API Layer (FastAPI)

#### Observations
- **Mixed async/sync endpoints**: Some endpoints are `async def` while others are regular `def`
- **Synchronous database calls in async contexts**: Async endpoints make blocking database calls
- **No async database drivers**: Using synchronous SQLModel/SQLAlchemy with psycopg2 (not asyncpg)

#### Examples

```python
# main.py - PROBLEMATIC PATTERN
@app.get("/", response_class=HTMLResponse)
async def root(request: Request, templates: Jinja2Templates = Depends(get_templates)):
    # ISSUE: Async endpoint making synchronous database calls
    with SessionManager() as session:  # Blocking I/O in async context
        articles = article_crud_instance.get_by_date_range(
            session, start_date=start_date, end_date=end_date
        )
```

```python
# webhooks.py - CORRECT PATTERN
@router.post("/apify", response_model=ApifyWebhookResponse)
async def apify_webhook(payload: ApifyWebhookPayload) -> ApifyWebhookResponse:
    # Pure async endpoint with no database calls
    logger.info(f"Received Apify webhook: {payload.eventType}")
    # Just validation and logging, no blocking I/O
```

### 2. Dependency Injection Layer

#### Issues with fastapi-injectable
- **Event loop requirement**: The `@injectable` decorator uses asyncio internally even for sync code
- **Conditional decorator pattern**: Workaround to avoid event loop issues in tests

```python
# Problematic pattern in tools
try:
    if not os.environ.get('PYTEST_CURRENT_TEST'):
        from fastapi_injectable import injectable
        OpinionVisualizerTool = injectable(use_cache=False)(OpinionVisualizerTool)
except (ImportError, Exception):
    pass
```

#### Provider Functions
- All providers are synchronous functions
- `use_cache=False` everywhere for safety, but adds overhead
- No async providers despite FastAPI's async nature

### 3. Service Layer

#### Current State
- **All services are synchronous**: No async methods in any service class
- **Session factory pattern**: Uses `session_factory` callable for lazy session creation
- **No async/await**: Services don't support async operations

```python
# article_service.py
@injectable(use_cache=False)
class ArticleService:
    def process_article(self, url: str, content: str, title: str, published_at: datetime):
        with self.session_factory() as session:  # Synchronous context manager
            # All database operations are synchronous
```

### 4. Database Layer

#### Issues
- **Synchronous only**: Using SQLModel with synchronous SQLAlchemy core
- **No async session support**: `get_session()` is a synchronous generator
- **Blocking I/O**: All database queries block the event loop when called from async contexts

```python
# engine.py
def get_session() -> Generator[Session, None, None]:
    """Get a database session."""
    engine = get_engine()
    with Session(engine) as session:
        yield session  # Synchronous yield
```

### 5. Test Infrastructure

#### Major Issues
- **Event loop conflicts**: Tests fail due to "Event loop is closed" errors
- **CI-specific failures**: Tests pass locally but fail in CI
- **Heavy use of skip decorators**: `ci_skip_async`, `ci_skip_injectable`

```python
# Common test pattern to avoid issues
@ci_skip_injectable
class TestOpinionVisualizerImplementation:
    def test_something(self, event_loop_fixture):
        # Test implementation
```

#### Event Loop Fixture Complexity
```python
# event_loop.py - Complex workarounds
@contextmanager
def _event_loop_context():
    # Thread-local storage for event loops
    # Multiple fallback strategies
    # Complex cleanup logic
```

## Root Causes

### 1. Architectural Mismatch
- **FastAPI is async-first**: Designed for async operations
- **Database layer is sync-only**: SQLModel/SQLAlchemy without async support
- **No clear boundary**: Async and sync code mixed without clear separation

### 2. Dependency Injection Issues
- **fastapi-injectable internals**: Uses asyncio even for sync dependencies
- **No sync-only mode**: Can't opt out of async behavior
- **Test environment conflicts**: Different event loop behavior in tests vs runtime

### 3. Missing Async Infrastructure
- **No async database driver**: Using psycopg2 instead of asyncpg
- **No async ORM configuration**: SQLModel not configured for async
- **No async service layer**: Services can't be awaited

## Impact Assessment

### Performance
- **Thread pool exhaustion**: Sync database calls in async endpoints use thread pool
- **Suboptimal concurrency**: Can't handle concurrent requests efficiently
- **Increased latency**: Blocking I/O prevents other requests from processing

### Reliability
- **Test instability**: Frequent test failures in CI
- **Deployment risks**: Async issues may manifest differently in production
- **Debugging difficulty**: Event loop errors are hard to trace

### Maintainability
- **Complex workarounds**: Conditional decorators, event loop fixtures
- **Inconsistent patterns**: Developers unsure when to use async
- **Technical debt**: Skip decorators hide underlying issues

## Best Practices Violations

### 1. FastAPI Best Practices
- ❌ **Blocking I/O in async endpoints**: Should use async database drivers
- ❌ **Mixed async/sync endpoints**: Should be consistent
- ❌ **No async dependency injection**: Should use async providers for async endpoints

### 2. Python Async Best Practices
- ❌ **No clear async boundary**: Should separate async and sync layers
- ❌ **Event loop management**: Should let framework handle event loops
- ❌ **Thread safety**: Sharing sync resources across async contexts

### 3. Testing Best Practices
- ❌ **Environment-specific tests**: Tests should pass in all environments
- ❌ **Skip decorator overuse**: Should fix root cause, not skip tests
- ❌ **Complex fixtures**: Event loop fixtures indicate architectural issues

## Comprehensive Solution Recommendations

### Option 1: Full Async Migration (Recommended)

#### Changes Required
1. **Database Layer**
   ```python
   # Use async SQLModel/SQLAlchemy
   from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
   from sqlmodel.ext.asyncio.session import AsyncSession

   async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
       async with AsyncSession(async_engine) as session:
           yield session
   ```

2. **Service Layer**
   ```python
   @injectable(use_cache=False)
   class ArticleService:
       async def process_article(self, url: str, content: str, ...):
           async with self.session_factory() as session:
               article = await self.article_crud.create_async(session, ...)
   ```

3. **CRUD Layer**
   ```python
   class CRUDBase:
       async def get_async(self, db: AsyncSession, id: int):
           result = await db.execute(select(self.model).where(self.model.id == id))
           return result.scalar_one_or_none()
   ```

4. **API Layer**
   ```python
   @app.get("/")
   async def root(
       session: Annotated[AsyncSession, Depends(get_async_session)]
   ):
       articles = await article_service.get_recent_articles(session)
   ```

### Option 2: Clear Sync/Async Separation

#### Changes Required
1. **Sync-only endpoints for database operations**
   ```python
   @app.get("/", response_class=HTMLResponse)
   def root(request: Request, session: Session = Depends(get_session)):
       # All database operations remain synchronous
       articles = article_crud.get_by_date_range(session, ...)
   ```

2. **Async-only for I/O operations**
   ```python
   @app.post("/scrape")
   async def scrape_url(url: str):
       # Only for external API calls, not database
       async with httpx.AsyncClient() as client:
           response = await client.get(url)
   ```

3. **Remove fastapi-injectable** (if choosing sync approach)
   - Use plain FastAPI dependency injection
   - Avoid event loop complications

### Option 3: Minimal Changes (Not Recommended)

#### Quick Fixes
1. **Use synchronous endpoints everywhere**
   ```python
   # Change all async def to def in routers
   @app.get("/")
   def root(...):  # Remove async
   ```

2. **Fix test infrastructure**
   - Remove conditional decorators
   - Use pytest-asyncio properly
   - Don't skip tests in CI

## Implementation Plan

### Phase 1: Stabilize Current System (1-2 weeks)
1. Convert all endpoints to synchronous (Option 3)
2. Remove conditional decorators
3. Fix event loop fixtures
4. Ensure all tests pass in CI

### Phase 2: Architectural Decision (1 week)
1. Team discussion on async vs sync
2. Performance benchmarking
3. Choose Option 1 or Option 2

### Phase 3: Implementation (4-6 weeks)
1. Implement chosen architecture
2. Update all affected components
3. Comprehensive testing
4. Documentation updates

### Phase 4: Migration (2-3 weeks)
1. Gradual rollout
2. Monitor performance
3. Fix any issues
4. Remove old code

## Updated Documentation Recommendations

### CLAUDE.md Updates

Add new section:

```markdown
## Async/Sync Architecture Guidelines

### Current State (Synchronous)
- All database operations are synchronous
- Use regular `def` for endpoints that access the database
- Use `async def` only for endpoints that make external API calls

### Database Access Pattern
```python
# CORRECT - Synchronous endpoint for database access
@app.get("/items/{item_id}")
def get_item(
    item_id: int,
    session: Session = Depends(get_session)
):
    return item_service.get_item(session, item_id)

# INCORRECT - Don't use async with sync database
@app.get("/items/{item_id}")
async def get_item(...):  # This will cause issues
```

### Testing Guidelines
- Always include event_loop_fixture for tests touching injectable components
- Never use conditional decorators on classes
- If a test fails in CI, fix the root cause, don't skip it
```

## Conclusion

The Local Newsifier codebase has significant architectural issues around async/sync patterns. The mixing of async FastAPI endpoints with synchronous database operations, combined with fastapi-injectable's event loop requirements, creates a fragile system with frequent test failures.

**UPDATE**: The project has decided to migrate to sync-only patterns. The previously recommended async approach (Option 1) has been deprecated due to production crashes caused by async/sync mixing. The sync-only approach provides better stability and easier maintenance.

The current approach of mixing patterns and using workarounds is unsustainable and should be addressed as a priority.

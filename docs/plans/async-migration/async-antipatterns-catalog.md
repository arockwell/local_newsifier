# Async Antipatterns Catalog - Local Newsifier

This document catalogs specific antipatterns found in the Local Newsifier codebase related to async/sync code mixing and event loop management.

## Antipattern 1: Blocking I/O in Async Context

### Description
Performing synchronous, blocking database operations inside async functions, which blocks the event loop and defeats the purpose of async.

### Examples Found

#### main.py (lines 78-128)
```python
@app.get("/", response_class=HTMLResponse)
async def root(
    request: Request,
    templates: Jinja2Templates = Depends(get_templates)
):
    # ANTIPATTERN: Synchronous database operations in async function
    from local_newsifier.database.engine import SessionManager

    with SessionManager() as session:  # Blocking context manager
        articles = article_crud_instance.get_by_date_range(
            session,
            start_date=start_date,
            end_date=end_date
        )  # Blocking database query
```

### Impact
- Blocks the entire event loop while waiting for database
- Other concurrent requests cannot be processed
- Negates benefits of async FastAPI

### Correct Pattern
```python
# Option 1: Make it synchronous
@app.get("/", response_class=HTMLResponse)
def root(request: Request, session: Session = Depends(get_session)):
    articles = article_crud_instance.get_by_date_range(session, ...)

# Option 2: Use async database
@app.get("/", response_class=HTMLResponse)
async def root(request: Request, session: AsyncSession = Depends(get_async_session)):
    articles = await article_crud_instance.get_by_date_range_async(session, ...)
```

## Antipattern 2: Conditional Decorator Application

### Description
Applying decorators conditionally based on environment variables to work around event loop issues.

### Examples Found

#### opinion_visualizer.py (pattern repeated in multiple files)
```python
# ANTIPATTERN: Conditional decorator application
try:
    if not os.environ.get('PYTEST_CURRENT_TEST'):
        from fastapi_injectable import injectable
        OpinionVisualizerTool = injectable(use_cache=False)(OpinionVisualizerTool)
except (ImportError, Exception):
    pass
```

### Impact
- Different behavior in test vs production
- Hidden bugs that only appear in certain environments
- Increases complexity and reduces predictability

### Correct Pattern
```python
# Always apply decorators consistently
@injectable(use_cache=False)
class OpinionVisualizerTool:
    def __init__(self, session: Optional[Session] = None):
        self.session = session
```

## Antipattern 3: Mixed Sync/Async Dependency Injection

### Description
Using synchronous providers with async frameworks, causing event loop conflicts.

### Examples Found

#### dependencies.py (lines 57-97)
```python
def get_session() -> Generator[Session, None, None]:
    """Get a database session."""
    from local_newsifier.di.providers import get_session as get_injectable_session
    # ANTIPATTERN: Sync generator in async context
    yield from get_injectable_session()

def get_article_service() -> ArticleService:
    """Get the article service."""
    from local_newsifier.database.engine import get_session
    # ANTIPATTERN: Creating session inside provider
    with next(get_session()) as session:
        return get_injectable_article_service(session=session)
```

### Impact
- Event loop conflicts when FastAPI tries to handle these
- Inconsistent session lifecycle management
- Potential for session leaks

### Correct Pattern
```python
# For async endpoints
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSession(async_engine) as session:
        yield session

# For sync endpoints
def get_session() -> Generator[Session, None]:
    with Session(engine) as session:
        yield session
```

## Antipattern 4: Thread-Local Event Loop Management

### Description
Complex event loop management with thread-local storage and multiple fallback strategies.

### Examples Found

#### event_loop.py (lines 26-104)
```python
# ANTIPATTERN: Complex event loop management
_thread_local = threading.local()

@contextmanager
def _event_loop_context():
    try:
        current_loop = asyncio.get_running_loop()
        _thread_local.loop = current_loop
        yield current_loop
        return
    except RuntimeError:
        pass
    # Multiple fallback strategies...
```

### Impact
- Masks underlying architectural issues
- Fragile and environment-dependent
- Difficult to debug when it fails

### Correct Pattern
```python
# Let the framework manage event loops
# Don't create custom event loop management
@pytest.fixture
def async_client():
    app = create_app()
    with TestClient(app) as client:
        yield client
```

## Antipattern 5: CI-Specific Test Skipping

### Description
Skipping tests in CI environments due to event loop issues rather than fixing root cause.

### Examples Found

#### ci_skip_config.py
```python
ci_skip_async = lambda func=None: ci_skip("Skipped in CI due to async event loop issues")(func)
ci_skip_injectable = lambda func=None: ci_skip("Skipped in CI due to fastapi-injectable issues")(func)
```

#### Usage in tests
```python
@ci_skip_injectable
class TestOpinionVisualizerImplementation:
    # Tests that only run locally, not in CI
```

### Impact
- False confidence from local test passes
- Production issues not caught in CI
- Technical debt accumulation

### Correct Pattern
```python
# Fix the underlying issue, don't skip tests
class TestOpinionVisualizerImplementation:
    def test_something(self):
        # Test should work in all environments
```

## Antipattern 6: Sync Database Operations with Async Decorators

### Description
Using the `@injectable` decorator which requires async context on classes that perform synchronous database operations.

### Examples Found

#### services/article_service.py
```python
@injectable(use_cache=False)  # Requires event loop
class ArticleService:
    def process_article(self, url: str, ...):  # Sync method
        with self.session_factory() as session:  # Sync context manager
            # Synchronous database operations
```

### Impact
- Event loop required even for sync operations
- Test complications with event loop management
- Performance overhead from async machinery for sync code

### Correct Pattern
```python
# Option 1: Remove injectable if staying sync
class ArticleService:
    def __init__(self, session_factory):
        self.session_factory = session_factory

# Option 2: Make it truly async
@injectable(use_cache=False)
class ArticleService:
    async def process_article(self, url: str, ...):
        async with self.session_factory() as session:
            # Async database operations
```

## Antipattern 7: Event Loop Fixture Proliferation

### Description
Multiple overlapping event loop fixtures trying to solve the same problem.

### Examples Found

#### Multiple fixture files
```python
# conftest_injectable.py
@pytest.fixture
def event_loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()

# fixtures/event_loop.py
@pytest.fixture
def event_loop_fixture():
    with _event_loop_context() as loop:
        yield loop

# fixtures/event_loop.py
@pytest.fixture
def injectable_service_fixture(event_loop_fixture):
    def get_injected_service(service_factory, *args, **kwargs):
        with _event_loop_context() as loop:
            # More complex logic...
```

### Impact
- Confusion about which fixture to use
- Potential conflicts between fixtures
- Maintenance burden

### Correct Pattern
```python
# Use pytest-asyncio's built-in fixture
# conftest.py
pytest_plugins = ['pytest_asyncio']

# Then use standard pytest.mark.asyncio
@pytest.mark.asyncio
async def test_async_function():
    result = await async_function()
    assert result == expected
```

## Summary of Antipatterns

1. **Blocking I/O in Async Context**: Sync database calls in async endpoints
2. **Conditional Decorator Application**: Environment-based decorator logic
3. **Mixed Sync/Async Dependency Injection**: Sync providers in async framework
4. **Thread-Local Event Loop Management**: Complex custom event loop handling
5. **CI-Specific Test Skipping**: Hiding problems instead of fixing them
6. **Sync Operations with Async Decorators**: Mismatch between decorator and implementation
7. **Event Loop Fixture Proliferation**: Multiple competing solutions for same problem

## Root Cause
All these antipatterns stem from a fundamental architectural mismatch: trying to use synchronous database operations with an async web framework (FastAPI) and an async-aware dependency injection system (fastapi-injectable).

## Solution
Choose one consistent approach:
1. **Go fully async**: Async database, async services, async everywhere
2. **Stay fully sync**: Use sync endpoints for database operations, async only for external I/O
3. **Clear separation**: Sync endpoints for database, async endpoints for external APIs

The current mixed approach is the source of all these antipatterns and should be resolved.

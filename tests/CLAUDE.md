# Local Newsifier Testing Guide

This guide documents testing patterns and best practices for the Local Newsifier project.

## Test Organization

Tests mirror the source code structure:
- `api/` - FastAPI endpoint tests
- `cli/` - Command-line interface tests
- `crud/` - Database CRUD operation tests
- `services/` - Business logic service tests
- `tools/` - Utility tool tests
- `flows/` - Workflow orchestration tests
- `models/` - Data model tests
- `di/` - Dependency injection provider tests
- `errors/` - Error handling tests
- `integration/` - Integration tests
- `examples/` - Example test patterns with documentation

## Key Testing Patterns

### 1. Database Testing

Use SQLite in-memory database for fast test execution:
```python
@pytest.fixture(scope="session")
def engine():
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    yield engine
    SQLModel.metadata.drop_all(engine)
```

Always use function-scoped sessions for test isolation:
```python
@pytest.fixture
def session(engine):
    with Session(engine) as session:
        yield session
        session.rollback()
```

### 2. Dependency Injection Testing

Use the mock manager pattern for injectable dependencies:
```python
@pytest.fixture
def mock_injectable_dependencies(monkeypatch):
    manager = MockManager(monkeypatch)
    manager.create_common_mocks()
    return manager
```

Direct instantiation pattern for service testing:
```python
def test_service_method():
    mock_crud = MagicMock(spec=ArticleCRUD)
    service = ArticleService(
        article_crud=mock_crud,
        session_factory=lambda: MagicMock()
    )
    # Test service methods
```

### 3. Async Testing

Use pytest-asyncio's built-in event loop handling (event loop stabilization has been completed):
```python
@pytest.mark.asyncio
async def test_async_function():
    result = await async_function()
    assert result == expected
```

For testing async database operations:
```python
@pytest.mark.asyncio
async def test_async_crud_operation():
    # Use async session fixture
    async with get_async_session() as session:
        crud = AsyncCRUDArticle(Article)
        article = await crud.create(session, Article(title="Test"))
        assert article.id is not None
```

### 4. Mocking External Dependencies

Always mock external services:
```python
@patch('local_newsifier.services.apify_service.ApifyClient')
def test_apify_integration(mock_client):
    mock_client.return_value.actor.return_value.call.return_value = {
        "id": "test-run-id",
        "status": "SUCCEEDED"
    }
    # Test code
```

### 5. FastAPI Testing

Use TestClient for endpoint testing:
```python
from fastapi.testclient import TestClient

def test_endpoint(mock_injectable_dependencies):
    # Mock dependencies
    mock_injectable_dependencies.patch_provider(
        "get_article_service",
        mock_injectable_dependencies.mocks["article_service"]
    )

    client = TestClient(app)
    response = client.get("/api/articles")
    assert response.status_code == 200
```

## Best Practices

### DO:
- Use AAA (Arrange-Act-Assert) pattern
- Create descriptive test names: `test_<component>_<scenario>`
- Test both success and error cases
- Use fixtures for reusable test data
- Mock all external dependencies
- Keep tests focused on a single behavior
- Use function-scoped fixtures for mutable data

### DON'T:
- Don't carry SQLModel objects between sessions
- Don't mix sync and async patterns in the same test
- Don't use session-scoped fixtures for mutable data
- Don't skip mocking external services
- Don't write tests that depend on test execution order

## Common Fixtures

### Database Fixtures
- `engine` - Test database engine (session-scoped)
- `session` - Database session (function-scoped)
- `sample_article_data` - Sample article data dict
- `create_article` - Creates test article in database
- `create_entity` - Creates test entity in database

### Mock Fixtures
- `mock_injectable_dependencies` - Injectable dependency manager
- `mock_sentiment_analyzer` - Mocked sentiment analyzer
- `mock_entity_extractor` - Mocked entity extractor
- `mock_web_scraper` - Mocked web scraper

### Utility Fixtures
- `run_async` - Helper for running async code in sync tests
- `event_loop` - Centralized async event loop

## CI-Specific Considerations

The event loop stabilization has been completed and flaky CI skip decorators have been removed. All async tests should now run reliably in CI without special handling.

## Testing Services with Dependencies

When testing services that use dependency injection:

1. Create mocks for all dependencies
2. Instantiate the service directly with mocks
3. Test the service methods
4. Verify mock interactions

Example:
```python
def test_article_service_create():
    # Arrange
    mock_crud = MagicMock(spec=ArticleCRUD)
    mock_crud.create.return_value = Article(id=1, title="Test")

    service = ArticleService(
        article_crud=mock_crud,
        session_factory=lambda: MagicMock()
    )

    # Act
    result = service.create_article({"title": "Test"})

    # Assert
    assert result.id == 1
    mock_crud.create.assert_called_once()
```

## Testing Async Code

For async code testing:
1. Mark test with `@pytest.mark.asyncio`
2. Use `async def` for test function
3. Use `await` for async calls
4. Mock async dependencies with `AsyncMock`

### Testing Async Services

Example async service test:
```python
@pytest.mark.asyncio
async def test_async_webhook_service():
    # Mock async session
    mock_session = MagicMock()
    mock_session.execute = AsyncMock()
    mock_session.add = MagicMock()
    mock_session.flush = AsyncMock()
    mock_session.commit = AsyncMock()

    # Create service
    service = ApifyWebhookServiceAsync(session=mock_session)

    # Test async method
    result = await service.process_webhook({"eventType": "ACTOR.RUN.SUCCEEDED"})

    assert result["status"] == "processed"
    mock_session.flush.assert_awaited_once()
```

### Testing Async CRUD Operations

```python
@pytest.mark.asyncio
async def test_async_crud_get_by_url():
    # Setup async in-memory database
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    async with AsyncSession(engine) as session:
        # Create test data
        crud = AsyncCRUDArticle(Article)
        article = Article(title="Test", url="https://test.com")
        created = await crud.create(session, article)
        await session.commit()

        # Test get_by_url
        found = await crud.get_by_url(session, "https://test.com")
        assert found is not None
        assert found.title == "Test"
```

### Mocking Async Dependencies

```python
from unittest.mock import AsyncMock, MagicMock

@pytest.mark.asyncio
async def test_with_async_mocks():
    # Mock async external API
    mock_client = MagicMock()
    mock_client.fetch = AsyncMock(return_value={"data": "test"})

    # Mock async database operation
    mock_crud = MagicMock()
    mock_crud.get = AsyncMock(return_value=Article(id=1, title="Test"))

    # Use in service
    service = MyAsyncService(client=mock_client, crud=mock_crud)
    result = await service.process(1)

    # Verify async calls
    mock_client.fetch.assert_awaited_with("https://api.example.com/1")
    mock_crud.get.assert_awaited_with(1)
```

## Running Tests

```bash
# Run all tests in parallel
make test

# Run tests serially (for debugging)
make test-serial

# Run with coverage
make test-coverage

# Run specific test file
pytest tests/services/test_article_service.py

# Run with verbose output
pytest -v tests/

# Run only marked tests
pytest -m "not ci_skip"
```

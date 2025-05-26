# Testing Strategy for FastAPI-Injectable Migration

This document outlines the testing approach for migrating away from FastAPI-Injectable, addressing current pain points and establishing new patterns.

## Current Testing Challenges

### 1. Event Loop Conflicts
```python
# Previous problem: Tests failed with event loop errors (NOW RESOLVED)
# The custom event_loop_fixture has been removed in favor of pytest-asyncio

@pytest.mark.asyncio
async def test_with_injectable():
    # Tests now work consistently in both local and CI environments
    result = await async_function()
    assert result == expected
```

### 2. Complex Mocking
```python
# Current: Elaborate mocking setup
@pytest.fixture
def patch_injectable_dependencies(monkeypatch):
    mock_service = Mock()
    monkeypatch.setattr("local_newsifier.di.providers.get_service", lambda: mock_service)
    return {"service": mock_service}
```

### 3. Inconsistent Test Patterns
- Some tests use `TestClient`
- Some tests use direct service instantiation
- Some tests patch providers
- Some tests override dependencies

## New Testing Approach

### 1. Service Testing (Post-Migration)

#### Unit Tests
```python
# test_article_service.py
import pytest
from unittest.mock import Mock, AsyncMock
from local_newsifier.services.article_service import ArticleService

class TestArticleService:
    """Test article service without any DI framework."""

    @pytest.fixture
    def mock_article_crud(self):
        """Mock CRUD dependency."""
        mock = Mock()
        mock.get = AsyncMock()
        mock.create = AsyncMock()
        mock.update = AsyncMock()
        mock.delete = AsyncMock()
        return mock

    @pytest.fixture
    def article_service(self, mock_article_crud):
        """Create service with mocked dependencies."""
        return ArticleService(article_crud=mock_article_crud)

    @pytest.mark.asyncio
    async def test_get_article(self, article_service, mock_article_crud):
        # Setup
        mock_article = {"id": 1, "title": "Test"}
        mock_article_crud.get.return_value = mock_article

        # Execute
        mock_session = Mock()
        result = await article_service.get_article(mock_session, 1)

        # Verify
        assert result == mock_article
        mock_article_crud.get.assert_called_once_with(mock_session, 1)

    @pytest.mark.asyncio
    async def test_process_multiple_articles(self, article_service, mock_article_crud):
        # Test concurrent processing
        urls = ["http://example1.com", "http://example2.com"]
        mock_session = Mock()

        # Mock responses
        mock_article_crud.create.side_effect = [
            {"id": 1, "url": urls[0]},
            {"id": 2, "url": urls[1]}
        ]

        # Execute
        results = await article_service.process_multiple_urls(mock_session, urls)

        # Verify
        assert len(results) == 2
        assert mock_article_crud.create.call_count == 2
```

#### Integration Tests
```python
# test_article_service_integration.py
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from local_newsifier.services.article_service import ArticleService
from local_newsifier.crud.article import ArticleCRUD

@pytest.fixture
async def async_test_session():
    """Provide real async test database session."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSession(engine) as session:
        yield session

    await engine.dispose()

@pytest.mark.asyncio
async def test_article_service_integration(async_test_session):
    """Test service with real database."""
    # Create service with real dependencies
    article_crud = ArticleCRUD()
    service = ArticleService(article_crud=article_crud)

    # Test full flow
    article_data = {
        "title": "Integration Test",
        "url": "http://example.com",
        "content": "Test content"
    }

    # Create
    created = await service.create_article(async_test_session, article_data)
    assert created.id is not None

    # Retrieve
    retrieved = await service.get_article(async_test_session, created.id)
    assert retrieved.title == "Integration Test"

    # Update
    updated = await service.update_article(
        async_test_session,
        created.id,
        {"title": "Updated Title"}
    )
    assert updated.title == "Updated Title"
```

### 2. API Endpoint Testing

#### Using TestClient
```python
# test_article_endpoints.py
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, AsyncMock

from local_newsifier.api.main import app
from local_newsifier.api.dependencies import get_article_service, get_session

@pytest.fixture
def mock_article_service():
    """Mock article service for testing."""
    mock = Mock()
    mock.get_article = AsyncMock()
    mock.create_article = AsyncMock()
    mock.list_articles = AsyncMock()
    return mock

@pytest.fixture
def mock_session():
    """Mock database session."""
    return Mock()

@pytest.fixture
def client(mock_article_service, mock_session):
    """Test client with mocked dependencies."""
    app.dependency_overrides[get_article_service] = lambda: mock_article_service
    app.dependency_overrides[get_session] = lambda: mock_session

    with TestClient(app) as client:
        yield client

    # Clear overrides
    app.dependency_overrides.clear()

def test_get_article_endpoint(client, mock_article_service):
    # Setup
    mock_article = {"id": 1, "title": "Test Article"}
    mock_article_service.get_article.return_value = mock_article

    # Execute
    response = client.get("/articles/1")

    # Verify
    assert response.status_code == 200
    assert response.json() == mock_article

def test_create_article_endpoint(client, mock_article_service, mock_session):
    # Setup
    article_data = {"title": "New Article", "url": "http://example.com"}
    mock_article_service.create_article.return_value = {**article_data, "id": 1}

    # Execute
    response = client.post("/articles", json=article_data)

    # Verify
    assert response.status_code == 201
    assert response.json()["id"] == 1
    mock_article_service.create_article.assert_called_once()
```

#### Async Client Testing
```python
# test_article_endpoints_async.py
import pytest
from httpx import AsyncClient
from local_newsifier.api.main import app

@pytest.mark.asyncio
async def test_article_endpoints_async():
    """Test endpoints with async client."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Create article
        create_response = await client.post(
            "/articles",
            json={"title": "Async Test", "url": "http://example.com"}
        )
        assert create_response.status_code == 201
        article_id = create_response.json()["id"]

        # Get article
        get_response = await client.get(f"/articles/{article_id}")
        assert get_response.status_code == 200
        assert get_response.json()["title"] == "Async Test"
```

### 3. CLI Testing

#### HTTP Client Testing
```python
# test_cli_client.py
import pytest
from unittest.mock import Mock, patch
from local_newsifier.cli.client import CLIClient

class TestCLIClient:
    @pytest.fixture
    def mock_httpx_client(self):
        with patch("httpx.Client") as mock:
            yield mock

    def test_list_articles(self, mock_httpx_client):
        # Setup
        mock_response = Mock()
        mock_response.json.return_value = [{"id": 1, "title": "Test"}]
        mock_httpx_client.return_value.get.return_value = mock_response

        # Execute
        client = CLIClient()
        result = client.list_articles()

        # Verify
        assert result == [{"id": 1, "title": "Test"}]
        mock_httpx_client.return_value.get.assert_called_with(
            "/articles",
            params={"skip": 0, "limit": 100}
        )
```

#### CLI Command Testing
```python
# test_article_commands.py
from typer.testing import CliRunner
from local_newsifier.cli.commands.articles import app

runner = CliRunner()

def test_list_command(mock_cli_client):
    """Test list command without any DI complexity."""
    # Mock the HTTP client
    mock_cli_client.list_articles.return_value = [
        {"id": 1, "title": "Article 1"},
        {"id": 2, "title": "Article 2"}
    ]

    # Run command
    result = runner.invoke(app, ["list"])

    # Verify
    assert result.exit_code == 0
    assert "Article 1" in result.output
    assert "Article 2" in result.output
```

### 4. Performance Testing

```python
# test_performance.py
import pytest
import asyncio
import time
from local_newsifier.services.article_service import ArticleService

@pytest.mark.asyncio
async def test_concurrent_performance(article_service, mock_session):
    """Test that async improves performance."""
    urls = [f"http://example{i}.com" for i in range(10)]

    # Time concurrent processing
    start = time.time()
    await article_service.process_multiple_urls(mock_session, urls)
    async_duration = time.time() - start

    # Should process 10 items in parallel
    # Assuming each takes 0.1s, total should be ~0.1s not 1s
    assert async_duration < 0.5
```

## Test Organization

### Directory Structure
```
tests/
├── unit/                    # Pure unit tests
│   ├── services/           # Service unit tests
│   ├── crud/              # CRUD unit tests
│   └── tools/             # Tool unit tests
├── integration/            # Integration tests
│   ├── api/               # API integration tests
│   ├── services/          # Service integration tests
│   └── database/          # Database integration tests
├── e2e/                    # End-to-end tests
│   ├── workflows/         # Complete workflow tests
│   └── cli/               # CLI E2E tests
└── performance/            # Performance tests
```

### Test Fixtures

#### Shared Fixtures (conftest.py)
```python
# tests/conftest.py
import pytest
from unittest.mock import Mock
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

@pytest.fixture
async def async_engine():
    """Create async test engine."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()

@pytest.fixture
async def async_session(async_engine):
    """Create async test session."""
    async with AsyncSession(async_engine) as session:
        yield session

@pytest.fixture
def mock_http_client():
    """Mock HTTP client for CLI tests."""
    with patch("httpx.Client") as mock:
        yield mock

@pytest.fixture
def anyio_backend():
    """Use asyncio for async tests."""
    return "asyncio"
```

## Migration Testing Strategy

### Phase 1: Prepare Tests
1. ~~Identify all tests using `event_loop_fixture`~~ (COMPLETED - fixture removed)
2. ~~Identify all tests with `@ci_skip_async`~~ (COMPLETED - decorators removed)
3. Create inventory of test patterns used

### Phase 2: Create New Test Patterns
1. Write example tests for each pattern
2. Document best practices
3. Create test utilities and fixtures

### Phase 3: Migrate Tests
1. Start with unit tests (easiest)
2. Move to integration tests
3. Finally, update E2E tests

### Phase 4: Validate Coverage
1. Ensure test coverage remains high
2. Verify all CI tests pass
3. Remove old test utilities

## Test Migration Checklist

For each test file:

- [x] Remove `event_loop_fixture` usage (COMPLETED)
- [x] Remove `@ci_skip_async` decorators (COMPLETED)
- [ ] Update to use new async patterns
- [ ] Remove injectable mocking
- [ ] Use simple dependency injection
- [ ] Verify tests pass locally
- [ ] Verify tests pass in CI
- [ ] Update test documentation

## Benefits After Migration

### 1. Simpler Test Setup
- No complex event loop management
- No injectable-specific fixtures
- Standard pytest-asyncio patterns

### 2. Faster Test Execution
- No event loop overhead
- Better parallel test execution
- Cleaner test isolation

### 3. Better Debugging
- Clear stack traces
- No DI framework in the middle
- Easier to understand failures

### 4. CI Reliability
- All tests run in CI
- No platform-specific issues
- Consistent test behavior

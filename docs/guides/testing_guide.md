# Testing Guide

## Overview

This guide covers all aspects of testing in Local Newsifier, including test execution, dependency injection testing, Apify webhook testing, and performance optimization.

## Table of Contents
- [Quick Start](#quick-start)
- [Running Tests](#running-tests)
- [Test Organization](#test-organization)
- [Test Markers](#test-markers)
- [Parallel Test Execution](#parallel-test-execution)
- [Database Testing](#database-testing)
- [Dependency Injection Testing](#dependency-injection-testing)
- [Apify Webhook Testing](#apify-webhook-testing)
- [Performance Optimization](#performance-optimization)
- [Common Patterns](#common-patterns)
- [Troubleshooting](#troubleshooting)

## Quick Start

```bash
# Run all tests in parallel (fastest)
make test

# Run tests serially (for debugging)
make test-serial

# Run with coverage report
make test-coverage

# Run specific test file
poetry run pytest tests/services/test_article_service.py

# Run tests matching pattern
poetry run pytest -k "article"
```

## Running Tests

### Basic Commands

```bash
# Run all tests in parallel (fastest)
make test

# Run tests serially (for debugging)
make test-serial

# Run with coverage report
make test-coverage

# Run specific test file
poetry run pytest tests/services/test_article_service.py

# Run tests matching pattern
poetry run pytest -k "article"

# Run with verbose output
poetry run pytest -v

# Run failed tests only
poetry run pytest --lf
```

### Test Categories

```bash
# Run only fast tests
poetry run pytest -m fast

# Run database tests
poetry run pytest -m db

# Skip slow tests
poetry run pytest -m "not slow"

# Run API tests only
poetry run pytest tests/api/

# Run service tests only
poetry run pytest tests/services/
```

## Test Organization

Tests are organized by component type:

```
tests/
├── api/              # FastAPI endpoint tests
├── cli/              # CLI command tests
├── config/           # Configuration tests
├── crud/             # Database CRUD tests
├── database/         # Database engine tests
├── di/               # Dependency injection tests
├── errors/           # Error handling tests
├── flows/            # Flow/workflow tests
├── integration/      # Integration tests
├── models/           # Data model tests
├── services/         # Service layer tests
├── tasks/            # Background task tests
└── tools/            # Tool tests (NLP, scraping, etc.)
```

### Test Naming Conventions

- Test files: `test_<module_name>.py`
- Test functions: `test_<functionality>_<scenario>`
- Test classes: `Test<ComponentName>`

## Test Markers

Use pytest markers to categorize tests:

```python
import pytest

@pytest.mark.fast
def test_simple_calculation():
    """Tests that run in < 1 second"""
    assert 1 + 1 == 2

@pytest.mark.slow
def test_complex_operation():
    """Tests that take > 1 second"""
    # Complex test logic

@pytest.mark.db
def test_database_operation(db_session):
    """Tests requiring database access"""
    # Database test logic

@pytest.mark.skip(reason="Feature not implemented")
def test_future_feature():
    """Skip tests for unimplemented features"""
    pass

@pytest.mark.parametrize("input,expected", [
    ("hello", "HELLO"),
    ("world", "WORLD"),
])
def test_uppercase(input, expected):
    """Parameterized tests"""
    assert input.upper() == expected
```

## Parallel Test Execution

### Configuration

The project uses `pytest-xdist` for parallel test execution:

```python
# pyproject.toml
[tool.pytest.ini_options]
addopts = "-n auto"  # Use all available CPU cores
```

### Test Isolation

Each test process gets its own database:

```python
# conftest.py
@pytest.fixture(scope="session")
def db_url(worker_id):
    """Create unique database for each test worker"""
    if worker_id == "master":
        return "sqlite:///test.db"
    return f"sqlite:///test_{worker_id}.db"
```

### Best Practices for Parallel Tests

1. **Avoid Shared State**
```python
# Bad - shared state
shared_data = []

def test_append():
    shared_data.append(1)  # Race condition!

# Good - isolated state
def test_append():
    data = []
    data.append(1)
```

2. **Use Unique Resources**
```python
# Bad - fixed port
def test_server():
    server = Server(port=8080)  # Port conflict!

# Good - dynamic port
def test_server():
    server = Server(port=0)  # OS assigns free port
```

3. **Clean Up Resources**
```python
@pytest.fixture
def temp_file():
    file = create_temp_file()
    yield file
    file.unlink()  # Always cleanup
```

## Database Testing

### Test Database Configuration

Tests use SQLite in-memory databases for speed and isolation:

```python
# For unit tests - in-memory
DATABASE_URL = "sqlite:///:memory:"

# For integration tests - file-based
DATABASE_URL = "sqlite:///test.db"
```

### Database Fixtures

```python
@pytest.fixture
def db_session():
    """Provide clean database session for each test"""
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        yield session
        session.rollback()

@pytest.fixture
def sample_article(db_session):
    """Create sample article for tests"""
    article = Article(
        title="Test Article",
        content="Test content",
        url="https://example.com/test"
    )
    db_session.add(article)
    db_session.commit()
    db_session.refresh(article)
    return article
```

### Testing Database Operations

```python
def test_create_article(db_session, article_crud):
    # Arrange
    data = {
        "title": "Test Article",
        "content": "Test content",
        "url": "https://example.com/test"
    }

    # Act
    article = article_crud.create(db_session, data)

    # Assert
    assert article.id is not None
    assert article.title == data["title"]

    # Verify in database
    db_article = db_session.get(Article, article.id)
    assert db_article is not None
```

## Dependency Injection Testing

### FastAPI Native DI Testing

The API uses FastAPI's native dependency injection. Here's how to test it:

```python
from fastapi.testclient import TestClient
from unittest.mock import Mock

def test_api_endpoint(app):
    # Mock dependencies
    mock_session = Mock()
    mock_service = Mock()
    mock_service.get.return_value = {"id": 1, "title": "Test Article"}

    # Override dependencies
    app.dependency_overrides[get_session] = lambda: mock_session
    app.dependency_overrides[get_article_service] = lambda: mock_service

    # Test the endpoint
    client = TestClient(app)
    response = client.get("/articles/1")

    assert response.status_code == 200
    assert response.json()["title"] == "Test Article"
    mock_service.get.assert_called_once_with(1)
```

### CLI Testing (Injectable Pattern)

The CLI currently uses fastapi-injectable (being migrated to HTTP calls):

```python
from injectable import injectable_factory, clear_injectables
from unittest.mock import Mock

@pytest.fixture(autouse=True)
def reset_injection():
    """Reset injection container before/after each test"""
    clear_injectables()
    yield
    clear_injectables()

def test_cli_command_with_mocks():
    # Create mocks
    mock_crud = Mock()
    mock_crud.get.return_value = {"id": 1, "title": "Test"}

    # Register mocks
    with injectable_factory() as factory:
        factory.register(get_article_crud, mock_crud)

        # Test the service
        runner = CliRunner()
        result = runner.invoke(cli, ["articles", "get", "1"])

        # Verify
        assert result.exit_code == 0
        assert "Test" in result.output
        mock_crud.get.assert_called_once_with(1)
```

### Testing Services

```python
class TestArticleService:
    @pytest.fixture
    def service(self, db_session):
        """Provide service with real database session"""
        return ArticleService(
            article_crud=CRUDArticle(),
            session_factory=lambda: db_session
        )

    def test_create_article(self, service):
        # Act
        article = service.create({
            "title": "Test",
            "content": "Content",
            "url": "https://example.com"
        })

        # Assert
        assert article.id is not None
        assert article.title == "Test"
```

## Apify Webhook Testing

### Overview

The Apify webhook endpoint at `/webhooks/apify` is fully functional with sync-only implementation.

### Required Webhook Fields

All webhook requests must include:
- `eventType` (e.g., "ACTOR.RUN.SUCCEEDED")
- `actorId`
- `actorRunId`
- `userId`
- `webhookId`
- `createdAt`
- `defaultKeyValueStoreId`
- `defaultDatasetId`
- `startedAt`
- `status`

### Fish Shell Testing Functions

```bash
# Test successful webhook
test_webhook_success

# Test failed webhook
test_webhook_failure

# Test all scenarios
test_webhook_batch

# Custom parameters
test_webhook --event ACTOR.RUN.FAILED --status FAILED --actor my_actor
```

### HTTPie Testing (Correct Syntax)

```bash
# ✅ Correct - sends JSON
echo '{
    "eventType": "ACTOR.RUN.SUCCEEDED",
    "actorId": "tom_cruise",
    "actorRunId": "test-run-123",
    "webhookId": "webhook-456",
    "createdAt": "2025-01-25T12:00:00Z",
    "userId": "test_user",
    "defaultKeyValueStoreId": "test_kvs",
    "defaultDatasetId": "test_dataset",
    "startedAt": "2025-01-25T12:00:00Z",
    "status": "SUCCEEDED"
}' | http POST http://localhost:8000/webhooks/apify Content-Type:application/json

# ❌ Incorrect - sends form data
http POST http://localhost:8000/webhooks/apify \
    eventType=ACTOR.RUN.SUCCEEDED \
    actorId=tom_cruise
```

### Testing Apify Service

The ApifyService automatically detects test environments:

```python
def test_apify_run_actor():
    # No token = test mode with mock data
    service = ApifyService()

    result = service.run_actor(
        "apify/web-scraper",
        {"startUrls": [{"url": "https://example.com"}]}
    )

    assert result["status"] == "SUCCEEDED"
    assert len(result["items"]) == 2  # Mock returns 2 items
```

## Performance Optimization

### Identifying Slow Tests

```bash
# Find slow tests
python scripts/identify_slow_tests.py

# Profile test execution time
poetry run pytest --durations=10
```

### Optimizing Test Performance

1. **Use Fixtures Efficiently**
```python
# Expensive fixture - scope it appropriately
@pytest.fixture(scope="session")
def nlp_model():
    """Load once per test session"""
    return load_spacy_model()

@pytest.fixture(scope="function")
def db_session(nlp_model):
    """New session per test, reuse model"""
    # ...
```

2. **Mock External Services**
```python
@pytest.fixture
def mock_requests(mocker):
    """Mock HTTP requests to avoid network calls"""
    return mocker.patch("requests.get")

def test_web_scraper(mock_requests):
    mock_requests.return_value.text = "<html>...</html>"
    # Test without network calls
```

3. **Use Test Markers**
```python
@pytest.mark.slow
def test_full_pipeline():
    """Mark slow tests to skip during development"""
    # Complex integration test

# Run fast tests only during development
# pytest -m "not slow"
```

## Common Patterns

### Testing Sync-Only Code

**Important:** Local Newsifier uses sync-only patterns. All tests should follow sync patterns:

```python
# Testing sync endpoints
def test_webhook_endpoint(client):
    response = client.post(
        "/webhooks/apify",
        json={
            "eventType": "ACTOR.RUN.SUCCEEDED",
            "actorId": "test_actor",
            # ... other required fields
        }
    )
    assert response.status_code == 202

# Testing sync services
def test_sync_service(db_session):
    service = ArticleService(
        article_crud=CRUDArticle(),
        session_factory=lambda: db_session
    )

    article = service.create({
        "title": "Test",
        "content": "Content"
    })
    assert article.id is not None
```

### Testing Error Handling

```python
def test_service_handles_not_found(service):
    # Act & Assert
    with pytest.raises(ArticleNotFoundError):
        service.get(999)

def test_api_returns_404(client):
    # Mock service to raise error
    app.dependency_overrides[get_article_service] = lambda: Mock(
        get=Mock(side_effect=ArticleNotFoundError())
    )

    # Act
    response = client.get("/articles/999")

    # Assert
    assert response.status_code == 404
```

### Session Management in Tests

```python
@pytest.fixture
def db_session():
    """Provide sync database session for tests."""
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        yield session
        session.rollback()

def test_with_session(db_session):
    """Test using sync session."""
    article = Article(title="Test", content="Content")
    db_session.add(article)
    db_session.commit()

    # Query using sync session
    result = db_session.query(Article).first()
    assert result.title == "Test"
```

## Troubleshooting

### Common Issues

1. **Database Lock Errors**
```python
# Problem: SQLite database is locked
# Solution: Use in-memory databases for tests
DATABASE_URL = "sqlite:///:memory:"
```

2. **Port Conflicts in Parallel Tests**
```python
# Problem: Fixed ports cause conflicts
# Solution: Use dynamic port allocation
server = TestServer(port=0)  # OS assigns free port
```

3. **Flaky Tests**
```python
# Problem: Tests randomly fail
# Solutions:
# 1. Add retries for external services
@pytest.mark.flaky(reruns=3)
def test_external_api():
    # ...

# 2. Increase timeouts
def test_slow_operation():
    result = operation(timeout=10)  # Increase timeout
```

4. **Import Errors in Tests**
```python
# Problem: Circular imports when testing
# Solution: Import inside test functions
def test_service():
    from local_newsifier.services import MyService  # Import here
    service = MyService()
```

### Debugging Tips

```bash
# Run single test with debugging
poetry run pytest -xvs tests/path/to/test.py::test_function

# Drop into debugger on failure
poetry run pytest --pdb

# Show local variables on failure
poetry run pytest -l

# Capture print statements
poetry run pytest -s

# Run last failed tests
poetry run pytest --lf

# Run tests in specific order
poetry run pytest --ff  # Failed first
```

## CI/CD Integration

### GitHub Actions Configuration

```yaml
# .github/workflows/tests.yml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: |
          pip install -r requirements-dev.txt
      - name: Run tests
        run: |
          pytest tests/ -v --cov=src --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

### Test Categories in CI

```makefile
# Makefile
test-unit:
	pytest tests/api tests/cli tests/services -v

test-integration:
	pytest tests/integration -v

test-all:
	pytest tests/ -v --cov=src

test-fast:
	pytest tests/ -v -m "not slow"
```

## Best Practices

1. **Test Isolation**: Each test should be independent
2. **Clear Assertions**: Use descriptive assertion messages
3. **Arrange-Act-Assert**: Structure tests clearly
4. **Mock External Dependencies**: Don't hit real APIs/databases
5. **Use Fixtures**: Share setup code between tests
6. **Test Edge Cases**: Empty data, None values, errors
7. **Keep Tests Fast**: Mock expensive operations
8. **Descriptive Names**: Test names should explain what they test
9. **Sync-Only**: Follow the project's sync-only pattern
10. **Session Management**: Return IDs not objects across session boundaries

## See Also

- [Dependency Injection Guide](dependency_injection.md) - DI patterns and testing
- [CLI Usage Guide](cli_usage.md) - CLI commands and usage
- [Python Setup Guide](python_setup.md) - Environment configuration

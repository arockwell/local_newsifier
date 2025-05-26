# Testing Strategy for CLI to FastAPI Migration

## Overview

This document outlines the comprehensive testing strategy for migrating from direct dependency injection to FastAPI-based CLI, ensuring no functionality is lost and improving test reliability.

## Key Improvements

### Before Migration
- Complex event loop management
- Conditional decorators for CI
- Dependency injection mocking
- Intermittent test failures
- Slow test execution

### After Migration
- Simple TestClient usage
- No event loop issues
- Straightforward mocking
- Consistent test results
- Faster execution

## Test Categories

### 1. API Endpoint Tests

#### Router Tests
```python
# tests/api/test_cli_router.py
import pytest
from fastapi.testclient import TestClient
from main import app

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c

def test_process_article_endpoint(client, mock_db):
    response = client.post("/cli/articles/process", json={
        "url": "https://example.com/article",
        "content": "Test content"
    })

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "processed"
    assert "id" in data
```

#### Background Task Tests
```python
def test_batch_processing_queues_task(client, mock_background_tasks):
    response = client.post("/cli/articles/batch", json={
        "urls": ["https://example.com/1", "https://example.com/2"],
        "concurrent_limit": 5
    })

    assert response.status_code == 200
    assert "task_id" in response.json()
    mock_background_tasks.add_task.assert_called_once()
```

### 2. HTTP Client Tests

#### Client Unit Tests
```python
# tests/cli/test_http_client.py
import pytest
from unittest.mock import Mock, patch
import httpx
from cli.client import NewsifierClient, NewsifierAPIError

@pytest.fixture
def mock_httpx_client():
    with patch('httpx.Client') as mock:
        yield mock

def test_process_article_success(mock_httpx_client):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"id": 1, "status": "processed"}
    mock_httpx_client.return_value.post.return_value = mock_response

    client = NewsifierClient()
    result = client.process_article("https://example.com")

    assert result["id"] == 1
    assert result["status"] == "processed"
```

#### Error Handling Tests
```python
def test_api_error_handling(mock_httpx_client):
    mock_response = Mock()
    mock_response.status_code = 404
    mock_response.json.return_value = {"detail": "Article not found"}
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        message="", request=Mock(), response=mock_response
    )
    mock_httpx_client.return_value.post.return_value = mock_response

    client = NewsifierClient()
    with pytest.raises(NewsifierAPIError) as exc_info:
        client.process_article("https://example.com")

    assert exc_info.value.status_code == 404
    assert "Article not found" in str(exc_info.value)
```

### 3. CLI Command Tests

#### Command Integration Tests
```python
# tests/cli/test_commands.py
from click.testing import CliRunner
from cli.commands import cli

@pytest.fixture
def runner():
    return CliRunner()

@pytest.fixture
def mock_client(monkeypatch):
    mock = Mock()
    monkeypatch.setattr('cli.commands.NewsifierClient', lambda **kwargs: mock)
    return mock

def test_process_command(runner, mock_client):
    mock_client.process_article.return_value = {
        'id': 1,
        'title': 'Test Article',
        'url': 'https://example.com',
        'opinion_count': 5,
        'processing_time': 1.23,
        'status': 'processed'
    }

    result = runner.invoke(cli, ['process', 'https://example.com'])

    assert result.exit_code == 0
    assert 'Article processed successfully' in result.output
    assert 'Test Article' in result.output
```

### 4. Service Layer Tests

#### Service Unit Tests
```python
# tests/services/test_article_service.py
import pytest
from services.article_service import ArticleService
from sqlmodel import Session

@pytest.fixture
def article_service():
    return ArticleService()

def test_process_article_with_session(article_service, db_session):
    result = article_service.process_article(
        session=db_session,
        url="https://example.com",
        content="Test content"
    )

    assert result is not None
    assert result.url == "https://example.com"
```

### 5. Integration Tests

#### End-to-End Tests
```python
# tests/integration/test_cli_e2e.py
import pytest
from fastapi.testclient import TestClient
from click.testing import CliRunner
from main import app
from cli.commands import cli

def test_full_article_processing_flow():
    # Start with API
    with TestClient(app) as api_client:
        # Process via API
        response = api_client.post("/cli/articles/process", json={
            "url": "https://example.com/test",
            "content": "Integration test content"
        })
        assert response.status_code == 200
        article_id = response.json()["id"]

        # Verify via CLI
        runner = CliRunner()
        result = runner.invoke(cli, [
            '--api-url', 'http://testserver',
            'health'
        ])
        assert result.exit_code == 0
```

## Test Fixtures

### Database Fixtures
```python
@pytest.fixture
def db_session():
    """Provide clean database session for tests."""
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        yield session

@pytest.fixture
def sample_article(db_session):
    """Create sample article for tests."""
    article = Article(
        title="Test Article",
        url="https://example.com/test",
        content="Test content"
    )
    db_session.add(article)
    db_session.commit()
    return article
```

### Mock Fixtures
```python
@pytest.fixture
def mock_external_api():
    """Mock external API calls."""
    with patch('httpx.AsyncClient') as mock:
        yield mock

@pytest.fixture
def mock_celery_task():
    """Mock Celery task execution."""
    with patch('tasks.process_article.delay') as mock:
        mock.return_value.id = "test-task-123"
        yield mock
```

## Testing Best Practices

### 1. Test Organization
```
tests/
├── api/
│   ├── test_cli_router.py
│   ├── test_endpoints.py
│   └── test_background_tasks.py
├── cli/
│   ├── test_client.py
│   ├── test_commands.py
│   └── test_async_operations.py
├── services/
│   ├── test_article_service.py
│   └── test_report_service.py
├── integration/
│   ├── test_cli_e2e.py
│   └── test_api_e2e.py
└── conftest.py
```

### 2. Test Data Management
- Use factories for test data creation
- Isolate test data per test
- Clean up after tests
- Use transactions for rollback

### 3. Mocking Strategy
- Mock external dependencies
- Use real database for integration tests
- Mock time-sensitive operations
- Provide realistic mock data

### 4. Performance Testing
```python
def test_batch_processing_performance(client, benchmark):
    urls = [f"https://example.com/{i}" for i in range(100)]

    result = benchmark(
        client.post,
        "/cli/articles/batch",
        json={"urls": urls, "concurrent_limit": 10}
    )

    assert result.status_code == 200
    assert benchmark.stats["mean"] < 1.0  # Should respond quickly
```

## CI/CD Integration

### Test Execution
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
          python-version: '3.11'
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

## Migration Testing

### Parallel Testing
During migration, run both old and new implementations:

```python
def test_compatibility(old_service, new_client):
    url = "https://example.com/test"

    # Old way
    old_result = old_service.process_article(url)

    # New way
    new_result = new_client.process_article(url)

    # Verify same behavior
    assert old_result.title == new_result['title']
    assert old_result.id == new_result['id']
```

### Rollback Testing
```python
@pytest.mark.parametrize("use_new_api", [True, False])
def test_dual_mode_support(use_new_api):
    if use_new_api:
        client = NewsifierClient()
        result = client.process_article("https://example.com")
    else:
        service = get_article_service()
        result = service.process_article("https://example.com")

    assert result is not None
```

## Success Metrics

- **Test Coverage**: Maintain >90% coverage
- **Execution Time**: Reduce by 50%
- **Flaky Tests**: Eliminate all flaky tests
- **CI Success Rate**: Achieve 99%+ success rate
- **Debug Time**: Reduce average debug time by 70%

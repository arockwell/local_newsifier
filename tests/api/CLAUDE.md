# API Testing Guide

This guide covers testing patterns specific to FastAPI endpoints in Local Newsifier.

## API Test Structure

All API tests should follow this structure:
```python
from fastapi.testclient import TestClient
from local_newsifier.api.main import app

def test_endpoint_name(mock_injectable_dependencies):
    # 1. Setup mocks
    mock_injectable_dependencies.patch_provider(
        "get_service_name",
        mock_injectable_dependencies.mocks["service_name"]
    )

    # 2. Create test client
    client = TestClient(app)

    # 3. Make request
    response = client.get("/api/endpoint")

    # 4. Assert response
    assert response.status_code == 200
    assert response.json() == expected_data
```

## Dependency Injection in API Tests

### Mocking Injectable Dependencies
```python
def test_with_mocked_dependencies(mock_injectable_dependencies):
    # Get the mock service
    mock_service = mock_injectable_dependencies.mocks["article_service"]

    # Configure mock behavior
    mock_service.get_all.return_value = [
        Article(id=1, title="Test Article")
    ]

    # Patch the provider
    mock_injectable_dependencies.patch_provider(
        "get_article_service",
        mock_service
    )

    # Test the endpoint
    client = TestClient(app)
    response = client.get("/api/articles")
    assert response.status_code == 200
```

### Testing Different HTTP Methods

```python
# GET request
response = client.get("/api/articles/1")

# POST request with JSON
response = client.post(
    "/api/articles",
    json={"title": "New Article", "content": "Content"}
)

# PUT request
response = client.put(
    "/api/articles/1",
    json={"title": "Updated Title"}
)

# DELETE request
response = client.delete("/api/articles/1")
```

## Testing Authentication

For endpoints requiring authentication:
```python
def test_authenticated_endpoint(mock_injectable_dependencies):
    # Mock auth service
    mock_auth = mock_injectable_dependencies.mocks["auth_service"]
    mock_auth.verify_token.return_value = {"user_id": 1}

    mock_injectable_dependencies.patch_provider(
        "get_auth_service",
        mock_auth
    )

    client = TestClient(app)
    response = client.get(
        "/api/protected",
        headers={"Authorization": "Bearer test-token"}
    )
    assert response.status_code == 200
```

## Testing Error Responses

Always test error scenarios:
```python
def test_not_found_error(mock_injectable_dependencies):
    mock_service = mock_injectable_dependencies.mocks["article_service"]
    mock_service.get_by_id.return_value = None

    mock_injectable_dependencies.patch_provider(
        "get_article_service",
        mock_service
    )

    client = TestClient(app)
    response = client.get("/api/articles/999")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()
```

## Testing Webhooks

For webhook endpoints:
```python
def test_webhook_endpoint(mock_injectable_dependencies):
    # Mock webhook handler
    mock_handler = MagicMock()
    mock_injectable_dependencies.patch_provider(
        "get_webhook_handler",
        mock_handler
    )

    client = TestClient(app)
    webhook_data = {
        "eventType": "ACTOR.RUN.SUCCEEDED",
        "eventData": {"actorRunId": "test-run-id"}
    }

    response = client.post(
        "/webhooks/apify",
        json=webhook_data,
        headers={"X-Webhook-Secret": "test-secret"}
    )

    assert response.status_code == 200
    mock_handler.handle_webhook.assert_called_once_with(webhook_data)
```

## Testing Query Parameters

```python
def test_with_query_params(mock_injectable_dependencies):
    mock_service = mock_injectable_dependencies.mocks["article_service"]
    mock_service.search.return_value = [Article(id=1, title="Test")]

    mock_injectable_dependencies.patch_provider(
        "get_article_service",
        mock_service
    )

    client = TestClient(app)
    response = client.get("/api/articles?q=test&limit=10")

    assert response.status_code == 200
    mock_service.search.assert_called_with(query="test", limit=10)
```

## Testing File Uploads

```python
def test_file_upload(mock_injectable_dependencies):
    mock_service = mock_injectable_dependencies.mocks["file_service"]
    mock_service.process_file.return_value = {"status": "processed"}

    mock_injectable_dependencies.patch_provider(
        "get_file_service",
        mock_service
    )

    client = TestClient(app)

    with open("test_file.txt", "wb") as f:
        f.write(b"test content")

    with open("test_file.txt", "rb") as f:
        response = client.post(
            "/api/upload",
            files={"file": ("test.txt", f, "text/plain")}
        )

    assert response.status_code == 200
```

## Testing Async Endpoints

### Testing Async Webhook Endpoints

For async webhook endpoints with async sessions:
```python
from unittest.mock import AsyncMock, MagicMock
import pytest

@pytest.mark.asyncio
async def test_async_webhook_endpoint():
    # Mock async session
    mock_session = MagicMock()
    mock_session.execute = AsyncMock()
    mock_session.add = MagicMock()
    mock_session.flush = AsyncMock()
    mock_session.commit = AsyncMock()

    # Override async session dependency
    async def override_get_async_session():
        yield mock_session

    app.dependency_overrides[get_async_session] = override_get_async_session

    # Test webhook
    client = TestClient(app)
    response = client.post(
        "/webhooks/apify",
        json={
            "eventType": "ACTOR.RUN.SUCCEEDED",
            "actorId": "test-actor",
            "runId": "test-run"
        },
        headers={"Apify-Webhook-Signature": "test-signature"}
    )

    assert response.status_code == 202
    assert response.json()["status"] == "accepted"

    # Verify async operations were called
    mock_session.flush.assert_awaited()

    # Clean up override
    app.dependency_overrides.clear()
```

### Testing Async Database Operations in Endpoints

```python
@pytest.mark.asyncio
async def test_async_article_endpoint():
    # Mock async CRUD
    mock_crud = MagicMock()
    mock_crud.get = AsyncMock(return_value=Article(id=1, title="Test"))

    # Mock async session with proper query execution
    mock_session = MagicMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = Article(id=1, title="Test")
    mock_session.execute = AsyncMock(return_value=mock_result)

    async def override_get_async_session():
        yield mock_session

    app.dependency_overrides[get_async_session] = override_get_async_session

    client = TestClient(app)
    response = client.get("/api/articles/1")

    assert response.status_code == 200
    assert response.json()["title"] == "Test"

    app.dependency_overrides.clear()
```

### Testing Async Service Dependencies

```python
def test_endpoint_with_async_service(mock_injectable_dependencies):
    # Create async service mock
    mock_service = MagicMock()
    mock_service.process_webhook = AsyncMock(
        return_value={"status": "processed", "webhook_id": 123}
    )

    # Override the service provider
    mock_injectable_dependencies.patch_provider(
        "get_apify_webhook_service_async",
        mock_service
    )

    # TestClient handles async endpoints transparently
    client = TestClient(app)
    response = client.post(
        "/webhooks/apify",
        json={"eventType": "test"}
    )

    assert response.status_code == 202
    mock_service.process_webhook.assert_awaited_once()
```

## Common Patterns

### 1. Testing Pagination
```python
def test_pagination(mock_injectable_dependencies):
    # Setup mock to return paginated results
    mock_service.get_paginated.return_value = {
        "items": [Article(id=1), Article(id=2)],
        "total": 10,
        "page": 1,
        "size": 2
    }

    response = client.get("/api/articles?page=1&size=2")
    assert len(response.json()["items"]) == 2
```

### 2. Testing Validation Errors
```python
def test_validation_error(mock_injectable_dependencies):
    client = TestClient(app)
    response = client.post(
        "/api/articles",
        json={"title": ""}  # Empty title should fail validation
    )

    assert response.status_code == 422
    assert "validation error" in response.json()["detail"][0]["msg"]
```

### 3. Testing Background Tasks
```python
def test_background_task(mock_injectable_dependencies):
    mock_task_service = MagicMock()
    mock_injectable_dependencies.patch_provider(
        "get_task_service",
        mock_task_service
    )

    client = TestClient(app)
    response = client.post("/api/process-async")

    assert response.status_code == 202
    assert "task_id" in response.json()
    mock_task_service.create_task.assert_called_once()
```

## Best Practices

1. **Always mock external dependencies** - Never make real API calls or database queries
2. **Test both success and error paths** - Include tests for 4xx and 5xx responses
3. **Use descriptive test names** - `test_get_article_returns_article_when_exists`
4. **Keep tests isolated** - Each test should be independent
5. **Mock at the service layer** - Mock services, not individual database queries
6. **Test request validation** - Ensure invalid inputs return appropriate errors
7. **Test response schemas** - Verify the response structure matches expectations

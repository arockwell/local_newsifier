# Testing with Injectable Dependencies

This guide provides practical approaches for testing components that use fastapi-injectable dependencies. The focus is on simplicity and reusability.

## Overview

Testing components that use dependency injection can be challenging, especially when dealing with async functionality. This guide introduces simplified testing patterns to make this process easier.

## Prerequisites

- Python 3.10+
- pytest
- pytest-asyncio (for testing async functionality)
- fastapi-injectable
- Basic understanding of dependency injection concepts

## Testing Utilities

We've created a suite of testing utilities in `tests/conftest_injectable.py` to simplify testing with injectable dependencies.

### Key Utilities

1. **mock_injectable_dependencies**: A fixture that provides a simple way to mock and manage injectable dependencies
2. **common_injectable_mocks**: Pre-configured mocks for frequently used dependencies
3. **injectable_test_app**: A fixture that provides a properly configured FastAPI app for testing
4. **event_loop**: A fixture that creates and manages an event loop for async tests
5. **create_mock_service**: A helper function to create service instances with mocked dependencies

## Testing Patterns

### Pattern 1: Direct Instantiation

The simplest way to test components is to instantiate them directly with mock dependencies:

```python
def test_entity_service_get_entity(mock_injectable_dependencies):
    # Arrange
    entity_crud_mock = MagicMock()
    entity_crud_mock.get.return_value = {"id": 1, "name": "Test Entity"}
    session_mock = MagicMock()
    
    # Register mocks
    mock = mock_injectable_dependencies
    mock.register("get_entity_crud", entity_crud_mock)
    mock.register("get_session", session_mock)
    
    # Create service with mocks
    service = EntityService(
        entity_crud=entity_crud_mock,
        session=session_mock
    )
    
    # Act
    result = service.get_entity(1)
    
    # Assert
    assert result == {"id": 1, "name": "Test Entity"}
    entity_crud_mock.get.assert_called_once_with(session_mock, id=1)
```

### Pattern 2: Using Helper Functions

For more complex services, use the `create_mock_service` helper:

```python
def test_complex_service(mock_injectable_dependencies):
    # Arrange - create and register mocks
    mock = mock_injectable_dependencies
    entity_service_mock = MagicMock()
    mock.register("get_entity_service", entity_service_mock)
    article_service_mock = MagicMock()
    mock.register("get_article_service", article_service_mock)
    
    # Create service with mocks
    service = create_mock_service(
        ComplexService,
        entity_service=entity_service_mock,
        article_service=article_service_mock
    )
    
    # Act
    service.process_data()
    
    # Assert
    entity_service_mock.get_entities.assert_called_once()
    article_service_mock.get_articles.assert_called_once()
```

### Pattern 3: Testing API Endpoints

For testing FastAPI endpoints that use injectable dependencies:

```python
@pytest.mark.asyncio
async def test_endpoint(injectable_test_app, mock_injectable_dependencies):
    # Arrange
    app = injectable_test_app
    mock = mock_injectable_dependencies
    
    # Create and register mock
    entity_service_mock = MagicMock()
    entity_service_mock.get_entity.return_value = {"id": 1, "name": "Test Entity"}
    mock.register("get_entity_service", entity_service_mock)
    
    # Define test endpoint
    @app.get("/entities/{entity_id}")
    def get_entity(
        entity_id: int,
        entity_service = Depends(lambda: mock.get("get_entity_service"))
    ):
        return entity_service.get_entity(entity_id)
    
    # Create test client
    client = TestClient(app)
    
    # Act
    response = client.get("/entities/1")
    
    # Assert
    assert response.status_code == 200
    assert response.json() == {"id": 1, "name": "Test Entity"}
    entity_service_mock.get_entity.assert_called_once_with(1)
```

### Pattern 4: Using Common Mocks

For testing with pre-configured common mocks:

```python
def test_with_common_mocks(common_injectable_mocks):
    # Arrange - customize pre-configured mocks
    mock = common_injectable_mocks
    mock.get("get_entity_crud").get.return_value = {"id": 1, "name": "Test Entity"}
    
    # Create service
    service = EntityService(
        entity_crud=mock.get("get_entity_crud"),
        session=mock.get("get_session")
    )
    
    # Act
    result = service.get_entity(1)
    
    # Assert
    assert result == {"id": 1, "name": "Test Entity"}
```

## Testing Different Component Types

### Testing Services

Services typically handle business logic and may interact with the database:

```python
def test_article_service(mock_injectable_dependencies):
    # Arrange
    mock = mock_injectable_dependencies
    article_crud_mock = MagicMock()
    article_crud_mock.get_by_url.return_value = None  # No existing article
    article_crud_mock.create.return_value = {"id": 1, "title": "Test Article"}
    mock.register("get_article_crud", article_crud_mock)
    mock.register("get_session", MagicMock())
    
    # Create service
    service = ArticleService(
        article_crud=mock.get("get_article_crud"),
        session=mock.get("get_session")
    )
    
    # Act
    article_data = {"title": "Test Article", "url": "https://example.com"}
    result = service.create_article(article_data)
    
    # Assert
    assert result == {"id": 1, "title": "Test Article"}
    article_crud_mock.get_by_url.assert_called_once()
    article_crud_mock.create.assert_called_once()
```

### Testing Flows

Flows orchestrate multiple services and typically contain business process logic:

```python
def test_entity_tracking_flow(mock_injectable_dependencies):
    # Arrange - create and register mocks
    mock = mock_injectable_dependencies
    entity_service_mock = MagicMock()
    entity_service_mock.get_entities.return_value = [{"id": 1, "name": "Test Entity"}]
    mock.register("get_entity_service", entity_service_mock)
    
    article_service_mock = MagicMock()
    article_service_mock.get_article.return_value = {"id": 1, "title": "Test Article"}
    mock.register("get_article_service", article_service_mock)
    
    entity_extractor_mock = MagicMock()
    entity_extractor_mock.extract_entities.return_value = [{"text": "Test Entity", "type": "PERSON"}]
    mock.register("get_entity_extractor_tool", entity_extractor_mock)
    
    # Create flow
    flow = EntityTrackingFlow(
        entity_service=entity_service_mock,
        article_service=article_service_mock,
        entity_extractor=entity_extractor_mock
    )
    
    # Act
    result = flow.process_article(1)
    
    # Assert
    article_service_mock.get_article.assert_called_once_with(1)
    entity_extractor_mock.extract_entities.assert_called_once()
    entity_service_mock.create_entities.assert_called_once()
    assert len(result) > 0
```

### Testing Tools

Tools provide utility functions and are generally more stateless:

```python
def test_entity_extractor_tool(mock_injectable_dependencies):
    # Arrange
    mock = mock_injectable_dependencies
    nlp_model_mock = MagicMock()
    nlp_model_mock.return_value.ents = [
        MagicMock(text="John Doe", label_="PERSON"),
        MagicMock(text="New York", label_="GPE")
    ]
    mock.register("get_nlp_model", nlp_model_mock)
    
    # Create tool
    tool = EntityExtractorTool(
        nlp_model=nlp_model_mock
    )
    
    # Act
    text = "John Doe visited New York last week."
    entities = tool.extract_entities(text)
    
    # Assert
    assert len(entities) == 2
    assert {"text": "John Doe", "type": "PERSON"} in entities
    assert {"text": "New York", "type": "GPE"} in entities
    nlp_model_mock.assert_called_once_with(text)
```

## Advanced Techniques

### Testing Async Components

For testing async components, use the `pytest.mark.asyncio` decorator:

```python
@pytest.mark.asyncio
async def test_async_service(mock_injectable_dependencies):
    # Arrange
    mock = mock_injectable_dependencies
    api_client_mock = MagicMock()
    api_client_mock.fetch_data = AsyncMock(return_value={"data": "test"})
    mock.register("get_api_client", api_client_mock)
    
    # Create service
    service = AsyncService(
        api_client=api_client_mock
    )
    
    # Act
    result = await service.get_data()
    
    # Assert
    assert result == {"data": "test"}
    api_client_mock.fetch_data.assert_called_once()
```


## Common Pitfalls and Solutions

### 1. Event Loop Issues

**Problem**: Tests fail with `RuntimeError: There is no current event loop in thread`

**Solution**: Use the `event_loop` fixture provided in `conftest_injectable.py`:

```python
@pytest.mark.asyncio
async def test_async_function(event_loop):
    # Your test code here
```

### 2. Missing Mock Dependencies

**Problem**: Tests fail with `ValueError: Mock for provider 'get_service_name' not registered`

**Solution**: Always register your mocks before using them:

```python
mock.register("get_service_name", MagicMock())
```

### 3. FastAPI App Registration Issues

**Problem**: Tests fail with `RuntimeError: No event loop running`

**Solution**: Use the `injectable_test_app` fixture which properly handles the async registration:

```python
@pytest.mark.asyncio
async def test_endpoint(injectable_test_app, mock_injectable_dependencies):
    # Your test code here
```

### 4. Session Management Issues

**Problem**: Test fails with `sqlalchemy.exc.InvalidRequestError: Object is not bound to a Session`

**Solution**: Mock the session and ensure it's passed correctly:

```python
session_mock = MagicMock()
mock.register("get_session", session_mock)
```

## Best Practices

1. **Isolation**: Each test should be isolated from others - avoid shared state
2. **Explicit Dependencies**: Make all dependencies explicit in constructor parameters
3. **Comprehensive Mocking**: Mock all dependencies, not just the ones you're testing
4. **Assertion Specificity**: Make assertions as specific as possible
5. **Follow AAA Pattern**: Arrange, Act, Assert - keep tests structured
6. **Clean Setup/Teardown**: Use fixtures for clean setup and teardown
7. **Test Realistic Scenarios**: Test real use cases, not just function calls
8. **Use Helper Fixtures**: Leverage the utility fixtures for common patterns

## Conclusion

Testing components with injectable dependencies can be straightforward when using the right patterns and utilities. By following the examples in this guide, you can create clean, maintainable tests for your injectable components.

For more information, refer to:
- `tests/conftest_injectable.py` for the testing utilities
- `tests/api/test_injectable_endpoints.py` for examples of testing endpoints
- Example tests for services, flows, and tools in their respective test directories
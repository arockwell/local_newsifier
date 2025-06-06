# Service Testing Guide

This guide covers testing patterns for service layer components in Local Newsifier.

## Service Test Structure

All service tests should follow this pattern:
```python
def test_service_method():
    # Arrange - Create mocks and service instance
    mock_crud = MagicMock(spec=ArticleCRUD)
    mock_session = MagicMock(spec=Session)

    service = ArticleService(
        article_crud=mock_crud,
        session_factory=lambda: mock_session
    )

    # Act - Call the service method
    result = service.process_article(article_id=1)

    # Assert - Verify results and mock interactions
    assert result == expected_result
    mock_crud.get.assert_called_once_with(mock_session, 1)
```

## Mocking Dependencies

### CRUD Operations
```python
def test_service_with_crud():
    # Mock CRUD with specific return values
    mock_crud = MagicMock(spec=ArticleCRUD)
    mock_crud.get.return_value = Article(id=1, title="Test")
    mock_crud.get_all.return_value = [
        Article(id=1, title="Article 1"),
        Article(id=2, title="Article 2")
    ]

    service = ArticleService(
        article_crud=mock_crud,
        session_factory=lambda: MagicMock()
    )

    # Test service method
    article = service.get_article(1)
    assert article.title == "Test"
```

### External Services
```python
def test_service_with_external_dependency():
    # Mock external service
    mock_analyzer = MagicMock(spec=SentimentAnalyzer)
    mock_analyzer.analyze.return_value = {
        "sentiment": "positive",
        "score": 0.8
    }

    service = AnalysisService(
        sentiment_analyzer=mock_analyzer,
        session_factory=lambda: MagicMock()
    )

    result = service.analyze_text("Great product!")
    assert result["sentiment"] == "positive"
```

## Testing Session Management

### Proper Session Usage
```python
def test_session_management():
    mock_session = MagicMock(spec=Session)
    session_factory = MagicMock(return_value=mock_session)

    # Configure context manager
    session_factory.return_value.__enter__ = MagicMock(
        return_value=mock_session
    )
    session_factory.return_value.__exit__ = MagicMock(
        return_value=None
    )

    service = ArticleService(
        article_crud=MagicMock(),
        session_factory=session_factory
    )

    # Service method should use session properly
    service.get_article(1)

    # Verify session was used in context manager
    session_factory.return_value.__enter__.assert_called_once()
    session_factory.return_value.__exit__.assert_called_once()
```

## Testing Complex Business Logic

### Multi-Step Operations
```python
def test_complex_workflow():
    # Setup multiple mocks
    mock_article_crud = MagicMock(spec=ArticleCRUD)
    mock_entity_crud = MagicMock(spec=EntityCRUD)
    mock_extractor = MagicMock(spec=EntityExtractor)

    # Configure mock behaviors
    mock_article_crud.get.return_value = Article(
        id=1,
        title="Test Article",
        content="Apple announced new products"
    )
    mock_extractor.extract.return_value = [
        {"text": "Apple", "type": "ORG"}
    ]
    mock_entity_crud.create.return_value = Entity(
        id=1,
        name="Apple",
        type="ORG"
    )

    service = EntityExtractionService(
        article_crud=mock_article_crud,
        entity_crud=mock_entity_crud,
        entity_extractor=mock_extractor,
        session_factory=lambda: MagicMock()
    )

    # Test the workflow
    entities = service.extract_entities_from_article(1)

    # Verify all steps were executed
    assert len(entities) == 1
    assert entities[0].name == "Apple"
    mock_article_crud.get.assert_called_once()
    mock_extractor.extract.assert_called_once()
    mock_entity_crud.create.assert_called_once()
```

## Testing Error Handling

### Handling CRUD Errors
```python
def test_service_handles_not_found():
    mock_crud = MagicMock(spec=ArticleCRUD)
    mock_crud.get.return_value = None  # Simulate not found

    service = ArticleService(
        article_crud=mock_crud,
        session_factory=lambda: MagicMock()
    )

    with pytest.raises(ValueError, match="Article not found"):
        service.process_article(999)
```

### Handling External Service Errors
```python
def test_service_handles_external_failure():
    mock_scraper = MagicMock(spec=WebScraper)
    mock_scraper.scrape.side_effect = Exception("Network error")

    service = ScrapingService(
        web_scraper=mock_scraper,
        session_factory=lambda: MagicMock()
    )

    with pytest.raises(ServiceError, match="Failed to scrape"):
        service.scrape_url("http://example.com")
```

## Testing Async Services

### Basic Async Service Testing
```python
from unittest.mock import AsyncMock, MagicMock
import pytest

@pytest.mark.asyncio
async def test_async_service_method():
    # Mock async dependencies
    mock_client = AsyncMock()
    mock_client.fetch_data.return_value = {"data": "test"}

    service = AsyncDataService(
        client=mock_client,
        session_factory=lambda: MagicMock()
    )

    # Test async method
    result = await service.get_remote_data("test-id")

    assert result == {"data": "test"}
    mock_client.fetch_data.assert_awaited_once_with("test-id")
```

### Testing Async Webhook Service
```python
@pytest.mark.asyncio
async def test_async_webhook_service():
    # Mock async session
    mock_session = MagicMock()
    mock_session.execute = AsyncMock()
    mock_session.add = MagicMock()
    mock_session.flush = AsyncMock()
    mock_session.commit = AsyncMock()
    mock_session.rollback = AsyncMock()

    # Create service
    service = ApifyWebhookServiceAsync(
        session=mock_session,
        webhook_secret="test-secret"
    )

    # Test webhook processing
    webhook_data = {
        "eventType": "ACTOR.RUN.SUCCEEDED",
        "actorId": "test-actor",
        "runId": "test-run",
        "data": {"results": ["item1", "item2"]}
    }

    result = await service.process_webhook(webhook_data)

    assert result["status"] == "processed"
    assert "webhook_id" in result
    mock_session.flush.assert_awaited_once()
```

### Testing Async Database Operations
```python
@pytest.mark.asyncio
async def test_async_service_with_database():
    # Mock async CRUD
    mock_crud = MagicMock()
    mock_crud.create = AsyncMock(return_value=Article(id=1, title="Test"))
    mock_crud.get = AsyncMock(return_value=Article(id=1, title="Test"))

    # Mock async session
    mock_session = MagicMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = Article(id=1, title="Test")
    mock_session.execute = AsyncMock(return_value=mock_result)

    service = AsyncArticleService(
        article_crud=mock_crud,
        session=mock_session
    )

    # Test create operation
    created = await service.create_article({"title": "Test"})
    assert created.id == 1

    # Test get operation
    fetched = await service.get_article(1)
    assert fetched.title == "Test"
```

### Testing Async Error Handling
```python
@pytest.mark.asyncio
async def test_async_service_error_handling():
    # Mock session with rollback
    mock_session = MagicMock()
    mock_session.add = MagicMock()
    mock_session.flush = AsyncMock(side_effect=Exception("Database error"))
    mock_session.rollback = AsyncMock()

    service = ApifyWebhookServiceAsync(session=mock_session)

    # Test that errors are handled properly
    with pytest.raises(Exception, match="Database error"):
        await service.process_webhook({"eventType": "test"})

    # Verify rollback was called
    mock_session.rollback.assert_awaited_once()
```

### Testing Concurrent Async Operations
```python
@pytest.mark.asyncio
async def test_concurrent_async_operations():
    # Mock async operations with delays
    import asyncio

    async def delayed_response(delay, value):
        await asyncio.sleep(delay)
        return value

    mock_client = MagicMock()
    mock_client.fetch_item = AsyncMock(
        side_effect=lambda id: delayed_response(0.1, {"id": id, "data": f"item{id}"})
    )

    service = AsyncBatchService(client=mock_client)

    # Test concurrent fetching
    items = await service.fetch_multiple_items([1, 2, 3, 4, 5])

    assert len(items) == 5
    assert all(item["id"] in [1, 2, 3, 4, 5] for item in items)
    assert mock_client.fetch_item.await_count == 5
```

### Testing Async Context Managers
```python
@pytest.mark.asyncio
async def test_async_context_manager():
    # Mock async context manager
    mock_session = MagicMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    mock_session.execute = AsyncMock()

    async def mock_get_session():
        return mock_session

    service = AsyncServiceWithContextManager(
        session_factory=mock_get_session
    )

    # Test that context manager is used properly
    await service.process_data()

    mock_session.__aenter__.assert_awaited_once()
    mock_session.__aexit__.assert_awaited_once()
```

## Testing Service Initialization

### Testing Dependency Injection
```python
def test_service_initialization():
    # Test that service initializes with all required dependencies
    service = ArticleService(
        article_crud=MagicMock(spec=ArticleCRUD),
        entity_crud=MagicMock(spec=EntityCRUD),
        session_factory=lambda: MagicMock()
    )

    assert service.article_crud is not None
    assert service.entity_crud is not None
    assert callable(service.session_factory)
```

## Testing Data Transformations

### Testing Service Data Processing
```python
def test_data_transformation():
    mock_crud = MagicMock(spec=ArticleCRUD)
    mock_crud.get_all.return_value = [
        Article(id=1, title="Article 1", published_at=datetime.now()),
        Article(id=2, title="Article 2", published_at=datetime.now())
    ]

    service = ReportingService(
        article_crud=mock_crud,
        session_factory=lambda: MagicMock()
    )

    # Test data transformation
    report = service.generate_summary_report()

    assert report["total_articles"] == 2
    assert len(report["articles"]) == 2
    assert all("summary" in article for article in report["articles"])
```

## Common Patterns

### 1. Testing Pagination
```python
def test_paginated_results():
    mock_crud = MagicMock(spec=ArticleCRUD)
    mock_crud.get_paginated.return_value = (
        [Article(id=1), Article(id=2)],  # items
        10  # total count
    )

    service = ArticleService(
        article_crud=mock_crud,
        session_factory=lambda: MagicMock()
    )

    result = service.get_articles_page(page=1, size=2)

    assert result["total"] == 10
    assert len(result["items"]) == 2
    assert result["page"] == 1
```

### 2. Testing Caching
```python
def test_service_caching():
    mock_crud = MagicMock(spec=ArticleCRUD)
    mock_crud.get.return_value = Article(id=1, title="Test")

    service = CachedArticleService(
        article_crud=mock_crud,
        session_factory=lambda: MagicMock()
    )

    # First call should hit the database
    article1 = service.get_article_cached(1)
    assert mock_crud.get.call_count == 1

    # Second call should use cache
    article2 = service.get_article_cached(1)
    assert mock_crud.get.call_count == 1  # Still 1
    assert article1 == article2
```

### 3. Testing Batch Operations
```python
def test_batch_processing():
    mock_crud = MagicMock(spec=ArticleCRUD)
    processed_ids = []

    def process_side_effect(session, article_id):
        processed_ids.append(article_id)
        return Article(id=article_id, processed=True)

    mock_crud.update.side_effect = process_side_effect

    service = BatchProcessingService(
        article_crud=mock_crud,
        session_factory=lambda: MagicMock()
    )

    # Test batch processing
    results = service.process_batch([1, 2, 3, 4, 5])

    assert len(results) == 5
    assert processed_ids == [1, 2, 3, 4, 5]
    assert all(r.processed for r in results)
```

## Best Practices

1. **Mock at the right level** - Mock CRUD operations, not SQLModel queries
2. **Test business logic, not infrastructure** - Focus on what the service does
3. **Use spec parameter** - `MagicMock(spec=ClassName)` catches typos
4. **Test edge cases** - Empty lists, None values, invalid inputs
5. **Verify mock interactions** - Use `assert_called_once_with()`
6. **Keep tests independent** - No shared state between tests
7. **Test error conditions** - Both expected and unexpected errors
8. **Use descriptive variable names** - Make tests self-documenting

## Anti-patterns to Avoid

1. **Don't test implementation details** - Test behavior, not internal methods
2. **Don't use real database connections** - Always mock the session
3. **Don't create complex mock chains** - Keep mocks simple and focused
4. **Don't skip error testing** - Services should handle failures gracefully
5. **Don't mix unit and integration tests** - Keep them separate

## Async Service Testing Best Practices

1. **Always use AsyncMock for async methods** - Regular MagicMock won't work
2. **Don't forget to await** - Missing await will return coroutines, not results
3. **Mock at the session level** - Mock session.execute, not the entire SQLAlchemy stack
4. **Test error paths with rollback** - Ensure async transactions are rolled back on error
5. **Use pytest.mark.asyncio** - Required for all async test functions
6. **Mock both __aenter__ and __aexit__** - When testing async context managers
7. **Test concurrent operations** - Verify services handle concurrent requests properly
8. **Verify awaited calls** - Use assert_awaited_once() instead of assert_called_once()

### Common Async Testing Gotchas

```python
# Wrong - Returns coroutine, not result
mock.method.return_value = async_function()

# Correct - Returns the actual value
mock.method.return_value = {"result": "data"}

# Wrong - Forgot to mock as async
mock_session.execute = MagicMock()

# Correct - Mock as async
mock_session.execute = AsyncMock()

# Wrong - Not awaiting in test
result = service.async_method()

# Correct - Await the result
result = await service.async_method()
```

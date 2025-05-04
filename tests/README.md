# Testing with Injectable Pattern

## Mocking Sessions

When testing services that use the injectable pattern, you need to properly mock the session factory and its behavior. Here's how to do it correctly:

```python
@pytest.fixture
def mock_db_session():
    """Create a mock database session."""
    return MagicMock()

@pytest.fixture
def mock_session_factory(mock_db_session):
    """Create a mock session factory that returns a context manager with the mock session."""
    mock_context = MagicMock()
    mock_context.__enter__.return_value = mock_db_session
    
    mock_factory = MagicMock()
    mock_factory.return_value = mock_context
    return mock_factory
```

## Testing Services

When testing services with the injectable pattern, provide all required dependencies including the session factory:

```python
# Create service with properly mocked dependencies
service = YourService(
    some_crud=mock_some_crud,
    another_crud=mock_another_crud,
    session_factory=mock_session_factory
)
```

## Assertions

When making assertions about database operations, use the mock_db_session directly:

```python
# Assert
mock_some_crud.get.assert_called_once_with(mock_db_session, id=1)
```

This ensures the test verifies that the session passed to CRUD methods is the one returned by `__enter__()` from your session context manager.

## Common Issues

### Session Context Manager Issues

If you get assertion errors that look like:

```
Expected: get_by_feed_id(<MagicMock name='mock()' id='140148773124624'>, feed_id=1, skip=0, limit=100)
Actual: get_by_feed_id(<MagicMock name='mock().__enter__()' id='140148773110752'>, feed_id=1, skip=0, limit=100)
```

It means your test is trying to verify a method was called with the raw session, but the actual code is using the session from the context manager's `__enter__()` method. Fix this by setting up your mock_session_factory correctly as shown above.

### Container Dependency

If tests were previously using `container` as a constructor parameter, you'll need to update them since injectable services no longer accept a container parameter. Instead:

1. Remove the `container` parameter from service constructor calls in tests
2. Make sure all required dependencies are provided explicitly
3. Skip tests that specifically test container-based functionality, or update them to test the new mechanism

For example:

```python
# Before
service = RSSFeedService(
    rss_feed_crud=mock_rss_feed_crud,
    feed_processing_log_crud=mock_feed_processing_log_crud,
    article_service=None,  # Using container to get this
    session_factory=mock_session_factory,
    container=mock_container  # No longer supported!
)

# After
service = RSSFeedService(
    rss_feed_crud=mock_rss_feed_crud,
    feed_processing_log_crud=mock_feed_processing_log_crud,
    article_service=mock_article_service,  # Must provide explicitly
    session_factory=mock_session_factory
)
```

## CI Testing

When updating tests for the injectable pattern, make incremental changes and run tests locally before pushing. If you get unexpected failures in CI, check the logs to see which tests are failing and why.
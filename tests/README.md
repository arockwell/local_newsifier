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
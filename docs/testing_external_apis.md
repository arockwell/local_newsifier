# Testing External API Integrations

This document provides comprehensive guidance on testing components that interact with external APIs, with strategies for both DIContainer and fastapi-injectable approaches.

## Testing Strategies

### 1. Test Mode Pattern

The test mode pattern allows components to automatically detect when they're running in a test environment and provide mock responses without making real API calls. This pattern is currently implemented in the ApifyService.

#### Implementation

```python
class ExternalApiService:
    def __init__(self, token=None, test_mode=False):
        self._token = token
        # Detect test environment
        self.test_mode = test_mode or settings.is_test_mode() or os.environ.get("PYTEST_CURRENT_TEST") is not None
        self._client = None
    
    def call_api_method(self, param):
        # In test mode, return mock data
        if self.test_mode and not self._token:
            return {"mock": "data", "param": param}
            
        # Make the actual API call
        return self.client.make_request(param)
```

#### Benefits

- Tests run without requiring real API credentials
- Tests are faster since no network calls are made
- Tests are more reliable and deterministic
- CI environments can run tests without configuration secrets

### 2. Centralized Test Mode Detection

As seen in the current codebase, centralizing test mode detection provides consistency:

```python
# In settings.py
class Settings(BaseSettings):
    # ...
    
    def is_test_mode(self) -> bool:
        """Check if we're running in a test environment."""
        import os
        return os.environ.get("PYTEST_CURRENT_TEST") is not None
```

This allows consistent test detection across all services:

```python
# In a service
self.test_mode = test_mode or settings.is_test_mode()
```

### 3. Test Fixtures

#### For DIContainer Components

```python
@pytest.fixture
def mock_container_with_api_service():
    """Fixture providing a container with mocked API service."""
    container = DIContainer()
    
    # Create mock API service
    mock_api_service = MagicMock()
    mock_api_service.call_api_method.return_value = {"mock": "response"}
    
    # Register in container
    container.register("external_api_service", mock_api_service)
    
    return container, mock_api_service

def test_flow_using_api(mock_container_with_api_service):
    container, mock_api_service = mock_container_with_api_service
    
    # Create component with container
    flow = ApiDependentFlow(container=container)
    
    # Test the flow
    result = flow.process_data("test")
    
    # Verify the API was called
    mock_api_service.call_api_method.assert_called_once_with("test")
```

#### For Injectable Components

```python
@pytest.fixture
def mock_injectable_api_service(monkeypatch):
    """Fixture providing mocked injectable API service."""
    mock_api_service = MagicMock()
    mock_api_service.call_api_method.return_value = {"mock": "response"}
    
    # Patch the provider function
    monkeypatch.setattr(
        "local_newsifier.di.providers.get_external_api_service",
        lambda: mock_api_service
    )
    
    return mock_api_service

def test_flow_using_injectable_api(mock_injectable_api_service):
    # Create component directly with mock
    flow = InjectableApiDependentFlow(api_service=mock_injectable_api_service)
    
    # Test the flow
    result = flow.process_data("test")
    
    # Verify the API was called
    mock_injectable_api_service.call_api_method.assert_called_once_with("test")
```

### 4. Mocking Response Strategies

#### Static Mock Responses

```python
def get_mock_response(method_name, params=None):
    """Get a static mock response based on the method name."""
    responses = {
        "get_user": {"id": 1, "name": "Test User"},
        "get_items": [{"id": 1, "name": "Item 1"}, {"id": 2, "name": "Item 2"}],
        "create_item": {"id": 3, "success": True}
    }
    
    return responses.get(method_name, {"error": "Method not mocked"})
```

#### Dynamic Mock Responses

```python
class MockResponseGenerator:
    """Generate realistic mock responses for external APIs."""
    
    def __init__(self):
        self.items = {}
        self.next_id = 1
    
    def get_item(self, item_id):
        """Simulate getting an item by ID."""
        return self.items.get(str(item_id), {"error": "Not found"})
    
    def create_item(self, data):
        """Simulate creating an item with side effects."""
        item_id = str(self.next_id)
        self.next_id += 1
        
        item = {"id": item_id, **data}
        self.items[item_id] = item
        
        return {"id": item_id, "success": True}
    
    def list_items(self):
        """Return all items."""
        return list(self.items.values())
```

### 5. Testing Error Scenarios

Testing error handling is crucial for external API integrations. Cover these scenarios:

```python
def test_api_authentication_error():
    """Test handling of authentication errors."""
    service = ExternalApiService(token="invalid_token", test_mode=False)
    
    # Mock the client to raise an auth error
    mock_client = MagicMock()
    mock_client.make_request.side_effect = AuthenticationError("Invalid token")
    service._client = mock_client
    
    # Verify error handling
    result = service.call_api_method("test")
    assert "error" in result
    assert "authentication" in result["error"].lower()

def test_api_rate_limit_error():
    """Test handling of rate limit errors."""
    service = ExternalApiService(token="valid_token", test_mode=False)
    
    # Mock the client to raise a rate limit error
    mock_client = MagicMock()
    mock_client.make_request.side_effect = RateLimitError("Too many requests")
    service._client = mock_client
    
    # Verify error handling
    result = service.call_api_method("test")
    assert "error" in result
    assert "rate limit" in result["error"].lower()

def test_api_network_error():
    """Test handling of network errors."""
    service = ExternalApiService(token="valid_token", test_mode=False)
    
    # Mock the client to raise a network error
    mock_client = MagicMock()
    mock_client.make_request.side_effect = ConnectionError("Network error")
    service._client = mock_client
    
    # Verify error handling
    result = service.call_api_method("test")
    assert "error" in result
    assert "network" in result["error"].lower() or "connection" in result["error"].lower()
```

### 6. Integration Testing

For true integration tests that call the real API:

```python
@pytest.mark.integration
@pytest.mark.skipif(not os.environ.get("REAL_API_TESTING"), reason="Real API testing disabled")
def test_real_api_integration():
    """Test with the real API (only runs when explicitly enabled)."""
    # Get token from environment variable
    token = os.environ.get("API_TOKEN")
    if not token:
        pytest.skip("API_TOKEN environment variable not set")
    
    # Create real service
    service = ExternalApiService(token=token, test_mode=False)
    
    # Make actual API call
    result = service.call_api_method("test_parameter")
    
    # Basic verification without specific response expectations
    assert result is not None
    assert "error" not in result
```

## Testing Approaches by Component Type

### 1. Testing Primary API Services

Based on the current ApifyService implementation, focus on:
- Authentication and token handling
- Response parsing and normalization
- Error handling for different API error types
- Automatic test mode detection and behavior

```python
class TestExternalApiService:
    def test_initialization(self):
        """Test service initialization."""
        service = ExternalApiService(token="test_token")
        assert service._token == "test_token"
        assert service._client is None
        assert service.test_mode is True  # In pytest environment
    
    def test_client_initialization(self):
        """Test client initialization."""
        service = ExternalApiService(token="test_token")
        client = service.client  # This should initialize the client
        assert service._client is not None
    
    def test_api_call_success(self, monkeypatch):
        """Test successful API call."""
        # Mock the API client
        mock_client = MagicMock()
        mock_client.make_request.return_value = {"success": True, "data": "test"}
        
        service = ExternalApiService(token="test_token")
        service._client = mock_client
        
        # Test the call
        result = service.call_api_method("param")
        
        # Verify
        mock_client.make_request.assert_called_once_with("param")
        assert result["success"] is True
        assert result["data"] == "test"
    
    def test_api_call_error_handling(self, monkeypatch):
        """Test API call error handling."""
        # Mock the API client
        mock_client = MagicMock()
        mock_client.make_request.side_effect = Exception("API error")
        
        service = ExternalApiService(token="test_token")
        service._client = mock_client
        
        # Test the call with error
        result = service.call_api_method("param")
        
        # Verify error is handled
        assert "error" in result
        assert "API error" in result["error"]
```

### 2. Testing Configuration Services

Focus on:
- CRUD operations for API configurations
- Configuration validation
- Database interaction for storing configurations

```python
class TestApiConfigService:
    def test_get_config(self, mock_session):
        """Test getting a configuration."""
        # Setup
        mock_crud = MagicMock()
        mock_crud.get.return_value = {"id": 1, "name": "Test Config"}
        
        service = ApiConfigService(
            session=mock_session,
            config_crud=mock_crud
        )
        
        # Execute
        result = service.get_config(1)
        
        # Verify
        mock_crud.get.assert_called_once_with(mock_session, id=1)
        assert result["id"] == 1
        assert result["name"] == "Test Config"
    
    def test_create_config(self, mock_session):
        """Test creating a configuration."""
        # Setup
        mock_crud = MagicMock()
        mock_crud.create.return_value = {"id": 1, "name": "New Config"}
        
        service = ApiConfigService(
            session=mock_session,
            config_crud=mock_crud
        )
        
        # Execute
        config_data = {"name": "New Config", "api_key": "key123"}
        result = service.create_config(config_data)
        
        # Verify
        mock_crud.create.assert_called_once_with(mock_session, config_data)
        assert result["id"] == 1
        assert result["name"] == "New Config"
```

### 3. Testing Domain-Specific Services

Focus on:
- Business logic using the API
- Orchestration of multiple API calls
- Error handling and fallbacks
- Integration with other services

```python
class TestApiBusinessService:
    def test_process_data(self):
        """Test processing data using the API."""
        # Mock dependencies
        mock_api_service = MagicMock()
        mock_api_service.call_api_method.return_value = {"data": [1, 2, 3]}
        
        mock_config_service = MagicMock()
        mock_config_service.get_config.return_value = {"api_key": "key123"}
        
        # Create service with mocks
        service = ApiBusinessService(
            api_service=mock_api_service,
            config_service=mock_config_service
        )
        
        # Execute
        result = service.process_data("test_source")
        
        # Verify
        mock_config_service.get_config.assert_called_once_with("test_source")
        mock_api_service.call_api_method.assert_called_once()
        assert result is not None
```

## Real-World Example: Testing Apify Integration

This section shows how to test the Apify integration based on the current implementation in the codebase:

```python
class TestApifyService:
    def test_initialization(self):
        """Test service initialization."""
        service = ApifyService(token="test_token")
        assert service._token == "test_token"
        assert service._client is None
        assert service.test_mode is True  # In pytest environment
    
    def test_client_initialization(self):
        """Test client initialization with token."""
        with patch("apify_client.ApifyClient") as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            
            service = ApifyService(token="test_token")
            client = service.client  # This initializes the client
            
            mock_client_class.assert_called_once_with("test_token")
            assert service._client is mock_client
    
    def test_run_actor_in_test_mode(self):
        """Test running an actor in test mode."""
        # Ensure we're in test mode
        service = ApifyService(test_mode=True)
        
        # Test running an actor
        result = service.run_actor("test_actor", {"param": "value"})
        
        # Verify mock response
        assert result["id"] == "test_run_test_actor"
        assert result["actId"] == "test_actor"
        assert result["status"] == "SUCCEEDED"
        assert "defaultDatasetId" in result
    
    def test_get_dataset_items_in_test_mode(self):
        """Test getting dataset items in test mode."""
        # Ensure we're in test mode
        service = ApifyService(test_mode=True)
        
        # Test getting dataset items
        result = service.get_dataset_items("test_dataset")
        
        # Verify mock response
        assert "items" in result
        assert len(result["items"]) > 0
        assert "url" in result["items"][0]
        assert "title" in result["items"][0]
    
    @patch("apify_client.ApifyClient")
    def test_run_actor_with_real_client(self, mock_client_class):
        """Test running an actor with mocked client."""
        # Setup
        mock_client = Mock()
        mock_actor = Mock()
        mock_client.actor.return_value = mock_actor
        mock_actor.call.return_value = {"data": "test_result"}
        
        mock_client_class.return_value = mock_client
        
        # Create service with test token but not in test mode
        service = ApifyService(token="test_token", test_mode=False)
        
        # Test running an actor
        result = service.run_actor("test_actor", {"param": "value"})
        
        # Verify
        mock_client.actor.assert_called_once_with("test_actor")
        mock_actor.call.assert_called_once_with(run_input={"param": "value"})
        assert result == {"data": "test_result"}
```

## Best Practices

1. **Consistent Test Mode Detection**
   - Always use `settings.is_test_mode()` for detecting test environments
   - Follow the pattern established in ApifyService for automatic test detection

2. **Safe Token Handling**
   - Never require real API tokens in tests
   - Implement automatic fallback to dummy tokens in test mode

3. **Mock All External Dependencies**
   - Always mock API clients and external services in unit tests
   - Separate true integration tests with clear markers (`@pytest.mark.integration`)

4. **Thorough Error Handling Tests**
   - Mock different types of errors (auth, network, rate limits)
   - Verify your service handles errors gracefully
   - Test all error recovery paths

5. **Realistic Mock Responses**
   - Mock responses should match actual API structure
   - Include all fields your code depends on
   - Structure mock data to test edge cases

6. **Explicit Test Parameters**
   - Use pytest.mark.parametrize for testing different inputs
   - Test edge cases and boundary conditions

7. **Performance Considerations**
   - Keep tests fast by avoiding unnecessary API calls
   - Use dependency injection to replace real clients with mocks
   - Consider caching fixtures for expensive setup operations

## Conclusion

Testing external API integrations requires a structured approach that balances thoroughness with efficiency. By implementing test mode in your services and using proper mocking strategies, you can ensure your API integrations are reliable, maintainable, and easily testable in any environment.
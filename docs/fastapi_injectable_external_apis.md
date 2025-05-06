# External API Integration with fastapi-injectable

This guide explains how to integrate external APIs using fastapi-injectable in the Local Newsifier project.

## Service Structure Pattern

For a clean external API integration with fastapi-injectable, follow this pattern:

1. **Primary API Service**: Direct API communication
```python
@injectable(use_cache=False)
class ExternalApiService:
    def __init__(self, token: Optional[str] = None):
        self._token = token
        self._client = None
    
    @property
    def client(self):
        if self._client is None:
            token = self._token or settings.EXTERNAL_API_TOKEN
            self._client = ExternalApiClient(token)
        return self._client
    
    def make_request(self, endpoint, data):
        return self.client.call(endpoint, data)
```

2. **Configuration Service**: For persistent API configurations
```python
@injectable(use_cache=False)
class ApiConfigService:
    def __init__(
        self,
        session: Annotated[Session, Depends(get_session)],
        config_crud: Annotated[ConfigCRUD, Depends(get_config_crud)]
    ):
        self.session = session
        self.config_crud = config_crud
        self.session_factory = lambda: session
    
    def get_config(self, config_id: int):
        return self.config_crud.get(self.session, id=config_id)
```

3. **Domain-Specific Service**: Business functionality using the API
```python
@injectable(use_cache=False)
class BusinessService:
    def __init__(
        self,
        api_service: Annotated[ExternalApiService, Depends(get_external_api_service)],
        config_service: Annotated[ApiConfigService, Depends(get_api_config_service)],
        session: Annotated[Session, Depends(get_session)]
    ):
        self.api_service = api_service
        self.config_service = config_service
        self.session = session
```

## Provider Functions

Register service dependencies with provider functions:

```python
# In providers.py
@injectable(use_cache=False)
def get_external_api_service():
    """Provide the external API service.
    
    Uses use_cache=False to create new instances for each injection, as it
    interacts with external APIs that require fresh client instances.
    """
    from my_project.services.external_api_service import ExternalApiService
    return ExternalApiService()

@injectable(use_cache=False)
def get_api_config_service(
    session: Annotated[Session, Depends(get_session)],
    config_crud: Annotated[ConfigCRUD, Depends(get_config_crud)]
):
    """Provide API configuration service."""
    from my_project.services.api_config_service import ApiConfigService
    return ApiConfigService(
        session=session,
        config_crud=config_crud
    )
```

## Testing External API Services

1. **Create a test mode detection method**:
```python
# In settings.py
def is_test_mode(self) -> bool:
    """Check if we're running in a test environment."""
    import os
    return os.environ.get("PYTEST_CURRENT_TEST") is not None
```

2. **Implement test mode in the service**:
```python
@injectable(use_cache=False)
class ExternalApiService:
    def __init__(self, token: Optional[str] = None, test_mode: bool = False):
        self._token = token
        self._client = None
        self.test_mode = test_mode or settings.is_test_mode()
    
    def make_request(self, endpoint, data):
        # For unit tests, provide mock responses
        if self.test_mode:
            return {"mock_response": True, "data": data}
        
        # Otherwise make the real API call
        return self.client.call(endpoint, data)
```

3. **Unit test with mocks**:
```python
def test_api_service(monkeypatch):
    # Create service directly with test_mode=True
    service = ExternalApiService(test_mode=True)
    
    # Use the service in test mode (no actual API calls)
    result = service.make_request("endpoint", {"test": "data"})
    
    # Verify mock response
    assert result["mock_response"] is True
    assert result["data"]["test"] == "data"
```

4. **Test with dependency mocking**:
```python
def test_business_service(monkeypatch):
    # Mock the API service
    mock_api = MagicMock()
    mock_api.make_request.return_value = {"success": True}
    
    # Patch the provider
    monkeypatch.setattr(
        "my_project.di.providers.get_external_api_service",
        lambda: mock_api
    )
    
    # Create the service using the mocked dependency
    service = BusinessService(
        api_service=mock_api,
        config_service=MagicMock(),
        session=MagicMock()
    )
    
    # Test the service
    result = service.process_data("test")
    
    # Verify the mocked API was called
    mock_api.make_request.assert_called_once()
```

## Real-World Example: Apify Integration

Based on current implementation:

```python
# In providers.py
@injectable(use_cache=False)
def get_apify_service():
    """Provide the Apify service.
    
    Uses use_cache=False to create new instances for each injection, as it
    interacts with external APIs that require fresh client instances.
    """
    from local_newsifier.services.apify_service import ApifyService
    return ApifyService()

# In apify_service.py
class ApifyService:
    def __init__(self, token: Optional[str] = None, test_mode: bool = False):
        self._token = token
        self._client = None
        self.test_mode = test_mode or settings.is_test_mode()
    
    def run_actor(self, actor_id: str, run_input: Dict[str, Any]) -> Dict[str, Any]:
        # In test mode, return mock data
        if self.test_mode and not self._token:
            return {
                "id": f"test_run_{actor_id}",
                "actId": actor_id,
                "status": "SUCCEEDED",
                "defaultDatasetId": f"test_dataset_{actor_id}"
            }
            
        # Otherwise, make the actual API call
        return self.client.actor(actor_id).call(run_input=run_input)
```

## Best Practices

1. **Always use `use_cache=False`** for external API services to ensure fresh instances

2. **Enable test mode detection** for safe testing without real API credentials

3. **Keep service responsibilities clear**:
   - Primary API Service: Direct API communication only
   - Configuration Service: Manage stored configurations
   - Domain-Specific Services: Implement business logic

4. **Provide minimal but complete mocks** for testing

5. **Handle errors gracefully** in all API operations
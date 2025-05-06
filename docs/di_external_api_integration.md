# DI Guide for External API Integration

## Overview

This guide provides a comprehensive approach to integrating external APIs with the dependency injection systems in Local Newsifier. It addresses common challenges during the transition period between the legacy DIContainer and fastapi-injectable, using Apify integration as a practical example.

## Integration Patterns

### 1. Service Responsibility Structure

When integrating external APIs, follow these guidelines to determine service boundaries:

```
External API Integration
├── Primary API Service (e.g., ApifyService)
│   ├── Responsibility: Direct API communication
│   ├── Scope: Authentication, raw API calls, response handling
│   └── Example: ApifyService manages Apify API client, tokens, error handling
├── Configuration Service (e.g., ApifySourceConfigService)
│   ├── Responsibility: Managing API configuration
│   ├── Scope: CRUD operations for configurations, validation
│   └── Example: ApifySourceConfigService manages Apify actor configurations
└── Domain-Specific Services (e.g., ApifySchedulingService)
    ├── Responsibility: Business logic using the API
    ├── Scope: Domain-specific operations, orchestration
    └── Example: ApifySchedulingService manages scheduled scraping tasks
```

**Decision Guide for Service Creation:**

1. **Primary API Service**: Create when first integrating with a new external API
   - Handles authentication, client initialization, token management
   - Provides methods mapping closely to the external API's functionality
   - Example: `ApifyService` for basic Apify API interactions

2. **Configuration Service**: Create when you need persistent configuration
   - Manages stored configurations for the API integration 
   - Handles database operations for configuration entities
   - Example: `ApifySourceConfigService` for managing scraper configurations

3. **Domain-Specific Services**: Create when implementing business features
   - Implements specific business use cases using the API
   - Orchestrates multiple operations with the primary service
   - Example: `ApifySchedulingService` for managing scheduled scraping jobs

### 2. Implementation Patterns

#### Legacy DIContainer Pattern

```python
# In container.py
container.register_factory(
    "apify_service", 
    lambda c: ApifyService(test_mode=(environment == "testing"))
)

container.register_factory(
    "apify_source_config_service",
    lambda c: ApifySourceConfigService(
        session_factory=c.get("session_factory"),
        config_crud=c.get("apify_source_config_crud")
    )
)

# In a component using the service
class RSSScrapingFlow:
    def __init__(self, container=None):
        from local_newsifier.container import container as default_container
        self.container = container or default_container
        self.apify_service = self.container.get("apify_service")
        self.apify_config_service = self.container.get("apify_source_config_service")
```

#### FastAPI-Injectable Pattern

```python
# In providers.py
@injectable(use_cache=False)
def get_apify_service():
    """Provide the Apify service.
    
    Uses use_cache=False to create new instances for each injection, as it
    interacts with external APIs that require fresh client instances.
    
    Returns:
        ApifyService instance
    """
    from local_newsifier.services.apify_service import ApifyService
    return ApifyService()

@injectable(use_cache=False)
def get_apify_source_config_service(
    session: Annotated[Session, Depends(get_session)],
    config_crud: Annotated[ApifySourceConfigCRUD, Depends(get_apify_source_config_crud)]
):
    """Provide Apify source configuration service."""
    from local_newsifier.services.apify_source_config_service import ApifySourceConfigService
    
    return ApifySourceConfigService(
        session=session,
        config_crud=config_crud
    )

# In a component using the service
@injectable(use_cache=False)
class InjectableRSSScrapingFlow:
    def __init__(
        self,
        apify_service: Annotated[ApifyService, Depends(get_apify_service)],
        apify_config_service: Annotated[ApifySourceConfigService, Depends(get_apify_source_config_service)]
    ):
        self.apify_service = apify_service
        self.apify_config_service = apify_config_service
```

### 3. Transition Period Strategy

During the transition between DIContainer and fastapi-injectable, follow these guidelines:

#### Option 1: Dual-Registration (Current Practice)

Register services in both systems to ensure smooth transition:

```python
# In container.py
container.register_factory(
    "apify_service", 
    lambda c: ApifyService(test_mode=(environment == "testing"))
)

# In providers.py
@injectable(use_cache=False)
def get_apify_service():
    """Provide the Apify service."""
    from local_newsifier.services.apify_service import ApifyService
    return ApifyService()
```

This dual-registration approach is currently in use for the Apify service as seen in the core repository code.

#### Option 2: Adapter-Based Integration

Use the adapter layer to make legacy components available in the new system:

```python
# In fastapi_injectable_adapter.py
register_service_factory("apify_service")

# This creates an injectable provider function from the container registration
```

#### Option 3: Injectable-First with Legacy Compatibility

Implement using injectable pattern with compatibility constructor:

```python
@injectable(use_cache=False)
class ApifySourceConfigService:
    def __init__(
        self,
        session: Annotated[Session, Depends(get_session)] = None,
        config_crud: Annotated[ApifySourceConfigCRUD, Depends(get_apify_source_config_crud)] = None,
        session_factory = None,
        container = None
    ):
        # Support for injectable pattern
        self.session = session
        self.config_crud = config_crud
        
        # Support for legacy container pattern
        if container is not None:
            from local_newsifier.container import container as default_container
            self.container = container or default_container
            self.session_factory = session_factory or self.container.get("session_factory")
            self.config_crud = self.config_crud or self.container.get("apify_source_config_crud")
        elif session is not None:
            # When used with injectable pattern
            self.session_factory = lambda: session
```

### 4. Testing Strategies

#### Testing with Legacy DIContainer

```python
def test_apify_service_with_container(monkeypatch):
    # Create test container
    container = DIContainer()
    
    # Mock dependencies
    mock_config_crud = MagicMock()
    container.register("apify_source_config_crud", mock_config_crud)
    
    # Register service with test container
    container.register_factory(
        "apify_source_config_service",
        lambda c: ApifySourceConfigService(
            session_factory=lambda: MagicMock(),
            config_crud=c.get("apify_source_config_crud")
        )
    )
    
    # Create service from container
    service = container.get("apify_source_config_service")
    
    # Test the service
    service.get_config(1)
    mock_config_crud.get.assert_called_once()
```

#### Testing with FastAPI-Injectable

```python
def test_apify_service_with_injectable(monkeypatch):
    # Mock dependencies
    mock_session = MagicMock()
    mock_config_crud = MagicMock()
    
    # Patch provider functions
    monkeypatch.setattr("local_newsifier.di.providers.get_session", lambda: mock_session)
    monkeypatch.setattr(
        "local_newsifier.di.providers.get_apify_source_config_crud", 
        lambda: mock_config_crud
    )
    
    # Create service directly with dependencies 
    # This is cleaner than using the DI system in tests
    service = ApifySourceConfigService(
        session=mock_session,
        config_crud=mock_config_crud
    )
    
    # Test the service
    service.get_config(1)
    mock_config_crud.get.assert_called_once()
```

#### Testing External API Calls

Use a standardized approach to mocking external API calls:

```python
def test_apify_api_calls(monkeypatch):
    # Create mock client
    mock_client = MagicMock()
    mock_actor = MagicMock()
    mock_client.actor.return_value = mock_actor
    mock_actor.call.return_value = {"id": "test_run", "status": "SUCCESS"}
    
    # Patch the client creation
    monkeypatch.setattr("apify_client.ApifyClient", lambda token: mock_client)
    
    # Create service with test mode
    service = ApifyService(token="test_token")
    
    # Test API call
    result = service.run_actor("test_actor", {"param": "value"})
    
    # Verify interactions
    mock_client.actor.assert_called_once_with("test_actor")
    mock_actor.call.assert_called_once_with(run_input={"param": "value"})
    assert result["id"] == "test_run"
```

## Real-World Example: Apify Integration

The following section provides a practical example of integrating the Apify API using our DI systems, based on the actual current implementation in the codebase.

### 1. Primary API Service

```python
# apify_service.py
class ApifyService:
    """Service for interacting with the Apify API."""
    
    def __init__(self, token: Optional[str] = None, test_mode: bool = False):
        """Initialize the Apify service.
        
        Args:
            token: Optional token override. If not provided, uses settings.APIFY_TOKEN
            test_mode: If True, operates in test mode where token validation is skipped
        """
        self._token = token
        self._client = None
        # We use a public attribute for test_mode for better testability
        import os
        self.test_mode = test_mode or settings.is_test_mode() or os.environ.get("PYTEST_CURRENT_TEST") is not None
    
    @property
    def client(self) -> ApifyClient:
        """Get the Apify client."""
        if self._client is None:
            # For test mode, use a dummy token if not provided
            if self.test_mode and not self._token and not settings.APIFY_TOKEN:
                logging.warning("Running in test mode with dummy APIFY_TOKEN")
                token = "test_dummy_token"
            else:
                # Get token from settings if not provided
                token = self._token or settings.validate_apify_token()
                
            self._client = ApifyClient(token)
        return self._client
    
    def run_actor(self, actor_id: str, run_input: Dict[str, Any]) -> Dict[str, Any]:
        """Run an Apify actor."""
        # In test mode with no token, return a mock response
        if self.test_mode and not self._token and not settings.APIFY_TOKEN:
            logging.info(f"Test mode: Simulating run of actor {actor_id}")
            return {
                "id": f"test_run_{actor_id}",
                "actId": actor_id,
                "status": "SUCCEEDED",
                "defaultDatasetId": f"test_dataset_{actor_id}",
            }
            
        # Make the actual API call
        return self.client.actor(actor_id).call(run_input=run_input)
```

### 2. Current Registration in DI Systems

#### In container.py (Legacy DIContainer)

```python
# In container.py
container.register_factory(
    "apify_service", 
    lambda c: ApifyService(test_mode=(environment == "testing"))
)
```

#### In providers.py (FastAPI-Injectable)

```python
# In providers.py
@injectable(use_cache=False)
def get_apify_service():
    """Provide the Apify service.
    
    Uses use_cache=False to create new instances for each injection, as it
    interacts with external APIs that require fresh client instances.
    
    Returns:
        ApifyService instance
    """
    from local_newsifier.services.apify_service import ApifyService
    return ApifyService()
```

### 3. Example Domain-Specific Service

Here's an example of how a domain-specific service could be implemented using the ApifyService:

```python
# apify_scheduling_service.py
class ApifySchedulingService:
    """Service for managing scheduled Apify tasks."""
    
    def __init__(
        self,
        apify_service: Annotated[ApifyService, Depends(get_apify_service)],
        session: Annotated[Session, Depends(get_session)]
    ):
        """Initialize the scheduling service using the injectable pattern."""
        self.apify_service = apify_service
        self.session = session
        self.session_factory = lambda: session
    
    def create_scheduled_task(
        self, 
        source_id: str, 
        actor_id: str,
        schedule: str,
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a scheduled task on Apify."""
        # Create the scheduled task on Apify
        task_input = {
            "actorId": actor_id,
            "name": f"Scheduled task for {source_id}",
            "cronExpression": schedule,
            "defaultRunOptions": {"runInput": input_data}
        }
        result = self.apify_service.client.tasks().create(task_input)
        
        return result
    
    def list_scheduled_tasks(self) -> List[Dict[str, Any]]:
        """List all scheduled tasks."""
        try:
            # Get tasks from Apify
            tasks = self.apify_service.client.tasks().list()
            return tasks.get("items", [])
        except Exception as e:
            logging.error(f"Error getting tasks: {str(e)}")
            return []
```

### 4. Registering the Domain-Specific Service

#### In container.py (Legacy DIContainer)

```python
# In container.py
container.register_factory(
    "apify_scheduling_service",
    lambda c: ApifySchedulingService(
        apify_service=c.get("apify_service"),
        session_factory=c.get("session_factory")
    )
)
```

#### In providers.py (FastAPI-Injectable)

```python
# In providers.py
@injectable(use_cache=False)
def get_apify_scheduling_service(
    apify_service: Annotated[ApifyService, Depends(get_apify_service)],
    session: Annotated[Session, Depends(get_session)]
):
    """Provide Apify scheduling service."""
    from local_newsifier.services.apify_scheduling_service import ApifySchedulingService
    
    return ApifySchedulingService(
        apify_service=apify_service,
        session=session
    )
```

## Best Practices for External API Integration

### 1. Authentication and Configuration Management

- Store API tokens in environment variables, never hardcode in source
- Use settings with validation for token retrieval
- Create explicit test mode that doesn't require real credentials
- Handle authentication errors gracefully with meaningful messages

### 2. Service Structure

- Follow the principle of separation of concerns:
  - Primary API Service: Direct API communication
  - Configuration Service: Manage API configurations
  - Domain-Specific Services: Business logic using the API
- Limit service methods to single responsibility
- Use proper namespacing to avoid confusion with multiple APIs

### 3. Error Handling

- Implement robust error handling for all API calls
- Categorize and log different types of errors:
  - Authentication errors (invalid/expired tokens)
  - Rate limiting issues
  - Network problems
  - API-specific error responses
- Provide graceful degradation when APIs are unavailable

### 4. Testing

- Create a standardized test mode for all external APIs
- Provide realistic mock responses in test mode
- Test both successful and error scenarios
- Use consistent mocking patterns across all API services
- Avoid making real API calls in tests unless specifically testing integration

### 5. Dependency Injection Best Practices

- Always specify `use_cache=False` for API service injection to prevent stale client instances
- Provide clear, well-documented provider functions
- Consider token injection for flexibility in testing
- Register in both DI systems during transition as per current practice

### 6. Documentation

- Document all API services and their methods
- Include example usage for both DI approaches
- Clearly specify error handling expectations
- Document test mode behavior and mock responses

## DI Decision Making Guide

Use this decision flow to determine how to implement new API integrations:

```
Is this a new external API integration?
├── Yes → Implement with fastapi-injectable
│   └── Register in DIContainer too for backward compatibility
└── No → Is it an extension to an existing API service?
    ├── Yes → Which DI system does the existing service use?
    │   ├── DIContainer → Add to DIContainer and also add injectable provider
    │   └── Injectable → Extend using injectable pattern
    └── No → Implement with fastapi-injectable
```

## Transitional Considerations

During the transition period between DIContainer and fastapi-injectable:

1. **New APIs**: Implement using fastapi-injectable AND register in DIContainer (dual-registration)
2. **Extensions to Existing APIs**: Follow the pattern of the original service and apply dual-registration
3. **Documentation**: Document both approaches during transition
4. **Container Registration**: Register API services in DIContainer for backwards compatibility
5. **Injectable Registration**: Always provide injectable provider functions for new services

## Conclusion

By following these patterns and best practices, you can successfully integrate external APIs with our dependency injection systems during this transition period. The Apify integration serves as a practical example that demonstrates these principles in action.
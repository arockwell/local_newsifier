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
    lambda c: ApifyService(token=settings.APIFY_TOKEN)
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
    """Provide Apify service for external API integration."""
    from local_newsifier.config.settings import settings
    from local_newsifier.services.apify_service import ApifyService
    return ApifyService(token=settings.APIFY_TOKEN)

@injectable(use_cache=False)
def get_apify_source_config_service(
    session: Annotated[Session, Depends(get_session)],
    config_crud: Annotated[ApifySourceConfigCRUD, Depends(get_apify_source_config_crud)]
):
    """Provide Apify source configuration service."""
    from local_newsifier.services.apify_source_config_service import ApifySourceConfigService
    
    return ApifySourceConfigService(
        session_factory=lambda: session,
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

#### Option 1: Dual-Registration (Recommended)

Register services in both systems to ensure smooth transition:

```python
# In container.py
container.register_factory(
    "apify_service",
    lambda c: ApifyService(token=settings.APIFY_TOKEN)
)

# In providers.py
@injectable(use_cache=False)
def get_apify_service():
    """Provide Apify service for external API integration."""
    from local_newsifier.config.settings import settings
    from local_newsifier.services.apify_service import ApifyService
    return ApifyService(token=settings.APIFY_TOKEN)
```

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

The following section provides a practical example of integrating the Apify API using our DI systems.

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
        self.test_mode = test_mode or settings.is_test_mode()
    
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
    
    def get_dataset_items(self, dataset_id: str, **kwargs) -> Dict[str, Any]:
        """Get items from an Apify dataset."""
        # In test mode with no token, return mock data
        if self.test_mode and not self._token and not settings.APIFY_TOKEN:
            logging.info(f"Test mode: Simulating dataset items for {dataset_id}")
            return {
                "items": [
                    {
                        "id": 1,
                        "url": "https://example.com/test",
                        "title": "Test Article",
                        "content": "This is test content for testing."
                    }
                ]
            }
            
        # Handle API call exceptions gracefully
        try:
            list_page = self.client.dataset(dataset_id).list_items(**kwargs)
            return self._extract_items(list_page)
        except Exception as e:
            logging.error(f"Error calling Apify API: {str(e)}")
            return {"items": [], "error": str(e)}
```

### 2. Configuration Service

```python
# apify_source_config_service.py
class ApifySourceConfigService:
    """Service for managing Apify source configurations."""
    
    def __init__(
        self, 
        session: Optional[Session] = None,
        config_crud: Optional[ApifySourceConfigCRUD] = None,
        session_factory = None,
        container = None
    ):
        """Initialize the Apify source config service.
        
        Supports both injectable and container patterns during transition.
        """
        # Handle injectable pattern
        self.session = session
        self.config_crud = config_crud
        
        # Handle container pattern (for backward compatibility)
        if container is not None or session_factory is not None:
            from local_newsifier.container import container as default_container
            self.container = container or default_container
            self.session_factory = session_factory or self.container.get("session_factory")
            self.config_crud = self.config_crud or self.container.get("apify_source_config_crud")
        elif session is not None:
            # Injectable mode with session
            self.session_factory = lambda: session
    
    def get_config(self, config_id: int) -> Optional[ApifySourceConfig]:
        """Get a configuration by ID."""
        with self.session_factory() as session:
            return self.config_crud.get(session, id=config_id)
    
    def create_config(self, data: Dict[str, Any]) -> ApifySourceConfig:
        """Create a new configuration."""
        with self.session_factory() as session:
            return self.config_crud.create(session, data)
    
    def get_configs_for_source(self, source_id: str) -> List[ApifySourceConfig]:
        """Get all configurations for a specific source."""
        with self.session_factory() as session:
            return self.config_crud.get_by_source_id(session, source_id)
    
    def update_config(self, config_id: int, data: Dict[str, Any]) -> Optional[ApifySourceConfig]:
        """Update a configuration."""
        with self.session_factory() as session:
            return self.config_crud.update(session, config_id, data)
    
    def delete_config(self, config_id: int) -> bool:
        """Delete a configuration."""
        with self.session_factory() as session:
            return self.config_crud.delete(session, config_id)
```

### 3. Domain-Specific Service

```python
# apify_scheduling_service.py
class ApifySchedulingService:
    """Service for managing scheduled Apify tasks."""
    
    def __init__(
        self,
        apify_service: Annotated[ApifyService, Depends(get_apify_service)],
        config_service: Annotated[ApifySourceConfigService, Depends(get_apify_source_config_service)],
        session: Annotated[Session, Depends(get_session)]
    ):
        """Initialize the scheduling service using the injectable pattern."""
        self.apify_service = apify_service
        self.config_service = config_service
        self.session = session
        self.session_factory = lambda: session
    
    def create_scheduled_task(
        self, 
        source_id: str, 
        actor_id: str,
        schedule: str,
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a scheduled task on Apify.
        
        Args:
            source_id: Identifier for the source
            actor_id: Apify actor ID
            schedule: Cron expression for the schedule
            input_data: Input data for the actor
            
        Returns:
            Dict containing the created task details
        """
        # Store configuration
        config = self.config_service.create_config({
            "source_id": source_id,
            "actor_id": actor_id,
            "schedule": schedule,
            "input_data": input_data
        })
        
        # Create the scheduled task on Apify
        task_input = {
            "actorId": actor_id,
            "name": f"Scheduled task for {source_id}",
            "cronExpression": schedule,
            "defaultRunOptions": {"runInput": input_data}
        }
        result = self.apify_service.client.tasks().create(task_input)
        
        # Update config with task ID
        self.config_service.update_config(config.id, {"task_id": result.get("id")})
        
        return result
    
    def list_scheduled_tasks(self) -> List[Dict[str, Any]]:
        """List all scheduled tasks."""
        configs = []
        with self.session_factory() as session:
            configs = session.exec(select(ApifySourceConfig)).all()
        
        results = []
        for config in configs:
            if config.task_id:
                # Get task details from Apify
                try:
                    task = self.apify_service.client.task(config.task_id).get()
                    results.append({
                        "config_id": config.id,
                        "source_id": config.source_id,
                        "actor_id": config.actor_id,
                        "task_id": config.task_id,
                        "schedule": config.schedule,
                        "last_run": task.get("lastRunStartedAt"),
                        "stats": task.get("stats")
                    })
                except Exception as e:
                    logging.error(f"Error getting task {config.task_id}: {str(e)}")
                    results.append({
                        "config_id": config.id,
                        "source_id": config.source_id,
                        "error": str(e)
                    })
        
        return results
```

### 4. Registration in Both DI Systems

#### In container.py (Legacy DIContainer)

```python
# Register the primary API service
container.register_factory(
    "apify_service",
    lambda c: ApifyService(token=settings.APIFY_TOKEN)
)

# Register the configuration service
container.register_factory(
    "apify_source_config_service",
    lambda c: ApifySourceConfigService(
        session_factory=c.get("session_factory"),
        config_crud=c.get("apify_source_config_crud")
    )
)

# Register the domain-specific service
container.register_factory(
    "apify_scheduling_service",
    lambda c: ApifySchedulingService(
        apify_service=c.get("apify_service"),
        config_service=c.get("apify_source_config_service"),
        session_factory=c.get("session_factory")
    )
)
```

#### In providers.py (FastAPI-Injectable)

```python
@injectable(use_cache=False)
def get_apify_service():
    """Provide Apify service for external API integration."""
    from local_newsifier.config.settings import settings
    from local_newsifier.services.apify_service import ApifyService
    return ApifyService(token=settings.APIFY_TOKEN)

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

@injectable(use_cache=False)
def get_apify_scheduling_service(
    apify_service: Annotated[ApifyService, Depends(get_apify_service)],
    config_service: Annotated[ApifySourceConfigService, Depends(get_apify_source_config_service)],
    session: Annotated[Session, Depends(get_session)]
):
    """Provide Apify scheduling service."""
    from local_newsifier.services.apify_scheduling_service import ApifySchedulingService
    
    return ApifySchedulingService(
        apify_service=apify_service,
        config_service=config_service,
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
- When in doubt, register in both DI systems during transition

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
│   └── Register in DIContainer only if existing components depend on it
└── No → Is it an extension to an existing API service?
    ├── Yes → Which DI system does the existing service use?
    │   ├── DIContainer → Add to DIContainer and consider adding injectable provider
    │   └── Injectable → Extend using injectable pattern
    └── No → Implement with fastapi-injectable
```

## Transitional Considerations

During the transition period between DIContainer and fastapi-injectable:

1. **New APIs**: Implement using fastapi-injectable with provider functions
2. **Extensions to Existing APIs**: Follow the pattern of the original service
3. **Documentation**: Document both approaches during transition
4. **Container Registration**: Register API services in DIContainer when components depend on them
5. **Injectable Registration**: Always provide injectable provider functions for new services

## Conclusion

By following these patterns and best practices, you can successfully integrate external APIs with our dependency injection systems during this transition period. The Apify integration serves as a practical example that demonstrates these principles in action.
# External API Integration Guide

This document outlines the best practices for integrating external APIs in the Local Newsifier project, with a focus on authentication, testing, and dependency injection.

## Authentication Pattern

### 1. Configuration in Settings

API credentials should be defined in `settings.py`:

```python
# In settings.py
class Settings(BaseSettings):
    # External API credentials
    EXTERNAL_API_TOKEN: Optional[str] = Field(default=None, description="Token for External API")
    
    def is_test_mode(self) -> bool:
        """Check if we're running in a test environment."""
        import os
        return os.environ.get("PYTEST_CURRENT_TEST") is not None
    
    def validate_external_api_token(self, skip_validation_in_test=False) -> str:
        """Validate that EXTERNAL_API_TOKEN is set and return it."""
        # Use the centralized test mode detection
        in_test_env = self.is_test_mode()
        
        # Skip validation if requested and in test mode
        if skip_validation_in_test and in_test_env:
            if not self.EXTERNAL_API_TOKEN:
                import logging
                logging.warning("Using dummy External API token for testing")
                return "test_dummy_token"
        
        # Standard validation
        if not self.EXTERNAL_API_TOKEN:
            raise ValueError(
                "EXTERNAL_API_TOKEN is required but not set. "
                "Please set the EXTERNAL_API_TOKEN environment variable."
            )
        return self.EXTERNAL_API_TOKEN
```

### 2. Service Implementation

Create a service class that handles all interactions with the external API:

```python
class ExternalApiService:
    """Service for interacting with the External API."""
    
    def __init__(self, token: Optional[str] = None, test_mode: bool = False):
        """Initialize the External API service.
        
        Args:
            token: Optional token override. If not provided, uses settings.EXTERNAL_API_TOKEN
            test_mode: If True, operates in test mode where token validation is skipped
        """
        self._token = token
        self._client = None
        # Use settings.is_test_mode() for consistent test mode detection
        self._test_mode = test_mode or settings.is_test_mode()
    
    @property
    def client(self):
        """Get the API client."""
        if self._client is None:
            # For test mode, use a dummy token if not provided
            if self._test_mode and not self._token and not settings.EXTERNAL_API_TOKEN:
                logging.warning("Running in test mode with dummy EXTERNAL_API_TOKEN")
                token = "test_dummy_token"
            else:
                # Get token from settings if not provided
                token = self._token or settings.validate_external_api_token()
                
            self._client = ExternalApiClient(token)
        return self._client
    
    def call_api_method(self, param):
        """Call an API method."""
        # In test mode with no token, return mock data
        if self._test_mode and not self._token and not settings.EXTERNAL_API_TOKEN:
            logging.info(f"Test mode: Simulating API call with {param}")
            return {"mock": "data", "param": param}
            
        # Make the actual API call
        return self.client.make_request(param)
```

## Testing Approach

### 1. Test Mode Detection

Always use the centralized `settings.is_test_mode()` method for detecting test environments:

```python
# Good
in_test_env = settings.is_test_mode()

# Bad - inconsistent test detection
in_test_env = os.environ.get("PYTEST_CURRENT_TEST") is not None
```

### 2. Mock Responses in Test Mode

Provide realistic mock responses in test mode:

```python
def get_data(self, resource_id):
    """Get data from the API."""
    # In test mode with no token, return mock data
    if self._test_mode and not self._token and not settings.EXTERNAL_API_TOKEN:
        return {
            "id": resource_id,
            "name": f"Test Resource {resource_id}",
            "data": "This is mock data for testing"
        }
        
    # Make the actual API call
    return self.client.get_resource(resource_id)
```

### 3. Writing Tests

Tests should work without requiring real API credentials:

```python
def test_external_api_service():
    # No token needed, test mode is auto-detected
    service = ExternalApiService()
    
    # Will return mock data, not make a real API call
    result = service.call_api_method("test_param")
    
    # Assert against the mock response structure
    assert "mock" in result
    assert result["param"] == "test_param"
```

## Dependency Injection Pattern

### 1. Legacy DIContainer Registration

Register the service with the container:

```python
# In container.py
container.register_factory(
    "external_api_service", 
    lambda c: ExternalApiService()
)
```

### 2. FastAPI-Injectable Provider

Define a provider for the service:

```python
# In providers.py
@injectable(use_cache=False)
def get_external_api_service(
    token: Annotated[Optional[str], Depends(get_api_token)]
):
    from local_newsifier.services.external_api_service import ExternalApiService
    return ExternalApiService(token=token)

@injectable(use_cache=False)
def get_api_token():
    """Get the API token, can be customized per-request."""
    from local_newsifier.config.settings import settings
    return settings.EXTERNAL_API_TOKEN
```

### 3. Using with FastAPI Endpoints

Create endpoints that use the service:

```python
# In routers/external_api.py
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from fastapi_injectable import Inject, injectable

router = APIRouter(prefix="/api/external", tags=["external-api"])

@router.get("/data/{resource_id}")
async def get_external_data(
    resource_id: str,
    external_api_service: Annotated[Any, Inject(get_external_api_service)]
):
    """Get data from external API."""
    try:
        data = external_api_service.get_data(resource_id)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"API error: {str(e)}")

# Example with customized token
@router.post("/admin/call-with-token")
async def call_with_custom_token(
    request_data: dict,
    admin_token: str,
    # Override the default API token with a custom one
    external_api_service: Annotated[Any, Depends(
        lambda: ExternalApiService(token=admin_token)
    )]
):
    """Call API with a custom token (admin only)."""
    # Validate admin permissions here
    result = external_api_service.call_api_method(request_data.get("param"))
    return result
```

### 4. Real Example: Apify Integration

The Local Newsifier project uses these patterns for Apify API integration:

```python
# In providers.py
@injectable(use_cache=False)
def get_apify_service(
    token: Annotated[Optional[str], Depends(get_apify_token)]
):
    """Get a fresh instance of the Apify service."""
    from local_newsifier.services.apify_service import ApifyService
    return ApifyService(token=token)

@injectable(use_cache=False)
def get_apify_token():
    """Get the Apify token from settings."""
    from local_newsifier.config.settings import settings
    return settings.APIFY_TOKEN

# In routers/scraping.py
@router.post("/scrape")
async def scrape_url(
    request: ScrapeRequest,
    apify_service: Annotated[ApifyService, Inject(get_apify_service)]
):
    """Scrape a URL using Apify."""
    result = apify_service.run_actor(
        "apify/web-scraper", 
        {"startUrls": [{"url": request.url}]}
    )
    return result
```

## CLI Command Pattern

Handle token validation in CLI commands:

```python
def _ensure_token():
    """Ensure the API token is set."""
    # Check if running in test mode
    if settings.is_test_mode():
        # In test mode, provide a default token if not set
        if not settings.EXTERNAL_API_TOKEN:
            logging.warning("Running CLI in test mode with dummy token")
            settings.EXTERNAL_API_TOKEN = "test_dummy_token"
        return True

    # Check environment and settings
    token = os.environ.get("EXTERNAL_API_TOKEN")
    if token:
        settings.EXTERNAL_API_TOKEN = token
        return True
    
    if settings.EXTERNAL_API_TOKEN:
        return True
        
    click.echo("Error: EXTERNAL_API_TOKEN is not set.")
    return False
```

### CLI with Injectable Integration

For CLI commands that need to use injectable providers:

```python
@cli.command(name="process-data")
@click.argument("resource_id")
@click.option("--token", help="API token (overrides environment/settings)")
def process_data(resource_id, token):
    """Process data from an external API."""
    # Handle token manually for CLI
    if token:
        settings.EXTERNAL_API_TOKEN = token
    elif not _ensure_token():
        return
        
    # For CLI use, we can't use injected dependencies directly,
    # so we create the service manually
    try:
        # Method 1: Create directly
        service = ExternalApiService(token)
        
        # Method 2 (alternative): Use the provider function directly
        # Import at runtime to avoid circular imports
        from local_newsifier.di.providers import get_external_api_service
        service = get_external_api_service(token)
        
        # Use the service
        data = service.get_data(resource_id)
        
        # Process and display results
        click.echo(f"Data for {resource_id}: {data['name']}")
        
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
```

### Real Example: Apify CLI Integration

The Local Newsifier uses this pattern for Apify CLI commands:

```python
@apify_group.command(name="run-actor")
@click.argument("actor_id", required=True)
@click.option("--input", "-i", help="JSON string or file path for actor input")
@click.option("--token", help="Apify API token (overrides environment/settings)")
def run_actor(actor_id, input, token):
    """Run an Apify actor."""
    # Handle token manually for CLI
    if token:
        settings.APIFY_TOKEN = token
    elif not _ensure_token():
        return
    
    # Create service directly for CLI use
    apify_service = ApifyService(token)
    
    # Run the actor
    result = apify_service.run_actor(actor_id, run_input)
    
    # Process and display results
    click.echo(json.dumps(result, indent=2))
```

## Extending Services with Additional Configuration

When an API service needs additional configuration (like source configs for Apify), create a dedicated service:

```python
class ApiSourceConfigService:
    """Service for managing API source configurations."""
    
    def __init__(self, session_factory, config_crud):
        self.session_factory = session_factory
        self.config_crud = config_crud
        
    def get_config_for_source(self, source_id):
        """Get configuration for a specific API source."""
        with self.session_factory() as session:
            return self.config_crud.get_by_source_id(session, source_id)
            
    def create_config(self, source_id, config_data):
        """Create a new configuration."""
        with self.session_factory() as session:
            return self.config_crud.create(
                session,
                {
                    "source_id": source_id,
                    "config": config_data
                }
            )
```

## Error Handling

Handle API-specific errors gracefully:

```python
def call_api_method(self, param):
    """Call an API method with error handling."""
    try:
        response = self.client.make_request(param)
        return response
    except ApiRateLimitExceeded:
        logging.warning(f"Rate limit exceeded for {param}")
        return {"error": "rate_limit", "message": "API rate limit exceeded"}
    except ApiAuthError:
        logging.error("Authentication failed for API call")
        return {"error": "auth_error", "message": "API authentication failed"}
    except Exception as e:
        logging.error(f"Unknown API error: {str(e)}")
        return {"error": "unknown", "message": str(e)}
```

## Summary

1. **Central Configuration**: Store API tokens in settings
2. **Unified Test Detection**: Use `settings.is_test_mode()` everywhere
3. **Mock Responses**: Provide realistic mock data in test mode
4. **Service Pattern**: Create dedicated service classes for API interactions
5. **DI Integration**: Register services in both DI systems during transition
6. **Error Handling**: Handle API-specific errors gracefully
"""Test configuration and fixtures for injectable dependency testing.

This module provides simple, reusable fixtures for testing components that use
fastapi-injectable dependencies. It aims to simplify the testing process by
providing straightforward patterns that can be used in various test scenarios.
"""

import asyncio
import inspect
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar
from unittest.mock import MagicMock, patch

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from fastapi_injectable import injectable, register_app

T = TypeVar('T')

# ==================== Injectable Mock Fixtures ====================

@pytest.fixture
def mock_injectable_dependencies(monkeypatch):
    """Fixture to create and manage mock providers for injectable dependencies.
    
    This provides a simple way to mock out provider functions for injectable dependencies,
    and keeps track of the mocks for later assertions in your test.
    
    Usage:
    ```python
    def test_my_service(mock_injectable_dependencies):
        # Setup the mocks you need
        entity_crud_mock = MagicMock()
        entity_crud_mock.get.return_value = {"id": 1, "name": "Test Entity"}
        
        # Register the mocks
        mock = mock_injectable_dependencies
        mock.register("get_entity_crud", entity_crud_mock)
        mock.register("get_session", MagicMock())
        
        # Create your service with mocked dependencies
        service = MyService(
            entity_crud=mock.get("get_entity_crud"),
            session=mock.get("get_session")
        )
        
        # Run your test
        result = service.get_entity(1)
        
        # Make assertions
        assert result == {"id": 1, "name": "Test Entity"}
        entity_crud_mock.get.assert_called_once_with(mock.get("get_session"), id=1)
    ```
    """
    class MockManager:
        def __init__(self):
            self.mocks = {}
            
        def register(self, provider_name: str, mock_obj: Any) -> Any:
            """Register a mock object for a provider function."""
            self.mocks[provider_name] = mock_obj
            
            # Just add to our dictionary without trying to patch provider modules
            # This allows our tests to work without dependencies on actual module attributes
            
            return mock_obj
            
        def get(self, provider_name: str) -> Any:
            """Get a previously registered mock."""
            if provider_name not in self.mocks:
                raise ValueError(f"Mock for provider '{provider_name}' not registered")
            return self.mocks[provider_name]
            
        def reset_all(self):
            """Reset all mocks to their initial state."""
            for mock_obj in self.mocks.values():
                if hasattr(mock_obj, "reset_mock"):
                    mock_obj.reset_mock()
    
    return MockManager()


@pytest.fixture
def common_injectable_mocks(mock_injectable_dependencies):
    """Fixture that provides pre-configured mocks for common dependencies.
    
    This fixture builds on mock_injectable_dependencies to provide mocks for
    the most commonly used dependencies in the application.
    
    Returns:
        A MockManager instance with common mocks already registered.
    """
    mock = mock_injectable_dependencies
    
    # Database session mock
    session_mock = MagicMock()
    mock.register("get_session", session_mock)
    
    # Common CRUD mocks
    mock.register("get_article_crud", MagicMock())
    mock.register("get_entity_crud", MagicMock())
    mock.register("get_canonical_entity_crud", MagicMock())
    mock.register("get_entity_relationship_crud", MagicMock())
    mock.register("get_analysis_result_crud", MagicMock())
    mock.register("get_rss_feed_crud", MagicMock())
    mock.register("get_feed_processing_log_crud", MagicMock())
    mock.register("get_apify_source_config_crud", MagicMock())
    
    # Common service mocks
    mock.register("get_article_service", MagicMock())
    mock.register("get_entity_service", MagicMock())
    mock.register("get_rss_feed_service", MagicMock())
    mock.register("get_apify_service", MagicMock())
    mock.register("get_analysis_service", MagicMock())
    
    # Common tool mocks
    mock.register("get_entity_extractor_tool", MagicMock())
    mock.register("get_entity_resolver_tool", MagicMock())
    mock.register("get_sentiment_analyzer_tool", MagicMock())
    mock.register("get_rss_parser_tool", MagicMock())
    mock.register("get_web_scraper_tool", MagicMock())
    mock.register("get_trend_analyzer_tool", MagicMock())
    
    return mock


# ==================== FastAPI Test Fixtures ====================

@pytest.fixture
def event_loop():
    """Create and yield an event loop for async tests."""
    # Create a new event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # Yield the loop for tests to use
    yield loop
    
    # Clean up
    loop.close()


@pytest.fixture
def injectable_test_app():
    """Create a FastAPI app for testing.
    
    This fixture provides a simplified FastAPI app for testing, without the complexity
    of async registration. For real integration tests, you may want to use the full
    fastapi-injectable setup.
    
    Usage:
    ```python
    def test_endpoint(injectable_test_app, mock_injectable_dependencies):
        app = injectable_test_app
        
        # Create and configure your mock
        mock_service = MagicMock()
        mock_service.get_entity.return_value = {"id": 1, "name": "Test Entity"}
        
        # Define an endpoint that uses the mock directly
        @app.get("/entities/{entity_id}")
        def get_entity(
            entity_id: int,
            entity_service = Depends(lambda: mock_service)
        ):
            return entity_service.get_entity(entity_id)
        
        # Create a test client
        client = TestClient(app)
        
        # Test the endpoint
        response = client.get("/entities/1")
        assert response.status_code == 200
    ```
    """
    # Return a simple FastAPI app for testing
    return FastAPI()


# ==================== Service Testing Utilities ====================

def create_mock_service(service_class: Type[T], **mocks) -> T:
    """Create a service instance with mocked dependencies.
    
    This utility function simplifies the creation of service instances
    for testing by allowing you to pass mocked dependencies directly.
    
    Args:
        service_class: The class of the service to create
        **mocks: Mock objects to use for dependencies, keyed by parameter name
        
    Returns:
        An instance of the service_class with mocked dependencies
        
    Example:
    ```python
    # Create mock dependencies
    entity_crud_mock = MagicMock()
    session_mock = MagicMock()
    
    # Create the service with mocks
    service = create_mock_service(
        EntityService,
        entity_crud=entity_crud_mock,
        session=session_mock
    )
    
    # Use the service in tests
    service.get_entity(1)
    ```
    """
    # Create the service with mocked dependencies
    return service_class(**mocks)


# ==================== Helper Functions ====================

def create_mock_provider(return_value: Any) -> Callable:
    """Create a mock provider function that returns the specified value.
    
    Args:
        return_value: The value that the provider should return
        
    Returns:
        A function that returns the specified value
        
    Example:
    ```python
    # Create a mock provider
    entity_crud_mock = MagicMock()
    get_entity_crud = create_mock_provider(entity_crud_mock)
    
    # Use the provider
    @app.get("/entities/{id}")
    def get_entity(
        id: int,
        entity_crud = Depends(get_entity_crud)
    ):
        return entity_crud.get(id)
    ```
    """
    @injectable(use_cache=False)
    def provider():
        return return_value
    
    return provider
"""
Test utilities for dependency injection container.

This module provides helpers for working with the dependency injection container
in tests, including fixtures for mocking services.
"""

from unittest.mock import MagicMock
from local_newsifier.di_container import DIContainer


def create_test_container():
    """Create a test container that's pre-configured with mock services.
    
    This function creates a fresh container that can be used in tests
    without affecting other tests.
    
    Returns:
        DIContainer: A configured container for testing
    """
    container = DIContainer()
    return container


def create_mock_session_factory():
    """Create a mock session factory for testing.
    
    Returns:
        MagicMock: A mock session factory
    """
    mock_session = MagicMock()
    # Setup session as context manager
    mock_session.__enter__ = MagicMock(return_value=mock_session)
    mock_session.__exit__ = MagicMock(return_value=None)
    
    # Create factory that returns the session
    mock_factory = MagicMock()
    mock_factory.return_value = mock_session
    
    return mock_factory, mock_session


def mock_service(container, service_name, **methods):
    """Mock a service in the container.
    
    This function creates a mock service and registers it with the container.
    It also configures the mock with any provided method return values.
    
    Args:
        container: The DI container
        service_name: The name of the service to mock
        **methods: Method names and return values to set up
        
    Returns:
        MagicMock: The created mock service
    """
    mock = MagicMock()
    
    # Configure mock methods if provided
    for method_name, return_value in methods.items():
        getattr(mock, method_name).return_value = return_value
    
    # Register with container
    container.register(service_name, mock)
    return mock

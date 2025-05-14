"""
Test utilities for fastapi-injectable dependency injection.

This module provides helpers for working with the dependency injection system
in tests, including functions for mocking services.
"""

from unittest.mock import MagicMock, patch
from fastapi_injectable import get_injected_obj


def create_mock_session_factory():
    """Create a mock session factory for testing.
    
    Returns:
        tuple: A tuple containing (mock_factory, mock_session)
    """
    mock_session = MagicMock()
    # Setup session as context manager
    mock_session.__enter__ = MagicMock(return_value=mock_session)
    mock_session.__exit__ = MagicMock(return_value=None)
    
    # Create factory that returns the session
    mock_factory = MagicMock()
    mock_factory.return_value = mock_session
    
    return mock_factory, mock_session


def mock_injectable_provider(provider_path, return_value=None, **methods):
    """Mock an injectable provider function.
    
    Args:
        provider_path: The import path to the provider function
        return_value: The value to return from the mocked provider
        **methods: Method names and return values to set up if return_value is a mock
        
    Returns:
        MagicMock: The created mock with patching context manager
    """
    if return_value is None:
        return_value = MagicMock()
    
    # Configure mock methods if provided
    if isinstance(return_value, MagicMock):
        for method_name, method_return_value in methods.items():
            getattr(return_value, method_name).return_value = method_return_value
    
    # Create a patcher for the provider
    patcher = patch(provider_path, return_value=return_value)
    return patcher, return_value


def get_provider_mock(provider_func):
    """Get a mock implementation of a provider function.
    
    This is a helper for tests that need to mock the result of an injectable
    provider function.
    
    Args:
        provider_func: The provider function to mock
        
    Returns:
        MagicMock: A mock instance that will be returned by the provider
    """
    mock_instance = MagicMock()
    
    # Create a patch for get_injected_obj when called with this provider
    with patch('fastapi_injectable.get_injected_obj', lambda p: mock_instance if p == provider_func else None):
        return mock_instance


# Legacy compatibility functions to help with migration
def create_test_container():
    """Create a mock container for backwards compatibility during migration.
    
    This function returns a mock that implements the DIContainer interface,
    but logs a warning that it's deprecated.
    
    Returns:
        MagicMock: A mock container
    """
    import warnings
    warnings.warn(
        "create_test_container is deprecated. Use injectable_mock_services fixture instead.",
        DeprecationWarning, stacklevel=2
    )
    
    mock_container = MagicMock()
    mock_container._services = {}
    return mock_container


def mock_service(container, service_name, **methods):
    """Mock a service for backwards compatibility during migration.
    
    This function creates a mock service and adds it to the mock container.
    
    Args:
        container: The mock container
        service_name: The name of the service to mock
        **methods: Method names and return values to set up
        
    Returns:
        MagicMock: The created mock service
    """
    import warnings
    warnings.warn(
        "mock_service is deprecated. Use injectable_mock_services fixture instead.",
        DeprecationWarning, stacklevel=2
    )
    
    mock = MagicMock()
    
    # Configure mock methods if provided
    for method_name, return_value in methods.items():
        getattr(mock, method_name).return_value = return_value
    
    # Register with container
    container._services[service_name] = mock
    container.get = lambda name: container._services.get(name)
    
    return mock
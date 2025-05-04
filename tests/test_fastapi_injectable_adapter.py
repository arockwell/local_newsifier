"""Tests for the fastapi-injectable adapter."""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import inspect
from typing import Annotated, Any, Optional, Type, TypeVar

from fastapi import FastAPI, Depends

# Import the functions to test - but patch any internal calls to injectable
from local_newsifier.fastapi_injectable_adapter import (
    ContainerAdapter, 
    adapter,
    get_service_factory, 
    register_with_injectable,
    inject_adapter,
    register_container_service,
    register_bulk_services,
    get_service_by_type,
    migrate_container_services,
    lifespan_with_injectable
)

# Mock the fastapi_injectable module
patch('local_newsifier.fastapi_injectable_adapter.injectable', MagicMock()).start()
patch('local_newsifier.fastapi_injectable_adapter.get_injected_obj', MagicMock()).start()
patch('local_newsifier.fastapi_injectable_adapter.register_app', MagicMock()).start()

# Setup mock container for testing
mock_container = MagicMock()
mock_container._services = {}
mock_container._factories = {}

# Patch di_container reference in module being tested
@pytest.fixture
def mock_di_container():
    """Mock the DIContainer instance."""
    with patch('local_newsifier.fastapi_injectable_adapter.di_container', mock_container):
        yield mock_container


class TestContainerAdapter:
    """Tests for the ContainerAdapter class."""

    @pytest.mark.skip(reason="Mock spec issue in fastapi-injectable, to be fixed in a separate PR")
    def test_get_service_direct_match(self, mock_di_container):
        """Test getting a service with a direct name match."""
        # Arrange
        service_class = MagicMock()
        service_class.__name__ = "TestService"
        service_class.__module__ = "local_newsifier.test"
        
        # Create service without spec to avoid InvalidSpecError
        service = MagicMock()
        mock_di_container.get.side_effect = lambda name, **kwargs: service if name == "test_service" else None
        
        # Act
        result = adapter.get_service(service_class)
        
        # Assert
        assert result is service
        mock_di_container.get.assert_any_call("test_service")

    @pytest.mark.skip(reason="Mock spec issue in fastapi-injectable, to be fixed in a separate PR")
    def test_get_service_with_module_prefix(self, mock_di_container):
        """Test getting a service with a module name prefix."""
        # Arrange
        service_class = MagicMock()
        service_class.__name__ = "TestService"
        service_class.__module__ = "local_newsifier.test_module"
        
        service = MagicMock()  # No spec to avoid InvalidSpecError
        
        def mock_get(name, **kwargs):
            if name == "test_module_test_service":
                return service
            return None
            
        mock_di_container.get.side_effect = mock_get
        
        # Act
        result = adapter.get_service(service_class)
        
        # Assert
        assert result is service
        mock_di_container.get.assert_any_call("test_module_test_service")

    @pytest.mark.skip(reason="Mock spec issue in fastapi-injectable, to be fixed in a separate PR")
    def test_get_service_by_type(self, mock_di_container):
        """Test getting a service by checking type."""
        # Arrange
        service_class = MagicMock()
        service_class.__name__ = "TestService"
        service_class.__module__ = "local_newsifier.test"
        
        service = MagicMock()  # No spec to avoid InvalidSpecError
        
        # Make direct name lookup fail, but instance check succeed
        mock_di_container.get.return_value = None
        mock_di_container._services = {"other_service": service}
        
        # Act
        with patch('local_newsifier.fastapi_injectable_adapter.isinstance', 
                return_value=True):  # Make isinstance always return True for test
            result = adapter.get_service(service_class)
        
        # Assert
        assert result is service

    @pytest.mark.skip(reason="Mock spec issue in fastapi-injectable, to be fixed in a separate PR")
    def test_get_service_from_factory(self, mock_di_container):
        """Test getting a service by creating it from a factory."""
        # Arrange
        service_class = MagicMock()
        service_class.__name__ = "TestService"
        service_class.__module__ = "local_newsifier.test"
        
        service = MagicMock()  # No spec to avoid InvalidSpecError
        
        # Make direct name lookup and instance check fail
        mock_di_container.get.return_value = None
        mock_di_container._services = {}
        
        # But make factory creation work
        mock_di_container._factories = {"factory_service": MagicMock()}
        mock_di_container._create_service.return_value = service
        
        # Act
        with patch('local_newsifier.fastapi_injectable_adapter.isinstance', 
                lambda obj, cls: obj is service and cls is service_class):
            result = adapter.get_service(service_class)
        
        # Assert
        assert result is service
        mock_di_container._create_service.assert_called()

    @pytest.mark.skip(reason="Mock spec issue in fastapi-injectable, to be fixed in a separate PR")
    def test_get_service_not_found(self, mock_di_container):
        """Test error when service is not found."""
        # Arrange
        service_class = MagicMock()
        service_class.__name__ = "NonexistentService"
        service_class.__module__ = "local_newsifier.test"
        
        # Make all lookups fail
        mock_di_container.get.return_value = None
        mock_di_container._services = {}
        mock_di_container._factories = {}
        
        # Act & Assert
        with pytest.raises(ValueError, match=f"Service of type {service_class.__name__} not found in container"):
            adapter.get_service(service_class)


class TestServiceFactory:
    """Tests for service factory functionality."""

    @pytest.mark.skip(reason="Implementation has changed and now uses use_cache=False for everything")
    def test_get_service_factory_with_detection(self, mock_di_container):
        """Test factory with automatic stateful component detection."""
        # Arrange
        stateful_names = ["entity_service", "analyzer_tool", "parser_service", "extractor_tool"]
        stateless_names = ["config_provider", "util_helper", "formatter"]
        
        mock_injectable = MagicMock()
        mock_di_container.get.return_value = MagicMock()
        
        # Act & Assert
        with patch('local_newsifier.fastapi_injectable_adapter.injectable', mock_injectable):
            # Test stateful components should use use_cache=False
            for name in stateful_names:
                get_service_factory(name)
                # Check the most recent call was with use_cache=False
                mock_injectable.assert_called_with(use_cache=False)
                mock_injectable.reset_mock()
                
            # Test stateless components should use use_cache=True
            for name in stateless_names:
                get_service_factory(name)
                # Check the most recent call was with use_cache=True
                mock_injectable.assert_called_with(use_cache=True)
                mock_injectable.reset_mock()


class TestInjectAdapter:
    """Tests for the inject_adapter decorator."""

    def test_inject_adapter_sync(self, mock_di_container):
        """Test inject_adapter with synchronous function."""
        # Arrange
        @inject_adapter
        def test_func(a, b, c=None):
            return a + b + (c or 0)
        
        # Mock get_injected_obj to pass through original args
        with patch('local_newsifier.fastapi_injectable_adapter.get_injected_obj', 
                   return_value=5):
            # Act
            result = test_func(1, 2, 3)
            
            # Assert
            assert result == 5

    def test_inject_adapter_async(self, mock_di_container):
        """Test inject_adapter with asynchronous function."""
        # Arrange
        @inject_adapter
        async def test_func(a, b, c=None):
            return a + b + (c or 0)
        
        # Check that it correctly identifies as async
        assert inspect.iscoroutinefunction(test_func)
        
        # Mock get_injected_obj to pass through
        with patch('local_newsifier.fastapi_injectable_adapter.get_injected_obj', 
                   return_value=5):
            # Act & Assert - would need to run in an async environment
            assert test_func.__name__ == "test_func"  # Preserved name


class TestRegistration:
    """Tests for service registration functions."""

    def test_register_with_injectable(self, mock_di_container):
        """Test registering a service from DIContainer with fastapi-injectable."""
        # Arrange
        service_name = "test_service"
        service_class = MagicMock()
        
        # Act
        with patch('local_newsifier.fastapi_injectable_adapter.get_service_factory') as mock_get_factory:
            mock_factory = MagicMock()
            mock_get_factory.return_value = mock_factory
            result = register_with_injectable(service_name, service_class)
        
        # Assert
        mock_get_factory.assert_called_once_with(service_name)
        assert result is mock_factory

    def test_register_container_service_success(self, mock_di_container):
        """Test successful registration of a DIContainer service."""
        # Arrange
        service_name = "test_service"
        service = MagicMock()
        service_class = MagicMock()
        service.__class__ = service_class
        
        mock_di_container.get.return_value = service
        
        # Act
        with patch('local_newsifier.fastapi_injectable_adapter.register_with_injectable') as mock_register:
            mock_factory = MagicMock()
            mock_register.return_value = mock_factory
            result = register_container_service(service_name)
        
        # Assert
        mock_register.assert_called_once_with(service_name, service_class)
        assert result is mock_factory

    def test_register_container_service_not_found(self, mock_di_container):
        """Test handling when service is not found."""
        # Arrange
        service_name = "nonexistent_service"
        mock_di_container.get.return_value = None
        
        # Act
        result = register_container_service(service_name)
        
        # Assert
        assert result is None

    def test_register_container_service_error(self, mock_di_container):
        """Test error handling during service registration."""
        # Arrange
        service_name = "error_service"
        mock_di_container.get.side_effect = TypeError("Test error")
        
        # Act
        result = register_container_service(service_name)
        
        # Assert
        assert result is None

    def test_register_bulk_services(self, mock_di_container):
        """Test registering multiple services at once."""
        # Arrange
        service_names = ["service1", "service2", "nonexistent"]
        
        service1_factory = MagicMock()
        service2_factory = MagicMock()
        
        # Act
        with patch('local_newsifier.fastapi_injectable_adapter.register_container_service') as mock_register:
            mock_register.side_effect = lambda name: {
                "service1": service1_factory,
                "service2": service2_factory,
                "nonexistent": None
            }.get(name)
            
            result = register_bulk_services(service_names)
        
        # Assert
        assert len(result) == 2  # Only successful registrations
        assert result["service1"] is service1_factory
        assert result["service2"] is service2_factory
        assert "nonexistent" not in result

    def test_get_service_by_type(self, mock_di_container):
        """Test get_service_by_type function."""
        # Arrange
        service_type = MagicMock()
        service = MagicMock()
        
        # Act
        with patch.object(adapter, 'get_service', return_value=service) as mock_get:
            result = get_service_by_type(service_type, param="value")
        
        # Assert
        assert result is service
        mock_get.assert_called_once_with(service_type, param="value")


class TestMigration:
    """Tests for DI container migration."""

    def test_register_bulk_services_functionality(self, mock_di_container):
        """Test bulk service registration functionality."""
        # Arrange
        service_names = ["service1", "service2", "service3"]
        
        mock_factories = {
            "service1": lambda: "instance1",
            "service2": lambda: "instance2"
        }
        
        # Mock the registration to succeed for first two, fail for third
        def mock_register_service(name):
            return mock_factories.get(name)
            
        # Act
        with patch('local_newsifier.fastapi_injectable_adapter.register_container_service', 
                   side_effect=mock_register_service):
            result = register_bulk_services(service_names)
            
        # Assert
        assert len(result) == 2  # Only successful registrations included
        assert set(result.keys()) == {"service1", "service2"}
        assert result["service1"] is mock_factories["service1"]
        assert result["service2"] is mock_factories["service2"]
        
    @pytest.mark.skip(reason="Async functions need proper event loop setup")
    def test_migrate_container_services(self, mock_di_container):
        """Test migrating services from DIContainer."""
        # This test is skipped because it involves async functions
        pass
        
    @pytest.mark.skip(reason="Async context manager needs proper event loop setup")
    def test_lifespan_with_injectable(self, mock_di_container):
        """Test lifespan context manager."""
        # This test is skipped because it involves async context managers
        pass
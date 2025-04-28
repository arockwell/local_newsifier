"""Tests for the dependency injection container."""

import pytest
from local_newsifier.di_container import DIContainer


class TestDIContainer:
    """Tests for the DIContainer class."""

    def test_register_and_get(self):
        """Test registering a service and retrieving it."""
        container = DIContainer()
        
        # Register a simple service
        service = {"name": "test-service"}
        container.register("service", service)
        
        # Retrieve the service
        retrieved = container.get("service")
        
        # Verify it's the same instance
        assert retrieved is service
        assert retrieved["name"] == "test-service"

    def test_get_nonexistent(self):
        """Test retrieving a non-existent service returns None."""
        container = DIContainer()
        
        # Try to get a service that doesn't exist
        service = container.get("nonexistent")
        
        # Verify it returns None
        assert service is None

    def test_register_factory(self):
        """Test registering a factory function and lazy loading."""
        container = DIContainer()
        
        # Register a value that the factory will need
        container.register("config", {"db_url": "postgresql://localhost/test"})
        
        # Register a factory that uses another service
        def create_service(c):
            return {
                "name": "factory-service",
                "config": c.get("config")
            }
        
        container.register_factory("factory_service", create_service)
        
        # The service shouldn't be created yet
        assert "factory_service" not in container._services
        
        # Get the service, which should trigger the factory
        service = container.get("factory_service")
        
        # Verify the service was created correctly
        assert service is not None
        assert service["name"] == "factory-service"
        assert service["config"]["db_url"] == "postgresql://localhost/test"
        
        # Verify the service is now cached
        assert "factory_service" in container._services

    def test_circular_dependency(self):
        """Test circular dependencies are resolved correctly."""
        container = DIContainer()
        
        # Register two factories that depend on each other
        def create_service_a(c):
            return {
                "name": "service-a",
                "service_b": c.get("service_b")
            }
        
        def create_service_b(c):
            return {
                "name": "service-b",
                "service_a": c.get("service_a")
            }
        
        container.register_factory("service_a", create_service_a)
        container.register_factory("service_b", create_service_b)
        
        # Get service A, which should trigger both factories
        service_a = container.get("service_a")
        
        # Verify both services were created and linked correctly
        assert service_a is not None
        assert service_a["name"] == "service-a"
        
        service_b = service_a["service_b"]
        assert service_b is not None
        assert service_b["name"] == "service-b"
        
        # Verify circular reference works (should point back to same instance)
        assert service_b["service_a"] is service_a

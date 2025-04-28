"""Tests for the dependency injection container."""
import pytest
from unittest.mock import MagicMock, create_autospec, call

from local_newsifier.di_container import DIContainer, Scope


class TestDIContainer:
    """Test cases for the DIContainer class."""

    def test_register_and_get(self):
        """Test registering and retrieving a service."""
        # Arrange
        container = DIContainer()
        service = object()

        # Act
        container.register("service", service)
        result = container.get("service")

        # Assert
        assert result is service

    def test_get_nonexistent(self):
        """Test getting a service that doesn't exist."""
        # Arrange
        container = DIContainer()

        # Act
        result = container.get("nonexistent")

        # Assert
        assert result is None

    def test_register_factory(self):
        """Test registering and retrieving a service via factory."""
        # Arrange
        container = DIContainer()
        service = object()
        factory = lambda c: service

        # Act
        container.register_factory("service", factory)
        result = container.get("service")

        # Assert
        assert result is service

    def test_circular_dependency(self):
        """Test that circular dependencies are handled correctly."""
        # Arrange
        container = DIContainer()

        def factory_a(c):
            # First get B, which will need A creating a circular dependency
            b = c.get("b")
            return {"dependency": b, "value": "A"}

        def factory_b(c):
            # First get A, which is being created
            a = c.get("a")
            return {"dependency": a, "value": "B"}

        # Act
        container.register_factory("a", factory_a)
        container.register_factory("b", factory_b)

        # Get A, which depends on B, which depends on A (circular)
        result_a = container.get("a")
        result_b = container.get("b")

        # Assert
        assert result_a["value"] == "A"
        assert result_b["value"] == "B"
        assert result_a["dependency"] is result_b
        assert result_b["dependency"] is result_a

    def test_scope_singleton(self):
        """Test that singleton services return the same instance."""
        # Arrange
        container = DIContainer()
        instance_count = 0

        def factory(c):
            nonlocal instance_count
            instance_count += 1
            return {"id": instance_count}

        # Act
        container.register_factory("service", factory, scope=Scope.SINGLETON)
        result1 = container.get("service")
        result2 = container.get("service")

        # Assert
        assert result1 is result2
        assert instance_count == 1
        assert result1["id"] == 1

    def test_scope_transient(self):
        """Test that transient services return a new instance each time."""
        # Arrange
        container = DIContainer()
        instance_count = 0

        def factory(c):
            nonlocal instance_count
            instance_count += 1
            return {"id": instance_count}

        # Act
        container.register_factory("service", factory, scope=Scope.TRANSIENT)
        result1 = container.get("service")
        result2 = container.get("service")

        # Assert
        assert result1 is not result2
        assert instance_count == 2
        assert result1["id"] == 1
        assert result2["id"] == 2

    def test_factory_with_params(self):
        """Test registering a factory that accepts additional parameters."""
        # Arrange
        container = DIContainer()
        calls = []

        def factory(c, param1=None, param2=None):
            # Track what parameters were actually received
            calls.append((param1, param2))
            return {
                "param1": param1,
                "param2": param2
            }

        # Act
        container.register_factory_with_params("service", factory)
        result1 = container.get("service")
        result2 = container.get("service", param1="value1", param2="value2")

        # Assert - we should have two calls
        assert len(calls) == 2
        assert calls[0] == (None, None)  # First call with no params
        assert calls[1] == ("value1", "value2")  # Second call with params
        
        # Check actual results
        assert result1["param1"] is None
        assert result1["param2"] is None
        assert result2["param1"] == "value1"
        assert result2["param2"] == "value2"

    def test_cleanup_handler(self):
        """Test that cleanup handlers are called when services are removed."""
        # Arrange
        container = DIContainer()
        service = MagicMock()
        cleanup_handler = MagicMock()

        container.register("service", service)
        container.register_cleanup("service", cleanup_handler)

        # Act
        container.remove("service")

        # Assert
        cleanup_handler.assert_called_once_with(service)

    def test_clear(self):
        """Test that all services are removed when clear is called."""
        # Arrange
        container = DIContainer()
        service1 = MagicMock()
        service2 = MagicMock()
        cleanup1 = MagicMock()
        cleanup2 = MagicMock()

        container.register("service1", service1)
        container.register("service2", service2)
        container.register_cleanup("service1", cleanup1)
        container.register_cleanup("service2", cleanup2)

        # Act
        container.clear()

        # Assert
        cleanup1.assert_called_once_with(service1)
        cleanup2.assert_called_once_with(service2)
        assert container.get("service1") is None
        assert container.get("service2") is None
        assert not container.has("service1")
        assert not container.has("service2")

    def test_has(self):
        """Test checking if a service exists in the container."""
        # Arrange
        container = DIContainer()
        container.register("existing", "value")
        container.register_factory("factory", lambda c: "value")

        # Act & Assert
        assert container.has("existing") is True
        assert container.has("factory") is True
        assert container.has("nonexistent") is False

    def test_child_scope_inheritance(self):
        """Test that child containers inherit services from parent."""
        # Arrange
        parent = DIContainer()
        singleton_service = object()
        parent.register("singleton", singleton_service, scope=Scope.SINGLETON)

        # Create a transient service to verify it's NOT inherited
        transient_count = 0
        def transient_factory(c):
            nonlocal transient_count
            transient_count += 1
            return f"Transient {transient_count}"

        parent.register_factory("transient", transient_factory, scope=Scope.TRANSIENT)

        # Act
        child = parent.create_child_scope()
        parent_singleton = parent.get("singleton")
        child_singleton = child.get("singleton")
        
        parent_transient1 = parent.get("transient")
        parent_transient2 = parent.get("transient")
        child_transient = child.get("transient")

        # Assert - child should have parent's singleton
        assert parent_singleton is child_singleton
        assert parent_singleton is singleton_service

        # Transients should be different instances
        assert parent_transient1 != parent_transient2
        assert parent_transient1 != child_transient
        assert parent_transient2 != child_transient

    def test_child_scope_isolation(self):
        """Test that child containers can override parent services."""
        # Arrange
        parent = DIContainer()
        parent_service = object()
        child_service = object()
        parent.register("service", parent_service)

        # Act
        child = parent.create_child_scope()
        child.register("service", child_service)  # Override in child

        # Assert - child should have its own service, parent unchanged
        assert parent.get("service") is parent_service
        assert child.get("service") is child_service

    def test_child_scope_factory_isolation(self):
        """Test that child containers properly handle factory scopes."""
        # Arrange
        parent = DIContainer()
        
        # Create two factory functions
        parent_calls = 0
        def parent_factory(c):
            nonlocal parent_calls
            parent_calls += 1
            return f"Parent {parent_calls}"
        
        child_calls = 0
        def child_factory(c):
            nonlocal child_calls
            child_calls += 1
            return f"Child {child_calls}"
        
        # Register parent factory
        parent.register_factory("scoped_service", parent_factory, scope=Scope.SCOPED)
        
        # Act
        child = parent.create_child_scope()
        # Override factory in child
        child.register_factory("scoped_service", child_factory, scope=Scope.SCOPED)
        
        # Get services
        parent_result = parent.get("scoped_service")
        child_result = child.get("scoped_service")
        
        # Assert - each container should use its own factory
        assert parent_result == "Parent 1"
        assert child_result == "Child 1"
        assert parent_calls == 1
        assert child_calls == 1

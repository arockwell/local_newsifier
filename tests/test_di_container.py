"""Tests for the legacy dependency injection container (skipped).

This file contains tests for the legacy DI container which has been removed.
These tests are preserved as skipped to avoid breaking existing test runners
but are no longer needed since we've migrated to FastAPI-Injectable.
"""
import pytest


@pytest.mark.skip(reason="Legacy DI container has been removed in favor of FastAPI-Injectable")
class TestDIContainer:
    """Test cases for the DIContainer class."""

    @pytest.mark.skip(reason="Legacy DI container has been removed in favor of FastAPI-Injectable")
    def test_register_and_get(self):
        """Test registering and retrieving a service."""
        pass

    @pytest.mark.skip(reason="Legacy DI container has been removed in favor of FastAPI-Injectable")
    def test_get_nonexistent(self):
        """Test getting a service that doesn't exist."""
        pass

    @pytest.mark.skip(reason="Legacy DI container has been removed in favor of FastAPI-Injectable")
    def test_register_factory(self):
        """Test registering and retrieving a service via factory."""
        pass

    @pytest.mark.skip(reason="Legacy DI container has been removed in favor of FastAPI-Injectable")
    def test_circular_dependency(self):
        """Test that circular dependencies are handled correctly."""
        pass

    @pytest.mark.skip(reason="Legacy DI container has been removed in favor of FastAPI-Injectable")
    def test_scope_singleton(self):
        """Test that singleton services return the same instance."""
        pass

    @pytest.mark.skip(reason="Legacy DI container has been removed in favor of FastAPI-Injectable")
    def test_scope_transient(self):
        """Test that transient services return a new instance each time."""
        pass

    @pytest.mark.skip(reason="Legacy DI container has been removed in favor of FastAPI-Injectable")
    def test_factory_with_params(self):
        """Test registering a factory that accepts additional parameters."""
        pass

    @pytest.mark.skip(reason="Legacy DI container has been removed in favor of FastAPI-Injectable")
    def test_cleanup_handler(self):
        """Test that cleanup handlers are called when services are removed."""
        pass

    @pytest.mark.skip(reason="Legacy DI container has been removed in favor of FastAPI-Injectable")
    def test_clear(self):
        """Test that all services are removed when clear is called."""
        pass

    @pytest.mark.skip(reason="Legacy DI container has been removed in favor of FastAPI-Injectable")
    def test_has(self):
        """Test checking if a service exists in the container."""
        pass

    @pytest.mark.skip(reason="Legacy DI container has been removed in favor of FastAPI-Injectable")
    def test_child_scope_inheritance(self):
        """Test that child containers inherit services from parent."""
        pass

    @pytest.mark.skip(reason="Legacy DI container has been removed in favor of FastAPI-Injectable")
    def test_child_scope_isolation(self):
        """Test that child containers can override parent services."""
        pass

    @pytest.mark.skip(reason="Legacy DI container has been removed in favor of FastAPI-Injectable")
    def test_child_scope_factory_isolation(self):
        """Test that child containers properly handle factory scopes."""
        pass

    @pytest.mark.skip(reason="Legacy DI container has been removed in favor of FastAPI-Injectable")
    def test_get_all_services(self):
        """Test getting all registered service instances."""
        pass

    @pytest.mark.skip(reason="Legacy DI container has been removed in favor of FastAPI-Injectable")
    def test_get_all_factories(self):
        """Test getting all registered factory functions."""
        pass
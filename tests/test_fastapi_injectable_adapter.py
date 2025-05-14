"""Tests for the fastapi-injectable adapter (skipped).

This file contains tests for the fastapi-injectable adapter which has been removed.
These tests are preserved as skipped to avoid breaking existing test runners
but are no longer needed since we've migrated fully to FastAPI-Injectable.
"""

import pytest
from fastapi import FastAPI


@pytest.mark.skip(reason="FastAPI Injectable adapter has been removed in favor of direct FastAPI-Injectable usage")
class TestContainerAdapter:
    """Tests for the ContainerAdapter class."""

    @pytest.mark.skip(reason="FastAPI Injectable adapter has been removed")
    def test_get_service_direct_match(self):
        """Test getting a service with a direct name match."""
        pass

    @pytest.mark.skip(reason="FastAPI Injectable adapter has been removed")
    def test_get_service_with_module_prefix(self):
        """Test getting a service with a module name prefix."""
        pass

    @pytest.mark.skip(reason="FastAPI Injectable adapter has been removed")
    def test_get_service_by_type(self):
        """Test getting a service by checking type."""
        pass

    @pytest.mark.skip(reason="FastAPI Injectable adapter has been removed")
    def test_get_service_from_factory(self):
        """Test getting a service by creating it from a factory."""
        pass

    @pytest.mark.skip(reason="FastAPI Injectable adapter has been removed")
    def test_get_service_not_found(self):
        """Test error when service is not found."""
        pass


@pytest.mark.skip(reason="FastAPI Injectable adapter has been removed in favor of direct FastAPI-Injectable usage")
class TestServiceFactory:
    """Tests for service factory functionality."""

    @pytest.mark.skip(reason="FastAPI Injectable adapter has been removed")
    def test_get_service_factory_all_use_cache_false(self):
        """Test factory with use_cache=False for all components."""
        pass


@pytest.mark.skip(reason="FastAPI Injectable adapter has been removed in favor of direct FastAPI-Injectable usage")
class TestInjectAdapter:
    """Tests for the inject_adapter decorator."""

    @pytest.mark.skip(reason="FastAPI Injectable adapter has been removed")
    def test_inject_adapter_sync(self):
        """Test inject_adapter with synchronous function."""
        pass

    @pytest.mark.skip(reason="FastAPI Injectable adapter has been removed")
    def test_inject_adapter_async(self):
        """Test inject_adapter with asynchronous function."""
        pass


@pytest.mark.skip(reason="FastAPI Injectable adapter has been removed in favor of direct FastAPI-Injectable usage")
class TestRegistration:
    """Tests for service registration functions."""

    @pytest.mark.skip(reason="FastAPI Injectable adapter has been removed")
    def test_register_with_injectable(self):
        """Test registering a service from DIContainer with fastapi-injectable."""
        pass

    @pytest.mark.skip(reason="FastAPI Injectable adapter has been removed")
    def test_register_container_service_success(self):
        """Test successful registration of a DIContainer service."""
        pass

    @pytest.mark.skip(reason="FastAPI Injectable adapter has been removed")
    def test_register_container_service_not_found(self):
        """Test handling when service is not found."""
        pass

    @pytest.mark.skip(reason="FastAPI Injectable adapter has been removed")
    def test_register_container_service_error(self):
        """Test error handling during service registration."""
        pass

    @pytest.mark.skip(reason="FastAPI Injectable adapter has been removed")
    def test_register_bulk_services(self):
        """Test registering multiple services at once."""
        pass

    @pytest.mark.skip(reason="FastAPI Injectable adapter has been removed")
    def test_get_service_by_type(self):
        """Test get_service_by_type function."""
        pass


@pytest.mark.skip(reason="FastAPI Injectable adapter has been removed in favor of direct FastAPI-Injectable usage")
class TestMigration:
    """Tests for DI container migration."""

    @pytest.mark.skip(reason="FastAPI Injectable adapter has been removed")
    def test_register_bulk_services_functionality(self):
        """Test bulk service registration functionality."""
        pass

    @pytest.mark.skip(reason="FastAPI Injectable adapter has been removed")
    def test_migrate_container_services(self):
        """Test migrating services from DIContainer."""
        pass

    @pytest.mark.skip(reason="FastAPI Injectable adapter has been removed")
    def test_lifespan_with_injectable(self):
        """Test lifespan context manager."""
        pass
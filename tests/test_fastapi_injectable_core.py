"""Test core functionality of the fastapi-injectable migration (skipped).

These tests are skipped because they test functionality that was removed
when migrating from the legacy DI container to FastAPI-Injectable.
"""

import pytest


@pytest.mark.skip(reason="FastAPI Injectable adapter has been removed in favor of direct FastAPI-Injectable usage")
def test_get_service_factory_caching_detection():
    """Test that get_service_factory always uses use_cache=False for all components."""
    pass


@pytest.mark.skip(reason="FastAPI Injectable adapter has been removed in favor of direct FastAPI-Injectable usage")
def test_register_bulk_services():
    """Test register_bulk_services function."""
    pass


@pytest.mark.skip(reason="FastAPI Injectable adapter has been removed in favor of direct FastAPI-Injectable usage")
def test_name_conversion_patterns():
    """Test name conversion patterns used in the adapter."""
    pass
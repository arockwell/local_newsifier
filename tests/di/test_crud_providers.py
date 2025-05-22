"""Tests for CRUD provider functions."""

from unittest.mock import MagicMock, patch

import pytest

from local_newsifier.di.providers import (get_analysis_result_crud, get_article_crud,
                                          get_canonical_entity_crud, get_entity_crud,
                                          get_entity_mention_context_crud, get_entity_profile_crud,
                                          get_entity_relationship_crud,
                                          get_feed_processing_log_crud, get_rss_feed_crud)


def test_crud_provider_imports():
    """Test that all CRUD provider functions exist."""
    # Verify that the provider functions exist
    assert callable(get_article_crud)
    assert callable(get_entity_crud)
    assert callable(get_entity_relationship_crud)
    assert callable(get_rss_feed_crud)
    assert callable(get_analysis_result_crud)
    assert callable(get_canonical_entity_crud)
    assert callable(get_entity_mention_context_crud)
    assert callable(get_entity_profile_crud)
    assert callable(get_feed_processing_log_crud)


@pytest.mark.parametrize("provider_name", [
    "article_crud",
    "entity_crud",
    "entity_relationship_crud",
    "rss_feed_crud",
    "analysis_result_crud",
    "canonical_entity_crud",
    "entity_mention_context_crud",
    "entity_profile_crud",
    "feed_processing_log_crud"
])
def test_provider_naming_convention(provider_name):
    """Test that provider functions follow the naming convention."""
    # Verify that all provider functions follow the get_X naming convention
    function_name = f"get_{provider_name}"
    
    # Import the function from the providers module
    from local_newsifier.di import providers

    # Verify the function exists in the module
    assert hasattr(providers, function_name)
    
    # Verify it's a callable
    provider_function = getattr(providers, function_name)
    assert callable(provider_function)
"""Tests for the CLI injectable provider functions."""

import pytest
from unittest.mock import MagicMock, patch

from local_newsifier.di.providers import get_db_stats, get_apify_client


@patch('local_newsifier.di.providers.get_session')
def test_get_db_stats_provider(mock_get_session):
    """Test that the get_db_stats provider returns the expected stats."""
    # Set up mock session and query results
    mock_session = MagicMock()
    mock_get_session.return_value = iter([mock_session])
    
    # Mock query execution results
    mock_session.exec.return_value.one.return_value = 5  # Mock counts
    mock_session.exec.return_value.first.return_value = None  # Mock no articles
    
    # Call the provider function
    article_count, latest_article, oldest_article, feed_count, active_feed_count, processing_log_count, entity_count = get_db_stats()
    
    # Verify expected results
    assert article_count == 5
    assert latest_article is None
    assert oldest_article is None
    assert feed_count == 5
    assert active_feed_count == 5
    assert processing_log_count == 5
    assert entity_count == 5
    
    # Verify the session was used correctly
    assert mock_session.exec.call_count == 7


@patch('local_newsifier.config.settings.settings')
def test_get_apify_client_with_provided_token(mock_settings):
    """Test that the get_apify_client provider works with a provided token."""
    # Configure the mock settings
    mock_settings.APIFY_TOKEN = None
    
    # Call the provider function with a token
    client = get_apify_client(token="test_token")
    
    # Verify the client was created correctly
    assert client is not None
    assert client.token == "test_token"


@patch('local_newsifier.config.settings.settings')
def test_get_apify_client_with_settings_token(mock_settings):
    """Test that the get_apify_client provider falls back to settings token."""
    # Set up mock settings
    mock_settings.APIFY_TOKEN = "settings_token"
    
    # Call the provider function without a token
    client = get_apify_client()
    
    # Verify the client was created with the settings token
    assert client is not None
    assert client.token == "settings_token"


@patch('local_newsifier.config.settings.settings')
def test_get_apify_client_missing_token(mock_settings):
    """Test that the get_apify_client provider raises an error with no token."""
    # Set up mock settings with no token
    mock_settings.APIFY_TOKEN = None
    
    # Call the provider function without a token should raise ValueError
    with pytest.raises(ValueError, match="Apify token not set"):
        get_apify_client()


def test_get_apify_client_test_mode():
    """Test that the get_apify_client provider works in test mode."""
    # Call the provider function in test mode
    client = get_apify_client(test_mode=True)
    
    # Verify the client is None in test mode (dummy client)
    assert client is None
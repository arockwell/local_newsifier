"""
Test fixtures for injectable-based testing.

This module provides pytest fixtures that make it easier to use injectable provider
functions in tests.
"""

import pytest
from unittest.mock import MagicMock, patch


@pytest.fixture
def patched_injectable():
    """Patch injectable provider functions used in CLI commands.
    
    This fixture creates mocks for the injectable provider functions 
    and makes the mocks available for configuring test behavior.
    """
    # Create mock services
    rss_feed_service_mock = MagicMock()
    article_crud_mock = MagicMock()
    news_pipeline_flow_mock = MagicMock()  
    entity_tracking_flow_mock = MagicMock()
    session_mock = MagicMock()
    
    # Create a mock session generator
    def mock_session_gen():
        yield session_mock
    
    # Patch all the provider functions for CLI commands
    with patch('local_newsifier.cli.commands.feeds.get_rss_feed_service', return_value=rss_feed_service_mock):
        with patch('local_newsifier.cli.commands.feeds.get_article_crud', return_value=article_crud_mock):
            with patch('local_newsifier.cli.commands.feeds.get_news_pipeline_flow', return_value=news_pipeline_flow_mock):
                with patch('local_newsifier.cli.commands.feeds.get_entity_tracking_flow', return_value=entity_tracking_flow_mock):
                    with patch('local_newsifier.cli.commands.feeds.get_db_session', return_value=mock_session_gen()):
                        yield {
                            "rss_feed_service": rss_feed_service_mock,
                            "article_crud": article_crud_mock,
                            "news_pipeline_flow": news_pipeline_flow_mock,
                            "entity_tracking_flow": entity_tracking_flow_mock,
                            "session": session_mock
                        }

# Injectable-based fixture for RSS feed service
@pytest.fixture
def mock_rss_feed_service(patched_injectable):
    """Create a mock RSSFeedService for testing using injectable."""
    return patched_injectable["rss_feed_service"]


# Injectable-based fixture for article CRUD
@pytest.fixture
def mock_article_crud(patched_injectable):
    """Create a mock article CRUD for testing using injectable."""
    return patched_injectable["article_crud"]


# Injectable-based fixture for flow services
@pytest.fixture
def mock_flows(patched_injectable):
    """Create mock flow services for testing using injectable."""
    return {
        "news_pipeline_flow": patched_injectable["news_pipeline_flow"],
        "entity_tracking_flow": patched_injectable["entity_tracking_flow"]
    }

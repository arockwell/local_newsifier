"""
Test fixtures for container-based testing.

This module provides pytest fixtures that make it easier to use the dependency injection
container in tests.
"""

import pytest
from unittest.mock import MagicMock, patch

from local_newsifier.di_container import DIContainer
from tests.utils.test_container import create_test_container, create_mock_session_factory, mock_service


@pytest.fixture
def test_container():
    """Create a test container that doesn't affect other tests."""
    container = create_test_container()
    yield container
    container.clear()


@pytest.fixture
def mock_session(test_container):
    """Create a mock database session for testing."""
    mock_factory, mock_session = create_mock_session_factory()
    test_container.register("session_factory", mock_factory)
    return mock_session


@pytest.fixture
def patched_container(test_container):
    """Patch the singleton container with our test container.
    
    This fixture temporarily replaces the application container with a test container
    and patches injectable provider functions to return mocked services.
    """
    with patch('local_newsifier.container.container', test_container):
        yield test_container


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

@pytest.fixture
def mock_rss_feed_service(patched_container):
    """Create a mock RSSFeedService and register it with the container."""
    mock = mock_service(patched_container, "rss_feed_service")
    return mock


@pytest.fixture
def mock_article_crud(patched_container):
    """Create a mock article CRUD and register it with the container."""
    mock = mock_service(patched_container, "article_crud")
    return mock


@pytest.fixture
def mock_flows(patched_container):
    """Create mock flow services and register them with the container."""
    news_pipeline_flow = mock_service(patched_container, "news_pipeline_flow")
    entity_tracking_flow = mock_service(patched_container, "entity_tracking_flow")
    return {
        "news_pipeline_flow": news_pipeline_flow,
        "entity_tracking_flow": entity_tracking_flow
    }

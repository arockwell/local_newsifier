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
    
    This fixture temporarily replaces the application container with a test container,
    allowing tests to control the behavior of components that directly use the container.
    """
    with patch('local_newsifier.container.container', test_container):
        with patch('local_newsifier.cli.commands.feeds.container', test_container):
            yield test_container


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

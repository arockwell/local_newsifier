"""
Test fixtures for CLI testing with dependency injection.

This module provides pytest fixtures that create test doubles for CLI commands.
"""

import pytest
from unittest.mock import MagicMock


@pytest.fixture
def mock_session():
    """Create a mock database session for testing."""
    session = MagicMock()
    
    # Set up session as context manager
    session.__enter__ = MagicMock(return_value=session)
    session.__exit__ = MagicMock(return_value=None)
    
    return session


@pytest.fixture
def injectable_deps():
    """Create injectable dependencies for CLI testing.
    
    Instead of patching provider functions, this fixture creates
    mock services that can be injected directly into CLI commands.
    
    Returns:
        dict: Mock objects for each service
    """
    # Create mock services
    rss_feed_service = MagicMock()
    article_crud = MagicMock()
    news_pipeline_flow = MagicMock()
    entity_tracking_flow = MagicMock()
    session = MagicMock()
    
    # Set up session as context manager
    session.__enter__ = MagicMock(return_value=session)
    session.__exit__ = MagicMock(return_value=None)
    
    # Return all mocks in a dictionary
    return {
        "rss_feed_service": rss_feed_service,
        "article_crud": article_crud,
        "news_pipeline_flow": news_pipeline_flow,
        "entity_tracking_flow": entity_tracking_flow,
        "session": session
    }

# Fixtures for individual mocked services
@pytest.fixture
def mock_rss_feed_service(injectable_deps):
    """Create a mock RSSFeedService for testing."""
    return injectable_deps["rss_feed_service"]


@pytest.fixture
def mock_article_crud(injectable_deps):
    """Create a mock article CRUD for testing."""
    return injectable_deps["article_crud"]


@pytest.fixture
def mock_flows(injectable_deps):
    """Create mock flow services for testing."""
    return {
        "news_pipeline_flow": injectable_deps["news_pipeline_flow"],
        "entity_tracking_flow": injectable_deps["entity_tracking_flow"]
    }

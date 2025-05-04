"""
Test fixtures for injectable-based testing.

This module provides pytest fixtures for mocking injectable provider functions.
"""

import pytest
from unittest.mock import MagicMock, patch


# Create mock session generator function
def create_mock_session():
    """Create a mock database session generator for testing."""
    session = MagicMock()
    
    # Set up session as context manager
    session.__enter__ = MagicMock(return_value=session)
    session.__exit__ = MagicMock(return_value=None)
    
    def session_gen():
        yield session
    
    return session_gen, session


@pytest.fixture
def patched_injectable(monkeypatch):
    """Patch injectable provider functions for CLI testing.
    
    This fixture creates mocks for injectable provider functions
    and returns them in a dictionary for easy test configuration.
    
    Args:
        monkeypatch: pytest's monkeypatch fixture
        
    Returns:
        dict: Mock objects for each service
    """
    # Create mock services
    rss_feed_service = MagicMock()
    article_crud = MagicMock()
    news_pipeline_flow = MagicMock()
    entity_tracking_flow = MagicMock()
    session_gen, session = create_mock_session()
    
    # Patch provider functions with monkeypatch (cleaner than nested with statements)
    monkeypatch.setattr('local_newsifier.cli.commands.feeds.get_rss_feed_service', lambda: rss_feed_service)
    monkeypatch.setattr('local_newsifier.cli.commands.feeds.get_article_crud', lambda: article_crud) 
    monkeypatch.setattr('local_newsifier.cli.commands.feeds.get_news_pipeline_flow', lambda: news_pipeline_flow)
    monkeypatch.setattr('local_newsifier.cli.commands.feeds.get_entity_tracking_flow', lambda: entity_tracking_flow)
    monkeypatch.setattr('local_newsifier.cli.commands.feeds.get_db_session', lambda: session_gen())
    
    # Return all mocks in a dictionary for easy access
    return {
        "rss_feed_service": rss_feed_service,
        "article_crud": article_crud,
        "news_pipeline_flow": news_pipeline_flow,
        "entity_tracking_flow": entity_tracking_flow,
        "session": session
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

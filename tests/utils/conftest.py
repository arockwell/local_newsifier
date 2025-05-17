"""
Test fixtures for injectable-based testing.

This module provides pytest fixtures that make it easier to use the dependency injection
in tests with fastapi-injectable.
"""

import pytest
from unittest.mock import MagicMock, patch
from sqlmodel import Session


@pytest.fixture
def mock_session():
    """Create a mock database session for testing."""
    mock_session = MagicMock(spec=Session)
    # Setup session as context manager
    mock_session.__enter__ = MagicMock(return_value=mock_session)
    mock_session.__exit__ = MagicMock(return_value=None)
    return mock_session


@pytest.fixture
def mock_session_factory(mock_session):
    """Create a mock session factory that returns the mock session."""
    def factory():
        return mock_session
    return factory


@pytest.fixture
def injectable_mock_services(mock_session, mock_session_factory):
    """Fixture to create and patch injectable services."""
    
    # This dictionary will store our mock services
    mocks = {}
    
    # Create mock for RSSFeedService
    mock_rss_feed_service = MagicMock()
    mocks["rss_feed_service"] = mock_rss_feed_service
    
    # Create mock for ArticleCRUD
    mock_article_crud = MagicMock()
    mocks["article_crud"] = mock_article_crud
    
    # Create mock for flows
    mock_news_pipeline_flow = MagicMock()
    mock_entity_tracking_flow = MagicMock()
    mocks["news_pipeline_flow"] = mock_news_pipeline_flow
    mocks["entity_tracking_flow"] = mock_entity_tracking_flow
    
    # Patch the injectable providers
    with patch("local_newsifier.di.providers.get_session", return_value=mock_session):
        with patch("local_newsifier.di.providers.get_session_factory", return_value=mock_session_factory):
            with patch("local_newsifier.di.providers.get_rss_feed_service", return_value=mock_rss_feed_service):
                with patch("local_newsifier.di.providers.get_article_crud", return_value=mock_article_crud):
                    with patch("local_newsifier.di.providers.get_news_pipeline_flow", return_value=mock_news_pipeline_flow):
                        with patch("local_newsifier.di.providers.get_entity_tracking_flow", return_value=mock_entity_tracking_flow):
                            yield mocks


@pytest.fixture
def mock_rss_feed_service():
    """Create a mock RSSFeedService."""
    return MagicMock()


@pytest.fixture
def mock_article_crud():
    """Create a mock article CRUD."""
    return MagicMock()


@pytest.fixture
def mock_flows():
    """Create mock flow services."""
    news_pipeline_flow = MagicMock()
    entity_tracking_flow = MagicMock()
    return {
        "news_pipeline_flow": news_pipeline_flow,
        "entity_tracking_flow": entity_tracking_flow
    }
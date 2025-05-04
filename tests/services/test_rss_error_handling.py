"""Tests for RSS feed error handling using ServiceError."""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone

from local_newsifier.services.rss_feed_service import RSSFeedService
from local_newsifier.errors import ServiceError


@pytest.fixture
def mock_db_session():
    """Create a mock database session."""
    return MagicMock()


@pytest.fixture
def mock_session_factory(mock_db_session):
    """Create a mock session factory that returns the mock session."""
    mock_factory = MagicMock()
    mock_factory.return_value = mock_db_session
    return mock_factory


def test_get_feed_not_found_raises_service_error(mock_db_session, mock_session_factory):
    """Test ServiceError is raised with appropriate type when feed not found."""
    # Arrange
    feed_id = 999
    mock_rss_feed_crud = MagicMock()
    mock_rss_feed_crud.get.return_value = None
    
    # Create service with session factory
    service = RSSFeedService(
        rss_feed_crud=mock_rss_feed_crud,
        feed_processing_log_crud=MagicMock(),
        article_service=MagicMock(),
        session_factory=mock_session_factory
    )
    
    # Act & Assert
    with pytest.raises(ServiceError) as excinfo:
        service.update_feed(feed_id=feed_id, name="Test Name")
    
    # Verify error properties
    error = excinfo.value
    assert error.service == "rss"
    assert error.error_type == "not_found"
    assert f"Feed with ID {feed_id} not found" in str(error)
    assert error.context["feed_id"] == feed_id


def test_create_duplicate_feed_raises_service_error(mock_db_session, mock_session_factory):
    """Test ServiceError is raised with appropriate type when creating duplicate feed."""
    # Arrange
    url = "https://example.com/feed"
    
    mock_rss_feed_crud = MagicMock()
    mock_existing_feed = MagicMock()
    mock_existing_feed.id = 1
    mock_existing_feed.url = url
    mock_rss_feed_crud.get_by_url.return_value = mock_existing_feed
    
    # Create service with session factory
    service = RSSFeedService(
        rss_feed_crud=mock_rss_feed_crud,
        feed_processing_log_crud=MagicMock(),
        article_service=MagicMock(),
        session_factory=mock_session_factory
    )
    
    # Act & Assert
    with pytest.raises(ServiceError) as excinfo:
        service.create_feed(url=url, name="Test Feed")
    
    # Verify error properties
    error = excinfo.value
    assert error.service == "rss"
    assert error.error_type == "validation"
    assert f"Feed with URL '{url}' already exists" in str(error)
    assert error.context["url"] == url


@patch('local_newsifier.services.rss_feed_service.parse_rss_feed', side_effect=ConnectionError("Failed to connect"))
def test_process_feed_network_error_classification(mock_parse_rss_feed, mock_db_session, mock_session_factory):
    """Test network errors during feed processing are properly classified."""
    # Arrange
    feed_id = 1
    
    mock_rss_feed_crud = MagicMock()
    mock_feed = MagicMock()
    mock_feed.id = feed_id
    mock_feed.url = "https://example.com/feed"
    mock_feed.name = "Example Feed"
    mock_rss_feed_crud.get.return_value = mock_feed
    
    mock_feed_processing_log_crud = MagicMock()
    mock_log = MagicMock()
    mock_log.id = 1
    mock_feed_processing_log_crud.create_processing_started.return_value = mock_log
    
    # Create service with session factory
    service = RSSFeedService(
        rss_feed_crud=mock_rss_feed_crud,
        feed_processing_log_crud=mock_feed_processing_log_crud,
        article_service=MagicMock(),
        session_factory=mock_session_factory
    )
    
    # Act & Assert
    with pytest.raises(ServiceError) as excinfo:
        service.process_feed(feed_id)
    
    # Verify error properties
    error = excinfo.value
    assert error.service == "rss"
    assert error.error_type == "network"
    assert "Failed to connect" in str(error.original)


@patch('local_newsifier.tools.rss_parser.parse_rss_feed', side_effect=ValueError("Invalid XML"))
def test_process_feed_parse_error_classification(mock_parse_rss_feed, mock_db_session, mock_session_factory):
    """Test parse errors during feed processing are properly classified."""
    # Arrange
    feed_id = 1
    
    mock_rss_feed_crud = MagicMock()
    mock_feed = MagicMock()
    mock_feed.id = feed_id
    mock_feed.url = "https://example.com/feed"
    mock_feed.name = "Example Feed"
    mock_rss_feed_crud.get.return_value = mock_feed
    
    mock_feed_processing_log_crud = MagicMock()
    mock_log = MagicMock()
    mock_log.id = 1
    mock_feed_processing_log_crud.create_processing_started.return_value = mock_log
    
    # Create service with session factory
    service = RSSFeedService(
        rss_feed_crud=mock_rss_feed_crud,
        feed_processing_log_crud=mock_feed_processing_log_crud,
        article_service=MagicMock(),
        session_factory=mock_session_factory
    )
    
    # Act & Assert - parser module patch doesn't work here, we need to patch at the source
    with patch('local_newsifier.services.rss_feed_service.parse_rss_feed', side_effect=ValueError("Invalid XML")):
        with pytest.raises(ServiceError) as excinfo:
            service.process_feed(feed_id)
    
    # Verify error is logged in processing log
    mock_feed_processing_log_crud.update_processing_completed.assert_called_once_with(
        mock_db_session,
        log_id=mock_log.id,
        status="error",
        error_message=str(excinfo.value),
    )
    
    # Verify error properties
    error = excinfo.value
    assert error.service == "rss"
    assert error.error_type == "validation"  # ValueError gets classified as validation
    assert "Invalid XML" in str(error.original)
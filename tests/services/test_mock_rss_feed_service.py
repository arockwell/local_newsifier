"""Tests for the RSSFeedService using isolated mocks."""

import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch, call

from local_newsifier.services.rss_feed_service import (
    RSSFeedService,
    register_article_service,
)
from local_newsifier.container import container


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


@patch('local_newsifier.services.rss_feed_service.parse_rss_feed')
def test_process_feed_with_container_task(mock_parse_rss_feed, mock_db_session, mock_session_factory):
    """Test processing a feed with task from container."""
    # Arrange
    feed_id = 1
    
    # Mock process_article_task
    mock_process_article_task = MagicMock()
    mock_process_article_task.delay = MagicMock()
    
    # Mock container
    mock_container = MagicMock()
    mock_container.get.return_value = mock_process_article_task
    
    # Mock RSS feed
    mock_rss_feed_crud = MagicMock()
    
    mock_feed = MagicMock()
    mock_feed.id = feed_id
    mock_feed.url = "https://example.com/feed"
    mock_feed.name = "Example Feed"
    
    mock_rss_feed_crud.get.return_value = mock_feed
    
    # Mock feed processing log
    mock_feed_processing_log_crud = MagicMock()
    
    mock_log = MagicMock()
    mock_log.id = 1
    mock_log.feed_id = feed_id
    
    mock_feed_processing_log_crud.create_processing_started.return_value = mock_log
    
    # Mock article service
    mock_article_service = MagicMock()
    mock_article_service.create_article_from_rss_entry.return_value = 123  # Article ID
    
    # Mock RSS data
    mock_parse_rss_feed.return_value = {
        "feed": {
            "title": "Example Feed",
            "link": "https://example.com",
            "description": "An example feed"
        },
        "entries": [
            {
                "title": "Article 1",
                "link": "https://example.com/article1",
                "description": "First article"
            },
            {
                "title": "Article 2",
                "link": "https://example.com/article2",
                "description": "Second article"
            }
        ]
    }
    
    # Create service with mock container
    service = RSSFeedService(
        rss_feed_crud=mock_rss_feed_crud,
        feed_processing_log_crud=mock_feed_processing_log_crud,
        article_service=mock_article_service,
        session_factory=mock_session_factory,
        container=mock_container
    )
    
    # Act
    result = service.process_feed(feed_id)  # Don't provide task_queue_func
    
    # Assert
    assert mock_article_service.create_article_from_rss_entry.call_count == 2
    assert mock_process_article_task.delay.call_count == 2  # This will verify _process_article_task.delay was called
    mock_process_article_task.delay.assert_has_calls([call(123), call(123)])
    
    assert result["status"] == "success"
    assert result["articles_added"] == 2


def test_process_feed_no_service_with_container(mock_db_session, mock_session_factory):
    """Test processing a feed with no article service but using container."""
    # Arrange
    feed_id = 1
    
    # Mock RSS feed crud
    mock_rss_feed_crud = MagicMock()
    
    mock_feed = MagicMock()
    mock_feed.id = feed_id
    mock_feed.url = "https://example.com/feed"
    mock_feed.name = "Example Feed"
    
    mock_rss_feed_crud.get.return_value = mock_feed
    
    # Mock feed processing log
    mock_feed_processing_log_crud = MagicMock()
    
    mock_log = MagicMock()
    mock_log.id = 1
    mock_feed_processing_log_crud.create_processing_started.return_value = mock_log
    
    # Create a mock ArticleService
    mock_article_service = MagicMock()
    mock_article_service.create_article_from_rss_entry.side_effect = [101, 102]  # Return different IDs for clarity
    
    # Create a mock container that selectively returns mocks
    mock_container = MagicMock()
    def mock_get(name):
        if name == "article_service":
            return None
        if name == "process_article_task":
            return None
        return None
    mock_container.get.side_effect = mock_get
    
    # Create a mock article service factory that returns our mock_article_service
    mock_article_service_factory = MagicMock()
    mock_article_service_factory.return_value = mock_article_service
    
    with patch('local_newsifier.services.rss_feed_service.parse_rss_feed') as mock_parse_rss_feed:
        # Setup mock feed data
        mock_parse_rss_feed.return_value = {
            "feed": {"title": "Example Feed"},
            "entries": [{"title": "Article 1"}, {"title": "Article 2"}]
        }
        
        # Create service instance with mock container and factory
        service = RSSFeedService(
            rss_feed_crud=mock_rss_feed_crud,
            feed_processing_log_crud=mock_feed_processing_log_crud,
            article_service=None,  # No direct article service
            article_service_factory=mock_article_service_factory,  # Use factory instead
            session_factory=mock_session_factory,
            container=mock_container
        )
        
        # Act
        result = service.process_feed(feed_id)
        
        # Assert
        # The service should use the factory to get the article service
        assert mock_article_service_factory.call_count == 2  # Called once for each article
        assert mock_article_service.create_article_from_rss_entry.call_count == 2
        
        assert result["status"] == "success"
        assert result["feed_id"] == feed_id
        assert result["feed_name"] == "Example Feed"
        assert result["articles_found"] == 2
        assert result["articles_added"] == 2


def test_process_feed_temp_service_fails(mock_db_session, mock_session_factory):
    """Test handling when temporary article service creation fails."""
    # Arrange
    feed_id = 1
    
    # Mock RSS feed
    mock_rss_feed_crud = MagicMock()
    
    mock_feed = MagicMock()
    mock_feed.id = feed_id
    mock_feed.url = "https://example.com/feed"
    mock_feed.name = "Example Feed"
    
    mock_rss_feed_crud.get.return_value = mock_feed
    
    # Mock feed processing log
    mock_feed_processing_log_crud = MagicMock()
    
    mock_log = MagicMock()
    mock_log.id = 1
    mock_feed_processing_log_crud.create_processing_started.return_value = mock_log
    
    # Create a mock for error handling
    error_log = MagicMock()
    error_log.id = 1
    error_log.status = "error"
    mock_feed_processing_log_crud.update_processing_completed.return_value = error_log
    
    # Create a mock container that returns None for article_service and process_article_task
    mock_container = MagicMock()
    def mock_get(name):
        if name == "article_service":
            return None
        if name == "process_article_task":
            return None
        return None
    mock_container.get.side_effect = mock_get
    
    # Use a more realistic approach for testing with database errors
    with patch('local_newsifier.services.rss_feed_service.parse_rss_feed') as mock_parse_rss_feed:
                # Mock feed data
                mock_parse_rss_feed.return_value = {
                    "feed": {"title": "Example Feed"},
                    "entries": [{"title": "Article 1"}]
                }
                
                # Create a mock for ArticleService that simulates raising an error during creation_article_from_rss_entry
                mock_article_service = MagicMock()
                mock_article_service.create_article_from_rss_entry.side_effect = ValueError("Database error")
                
                # Setup the ArticleService mock
                with patch('local_newsifier.services.article_service.ArticleService', return_value=mock_article_service):
                    # Create service with no article service
                    service = RSSFeedService(
                        rss_feed_crud=mock_rss_feed_crud,
                        feed_processing_log_crud=mock_feed_processing_log_crud,
                        article_service=None,  # No article service
                        session_factory=mock_session_factory,
                        container=mock_container
                    )
                    
                    # Act - the service will catch the exception but continue processing
                    result = service.process_feed(feed_id)
                    
                    # Assert - even though there was an error in processing an article,
                    # the overall feed process completes successfully 
                    assert result["status"] == "success"
                    assert result["feed_id"] == feed_id
                    # No articles were successfully added due to errors
                    assert result["articles_added"] == 0

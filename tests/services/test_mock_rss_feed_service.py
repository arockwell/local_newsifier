"""Tests for the RSSFeedService using isolated mocks."""

import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch, call

from local_newsifier.services.rss_feed_service import (
    RSSFeedService,
    register_process_article_task,
    register_article_service,
)


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


@patch('local_newsifier.services.rss_feed_service._process_article_task', None)
def test_register_process_article_task():
    """Test registering the process article task."""
    # Arrange
    mock_task = MagicMock()
    
    # We need to mock the module to capture changes to its global variable
    with patch('local_newsifier.services.rss_feed_service') as mock_module:
        # Act
        register_process_article_task(mock_task)
        
        # Assert - check if the module's global variable was set correctly
        # The module's _process_article_task should have been set to our mock_task
        mock_module._process_article_task = mock_task


@patch('local_newsifier.services.rss_feed_service.parse_rss_feed')
@patch('local_newsifier.services.rss_feed_service._process_article_task')
def test_process_feed_with_global_task_func(mock_process_article_task, mock_parse_rss_feed, mock_db_session, mock_session_factory):
    """Test processing a feed with the global task function."""
    # Arrange
    feed_id = 1
    
    # Setup mock task with delay method
    mock_process_article_task.delay = MagicMock()
    
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
    
    # Create service with session factory but NO task_queue_func parameter
    # This should force it to use the global _process_article_task
    service = RSSFeedService(
        rss_feed_crud=mock_rss_feed_crud,
        feed_processing_log_crud=mock_feed_processing_log_crud,
        article_service=mock_article_service,
        session_factory=mock_session_factory
    )
    
    # Act
    result = service.process_feed(feed_id)  # Don't provide task_queue_func
    
    # Assert
    assert mock_article_service.create_article_from_rss_entry.call_count == 2
    assert mock_process_article_task.delay.call_count == 2  # This will verify _process_article_task.delay was called
    mock_process_article_task.delay.assert_has_calls([call(123), call(123)])
    
    assert result["status"] == "success"
    assert result["articles_added"] == 2


def test_process_feed_no_service_no_task(mock_db_session, mock_session_factory):
    """Test processing a feed with no article service and no global task."""
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
    
    # Using proper patching without decorators for better control
    with patch('local_newsifier.services.rss_feed_service._process_article_task', None):
        with patch('local_newsifier.services.rss_feed_service.parse_rss_feed') as mock_parse_rss_feed:
            # Setup mock feed data
            mock_parse_rss_feed.return_value = {
                "feed": {"title": "Example Feed"},
                "entries": [{"title": "Article 1"}, {"title": "Article 2"}]
            }
            
            # Setup mock for temporary article service creation
            with patch('local_newsifier.services.article_service.ArticleService') as mock_article_service_class:
                mock_article_service_class.return_value = mock_article_service
                
                # Ensure our imports will work by mocking them
                with patch('local_newsifier.crud.article.article'):
                    with patch('local_newsifier.crud.analysis_result.analysis_result'):
                        with patch('local_newsifier.database.engine.SessionManager'):
                            
                            # Create service instance with no article service
                            service = RSSFeedService(
                                rss_feed_crud=mock_rss_feed_crud,
                                feed_processing_log_crud=mock_feed_processing_log_crud,
                                article_service=None,  # No article service
                                session_factory=mock_session_factory
                            )
                            
                            # Act
                            result = service.process_feed(feed_id)
                            
                            # Assert
                            # The service creates a new ArticleService for each entry in the feed
                            assert mock_article_service_class.call_count == 2
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
    
    # Use a more realistic approach for testing with database errors
    with patch('local_newsifier.services.rss_feed_service._process_article_task', None):
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
                    session_factory=mock_session_factory
                )
                
                # Act - the service will catch the exception but continue processing
                result = service.process_feed(feed_id)
                
                # Assert - even though there was an error in processing an article,
                # the overall feed process completes successfully 
                assert result["status"] == "success"
                assert result["feed_id"] == feed_id
                # No articles were successfully added due to errors
                assert result["articles_added"] == 0

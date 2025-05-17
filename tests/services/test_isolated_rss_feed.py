"""Tests for RSSFeedService focusing on standard dependency injection pattern."""

import pytest
from unittest.mock import MagicMock, patch
from typing import Any

from local_newsifier.services.rss_feed_service import RSSFeedService


def test_task_queue_func_usage():
    """Test that the service processes feeds and uses the provided task_queue_func."""
    # Create mock dependencies
    mock_rss_feed_crud = MagicMock()
    mock_feed_processing_log_crud = MagicMock()
    mock_article_service = MagicMock()
    mock_session_factory = MagicMock()
    
    # Create mocked feed
    mock_feed = MagicMock()
    mock_feed.id = 1
    mock_feed.url = "https://example.com/feed"
    mock_feed.name = "Example Feed"
    mock_rss_feed_crud.get.return_value = mock_feed
    
    # Create a service instance
    service = RSSFeedService(
        rss_feed_crud=mock_rss_feed_crud,
        feed_processing_log_crud=mock_feed_processing_log_crud,
        article_service=mock_article_service,
        session_factory=mock_session_factory
    )
    
    # Mock parse_rss_feed to return a simple feed with two entries
    mock_feed_data = {
        "feed": {"title": "Example Feed"},
        "entries": [{"title": "Article 1"}, {"title": "Article 2"}]
    }
    
    # Create a mock task_queue_func
    mock_task_queue_func = MagicMock()
    
    # Test using the task_queue_func
    with patch('local_newsifier.services.rss_feed_service.parse_rss_feed', return_value=mock_feed_data):
        # Mock article creation to return fixed IDs
        mock_article_service.create_article_from_rss_entry.side_effect = [101, 102]
        
        # Execute the method with task_queue_func
        result = service.process_feed(1, task_queue_func=mock_task_queue_func)
        
        # Verify result
        assert result["status"] == "success"
        assert result["articles_added"] == 2
        
        # Verify that the task_queue_func was used
        assert mock_task_queue_func.call_count == 2
        mock_task_queue_func.assert_any_call(101)
        mock_task_queue_func.assert_any_call(102)


def test_manual_service_creation():
    """Test manually creating the service with dependencies."""
    # Create mock dependencies
    mock_rss_feed_crud = MagicMock()
    mock_feed_processing_log_crud = MagicMock()
    mock_article_service = MagicMock()
    mock_session_factory = MagicMock()
    mock_session = MagicMock()
    mock_session_factory.return_value.__enter__.return_value = mock_session
    
    # Create the service manually (no DI)
    service = RSSFeedService(
        rss_feed_crud=mock_rss_feed_crud,
        feed_processing_log_crud=mock_feed_processing_log_crud,
        article_service=mock_article_service,
        session_factory=mock_session_factory
    )
    
    # Verify the service has the right dependencies
    assert service.rss_feed_crud == mock_rss_feed_crud
    assert service.feed_processing_log_crud == mock_feed_processing_log_crud
    assert service.article_service == mock_article_service
    assert service.session_factory == mock_session_factory


def test_service_error_handling():
    """Test that the service handles errors during feed processing."""
    # Create mock dependencies
    mock_rss_feed_crud = MagicMock()
    mock_feed_processing_log_crud = MagicMock()
    mock_article_service = MagicMock()
    mock_session_factory = MagicMock()
    mock_session = MagicMock()
    mock_session_factory.return_value.__enter__.return_value = mock_session
    
    # Create mocked feed
    mock_feed = MagicMock()
    mock_feed.id = 1
    mock_feed.url = "https://example.com/feed"
    mock_feed.name = "Example Feed"
    mock_rss_feed_crud.get.return_value = mock_feed
    
    # Create mocked log
    mock_log = MagicMock()
    mock_log.id = 1
    mock_feed_processing_log_crud.create_processing_started.return_value = mock_log
    
    # Configure the processing log for error handling
    error_log = MagicMock()
    error_log.status = "error"
    mock_feed_processing_log_crud.update_processing_completed.return_value = error_log
    
    # Create a service instance
    service = RSSFeedService(
        rss_feed_crud=mock_rss_feed_crud,
        feed_processing_log_crud=mock_feed_processing_log_crud,
        article_service=mock_article_service,
        session_factory=mock_session_factory
    )
    
    # Test with an exception during RSS feed parsing
    with patch('local_newsifier.services.rss_feed_service.parse_rss_feed', side_effect=Exception("Test error")):
        # Execute the method
        result = service.process_feed(1)
        
        # Verify error result
        assert result["status"] == "error"
        assert "message" in result
        assert "Test error" in result["message"]
        
        # Verify error was logged
        mock_feed_processing_log_crud.update_processing_completed.assert_called_once_with(
            mock_session, 
            log_id=mock_log.id, 
            status="error", 
            error_message="Test error"
        )


def test_service_processes_feed_entries():
    """Test that the service processes all entries in a feed."""
    # Create mock dependencies
    mock_rss_feed_crud = MagicMock()
    mock_feed_processing_log_crud = MagicMock()
    mock_article_service = MagicMock()
    mock_session_factory = MagicMock()
    mock_session = MagicMock()
    mock_session_factory.return_value.__enter__.return_value = mock_session
    
    # Create mocked feed
    mock_feed = MagicMock()
    mock_feed.id = 1
    mock_feed.url = "https://example.com/feed"
    mock_feed.name = "Example Feed"
    mock_rss_feed_crud.get.return_value = mock_feed
    
    # Create a service instance
    service = RSSFeedService(
        rss_feed_crud=mock_rss_feed_crud,
        feed_processing_log_crud=mock_feed_processing_log_crud,
        article_service=mock_article_service,
        session_factory=mock_session_factory
    )
    
    # Create a large feed with 10 entries
    entries = [{"title": f"Article {i}", "link": f"https://example.com/article{i}"} for i in range(1, 11)]
    mock_feed_data = {
        "feed": {"title": "Example Feed"},
        "entries": entries
    }
    
    # Create article IDs for the response
    article_ids = list(range(101, 111))
    mock_article_service.create_article_from_rss_entry.side_effect = article_ids
    
    # Create a mock task_queue_func
    mock_task_queue_func = MagicMock()
    
    # Test processing all entries
    with patch('local_newsifier.services.rss_feed_service.parse_rss_feed', return_value=mock_feed_data):
        # Execute the method
        result = service.process_feed(1, task_queue_func=mock_task_queue_func)
        
        # Verify result
        assert result["status"] == "success"
        assert result["articles_added"] == 10
        assert result["articles_found"] == 10
        
        # Verify all articles were created
        assert mock_article_service.create_article_from_rss_entry.call_count == 10
        
        # Verify all tasks were queued
        assert mock_task_queue_func.call_count == 10
        for article_id in article_ids:
            mock_task_queue_func.assert_any_call(article_id)
        
        # Verify feed last_fetched was updated
        mock_rss_feed_crud.update_last_fetched.assert_called_once_with(mock_session, id=1)


def test_list_feeds():
    """Test the list_feeds method of RSSFeedService."""
    # Create mock dependencies 
    mock_rss_feed_crud = MagicMock()
    mock_feed_processing_log_crud = MagicMock()
    mock_article_service = MagicMock()
    mock_session_factory = MagicMock()
    mock_session = MagicMock()
    mock_session_factory.return_value.__enter__.return_value = mock_session
    
    # Create the service directly
    service = RSSFeedService(
        rss_feed_crud=mock_rss_feed_crud,
        feed_processing_log_crud=mock_feed_processing_log_crud,
        article_service=mock_article_service,
        session_factory=mock_session_factory
    )
    
    # Setup mock feeds
    from datetime import datetime, timezone
    created_at = datetime.now(timezone.utc)
    updated_at = datetime.now(timezone.utc)
    
    # Create mock feeds with proper datetime objects
    mock_feed1 = MagicMock()
    mock_feed1.id = 1
    mock_feed1.url = "https://example.com/feed1"
    mock_feed1.name = "Feed 1"
    mock_feed1.description = "Description 1"
    mock_feed1.is_active = True
    mock_feed1.last_fetched_at = None
    mock_feed1.created_at = created_at
    mock_feed1.updated_at = updated_at
    
    mock_feed2 = MagicMock()
    mock_feed2.id = 2
    mock_feed2.url = "https://example.com/feed2"
    mock_feed2.name = "Feed 2"
    mock_feed2.description = "Description 2"
    mock_feed2.is_active = False
    mock_feed2.last_fetched_at = None
    mock_feed2.created_at = created_at
    mock_feed2.updated_at = updated_at
    
    # Configure the mock to return our test feeds
    mock_rss_feed_crud.get_multi.return_value = [mock_feed1, mock_feed2]
    mock_rss_feed_crud.get_active_feeds.return_value = [mock_feed1]
    
    # Test listing all feeds
    all_feeds = service.list_feeds()
    assert len(all_feeds) == 2
    assert all_feeds[0]["id"] == 1
    assert all_feeds[1]["id"] == 2
    
    # Test listing only active feeds
    active_feeds = service.list_feeds(active_only=True)
    assert len(active_feeds) == 1
    assert active_feeds[0]["id"] == 1
    
    # Verify the crud methods were called correctly
    mock_rss_feed_crud.get_multi.assert_called_once_with(mock_session, skip=0, limit=100)
    mock_rss_feed_crud.get_active_feeds.assert_called_once_with(mock_session, skip=0, limit=100)

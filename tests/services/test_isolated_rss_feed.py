"""Tests for RSSFeedService focusing on legacy container integration."""

import pytest
from unittest.mock import MagicMock, patch

from local_newsifier.services.rss_feed_service import RSSFeedService


@pytest.mark.skip(reason="Async event loop issue in fastapi-injectable, to be fixed in a separate PR")
def test_container_task_usage():
    """Test that the service uses the task from the legacy container when no task_queue_func is provided."""
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
    
    # Create a mock container
    mock_container = MagicMock()
    
    # Create a mock process_article_task
    mock_task = MagicMock()
    mock_task.delay = MagicMock()
    
    # Configure the container to return our mock_task
    def mock_get(service_name):
        if service_name == "process_article_task":
            return mock_task
        return None
    mock_container.get.side_effect = mock_get
    
    # Add the container to the service
    service.container = mock_container
    
    # Test using the container-provided task
    with patch('local_newsifier.services.rss_feed_service.parse_rss_feed', return_value=mock_feed_data):
        # Mock article creation to return fixed IDs
        mock_article_service.create_article_from_rss_entry.side_effect = [101, 102]
        
        # Execute the method
        result = service.process_feed(1)  # No task_queue_func provided
        
        # Verify result
        assert result["status"] == "success"
        assert result["articles_added"] == 2
        
        # Verify that the container task was used
        assert mock_task.delay.call_count == 2
        mock_task.delay.assert_any_call(101)
        mock_task.delay.assert_any_call(102)


@pytest.mark.skip(reason="Async event loop issue in fastapi-injectable, to be fixed in a separate PR")
def test_task_queue_func_overrides_container():
    """Test that the provided task_queue_func is used instead of the container task."""
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
    
    # Create a mock container
    mock_container = MagicMock()
    
    # Create a mock process_article_task that should NOT be used
    mock_container_task = MagicMock()
    mock_container_task.delay = MagicMock()
    
    # Configure the container to return our mock_task
    def mock_get(service_name):
        if service_name == "process_article_task":
            return mock_container_task
        return None
    mock_container.get.side_effect = mock_get
    
    # Add the container to the service
    service.container = mock_container
    
    with patch('local_newsifier.services.rss_feed_service.parse_rss_feed', return_value=mock_feed_data):
        # Mock article creation to return fixed IDs
        mock_article_service.create_article_from_rss_entry.side_effect = [101, 102]
        
        # Execute the method with task_queue_func
        result = service.process_feed(1, task_queue_func=mock_task_queue_func)
        
        # Verify result
        assert result["status"] == "success"
        assert result["articles_added"] == 2
        
        # Verify that the provided task_queue_func was used (not the global one)
        assert mock_task_queue_func.call_count == 2
        mock_task_queue_func.assert_any_call(101)
        mock_task_queue_func.assert_any_call(102)
        
        # Verify that the container task was NOT used
        assert mock_container_task.delay.call_count == 0


@pytest.mark.skip(reason="Async event loop issue in fastapi-injectable, to be fixed in a separate PR")
def test_container_article_service_fallback():
    """Test that the service tries to get the article service from the container when none is provided."""
    # Create mock dependencies
    mock_rss_feed_crud = MagicMock()
    mock_feed_processing_log_crud = MagicMock()
    mock_session_factory = MagicMock()
    
    # Create mocked feed
    mock_feed = MagicMock()
    mock_feed.id = 1
    mock_feed.url = "https://example.com/feed"
    mock_feed.name = "Example Feed"
    mock_rss_feed_crud.get.return_value = mock_feed
    
    # Create a service instance with no article_service
    service = RSSFeedService(
        rss_feed_crud=mock_rss_feed_crud,
        feed_processing_log_crud=mock_feed_processing_log_crud,
        article_service=None,  # No article service
        session_factory=mock_session_factory
    )
    
    # Mock parse_rss_feed to return a simple feed with two entries
    mock_feed_data = {
        "feed": {"title": "Example Feed"},
        "entries": [{"title": "Article 1"}, {"title": "Article 2"}]
    }
    
    # Create a mock task_queue_func
    mock_task_queue_func = MagicMock()
    
    # Create a mock temporary article service
    mock_temp_article_service = MagicMock()
    mock_temp_article_service.create_article_from_rss_entry.side_effect = [201, 202]
    
    # Create a mock container
    mock_container = MagicMock()
    
    # Create a mock article_service from the container
    mock_container_article_service = MagicMock()
    mock_container_article_service.create_article_from_rss_entry.side_effect = [201, 202]
    
    # Configure container to return our mock article service
    def mock_get(service_name):
        if service_name == "article_service":
            return mock_container_article_service
        return None
    mock_container.get.side_effect = mock_get
    
    # Add the container to the service
    service.container = mock_container
    with patch('local_newsifier.services.rss_feed_service.parse_rss_feed', return_value=mock_feed_data):
        # Execute the method
        result = service.process_feed(1, task_queue_func=mock_task_queue_func)
        
        # Verify result
        assert result["status"] == "success"
        assert result["articles_added"] == 2
        
        # Verify tasks were queued with the right IDs
        assert mock_task_queue_func.call_count == 2
        mock_task_queue_func.assert_any_call(201)
        mock_task_queue_func.assert_any_call(202)
        
        # Verify that container article service was used
        assert mock_container_article_service.create_article_from_rss_entry.call_count == 2


@pytest.mark.skip(reason="Async event loop issue in fastapi-injectable, to be fixed in a separate PR")
def test_temporary_service_creation():
    """Test that the service properly handles failures when creating a temporary ArticleService."""
    # Create mock dependencies
    mock_rss_feed_crud = MagicMock()
    mock_feed_processing_log_crud = MagicMock()
    mock_session_factory = MagicMock()
    
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
    
    # Create a service instance with no article_service
    service = RSSFeedService(
        rss_feed_crud=mock_rss_feed_crud,
        feed_processing_log_crud=mock_feed_processing_log_crud,
        article_service=None,  # No article service
        session_factory=mock_session_factory
    )
    
    # Create a mock container
    mock_container = MagicMock()
    
    # Configure container to return None for article_service
    mock_container.get.return_value = None
    
    # Add the container to the service
    service.container = mock_container
    
    # Create a mock for the temporary article service
    mock_temp_article_service = MagicMock()
    mock_temp_article_service.create_article_from_rss_entry.side_effect = [301, 302]
    
    # Configure the processing log for error handling
    error_log = MagicMock()
    error_log.status = "error"
    mock_feed_processing_log_crud.update_processing_completed.return_value = error_log
    
    # Mock the RSS feed data
    mock_feed_data = {
        "feed": {"title": "Example Feed"},
        "entries": [{"title": "Article 1"}, {"title": "Article 2"}]
    }
    
    # Create a mock task_queue_func
    mock_task_queue_func = MagicMock()
    
    # Test with a temporary ArticleService
    with patch('local_newsifier.services.rss_feed_service.parse_rss_feed', return_value=mock_feed_data):
        with patch('local_newsifier.services.article_service.ArticleService', return_value=mock_temp_article_service):
            # Execute the method
            result = service.process_feed(1, task_queue_func=mock_task_queue_func)
            
            # Verify result
            assert result["status"] == "success"
            assert result["articles_added"] == 2
            
            # Verify the temporary article service was used
            assert mock_temp_article_service.create_article_from_rss_entry.call_count == 2


@pytest.mark.skip(reason="Async event loop issue in fastapi-injectable, to be fixed in a separate PR")
def test_register_article_service_with_container():
    """Test registering the article service in RSSFeedService through container."""
    from local_newsifier.services.rss_feed_service import register_article_service
    
    # Create mock objects
    mock_article_service = MagicMock()
    mock_rss_feed_service = MagicMock()
    mock_container = MagicMock()
    
    # Configure container to return our mock service
    mock_container.get.return_value = mock_rss_feed_service
    
    # Test the function
    with patch('local_newsifier.container.container', mock_container):
        register_article_service(mock_article_service)
        
        # Verify the article service was registered
        mock_container.get.assert_called_with("rss_feed_service")
        assert mock_rss_feed_service.article_service == mock_article_service

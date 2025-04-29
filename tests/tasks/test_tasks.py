"""
Unit tests for Celery tasks in the Local Newsifier project.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, call

from celery import Task
from celery.result import AsyncResult

from local_newsifier.tasks import (
    fetch_rss_feeds,
    process_article
)


@pytest.fixture
def mock_container():
    """Mock container fixture for providing service dependencies."""
    mock_article_service = MagicMock()
    mock_article_crud = MagicMock()
    mock_entity_crud = MagicMock()
    mock_entity_service = MagicMock()
    mock_rss_feed_service = MagicMock()
    
    with patch("local_newsifier.tasks.container") as mock_container_obj:
        # Setup container to return mocked services
        def mock_get(service_name):
            if service_name == "article_service":
                return mock_article_service
            elif service_name == "article_crud":
                return mock_article_crud
            elif service_name == "entity_crud":
                return mock_entity_crud
            elif service_name == "entity_service":
                return mock_entity_service
            elif service_name == "rss_feed_service":
                return mock_rss_feed_service
            return None
            
        mock_container_obj.get.side_effect = mock_get
        
        yield (
            mock_container_obj, 
            mock_article_service, 
            mock_article_crud, 
            mock_entity_crud,
            mock_entity_service,
            mock_rss_feed_service
        )


@pytest.fixture
def mock_article():
    """Fixture for a mock article."""
    article = Mock()
    article.id = 1
    article.title = "Test Article"
    article.url = "https://example.com/test-article"
    article.content = "This is a test article about entities."
    return article


class TestBaseTask:
    """Tests for the BaseTask class."""
    
    def test_session_factory_property(self, mock_container):
        """Test that the session_factory property returns factory from container."""
        # Set up mock
        mock_container_obj, _, _, _, _, _ = mock_container
        mock_session_factory = Mock()
        
        # Configure container to return our mock session factory
        def mock_get(service_name):
            if service_name == "session_factory":
                return mock_session_factory
            return Mock()
        
        mock_container_obj.get.side_effect = mock_get
        
        # Need to get a task instance to test
        task = process_article
        
        # Reset the _session_factory attribute to force getting from container
        task._session_factory = None
        
        # Access the session_factory property
        factory = task.session_factory
        assert factory is mock_session_factory
        mock_container_obj.get.assert_any_call("session_factory")
    
    def test_db_property(self, mock_container):
        """Test that the db property returns a database session from session factory."""
        # Set up mock
        mock_container_obj, _, _, _, _, _ = mock_container
        mock_session = Mock()
        mock_session_factory = Mock()
        mock_session_factory.return_value = Mock()
        mock_session_factory.return_value.__enter__ = Mock(return_value=mock_session)
        
        # Configure container to return our mock session factory
        def mock_get(service_name):
            if service_name == "session_factory":
                return mock_session_factory
            return Mock()
        
        mock_container_obj.get.side_effect = mock_get
        
        # Need to get a task instance to test
        task = process_article
        
        # Reset the attributes to force getting new instances
        task._session_factory = None
        task._session = None
        
        # Access the db property
        db = task.db
        assert db is mock_session
        mock_container_obj.get.assert_any_call("session_factory")
        mock_session_factory.return_value.__enter__.assert_called_once()
        
    def test_article_service_property(self, mock_container):
        """Test that the article_service property returns service from container."""
        _, mock_article_service, _, _, _, _ = mock_container
        
        # Need to get a task instance to test
        task = process_article
        
        # Access the article_service property
        service = task.article_service
        
        # Verify the mock container was used
        assert service is mock_article_service
        
    def test_article_crud_property(self, mock_container):
        """Test that the article_crud property returns crud from container."""
        _, _, mock_article_crud, _, _, _ = mock_container
        
        # Need to get a task instance to test
        task = process_article
        
        # Access the article_crud property
        crud = task.article_crud
        
        # Verify the mock container was used
        assert crud is mock_article_crud
        
    def test_entity_crud_property(self, mock_container):
        """Test that the entity_crud property returns crud from container."""
        _, _, _, mock_entity_crud, _, _ = mock_container
        
        # Need to get a task instance to test
        task = process_article
        
        # Access the entity_crud property
        crud = task.entity_crud
        
        # Verify the mock container was used
        assert crud is mock_entity_crud


class TestProcessArticle:
    """Tests for the process_article task."""
    
    @patch("local_newsifier.tasks.NewsPipelineFlow")
    @patch("local_newsifier.tasks.EntityTrackingFlow")
    def test_process_article_success(
        self, mock_entity_flow_class, mock_pipeline_class, 
        mock_article, mock_container
    ):
        """Test that the process_article task processes an article successfully."""
        # Unpack mock container
        _, _, mock_article_crud, _, _, _ = mock_container
        
        # Create a mock task instance with a mock session factory
        task = process_article
        mock_session = Mock()
        mock_session_factory = Mock()
        mock_session_factory.return_value.__enter__ = Mock(return_value=mock_session)
        mock_session_factory.return_value.__exit__ = Mock(return_value=None)
        task._session_factory = mock_session_factory
        
        # Setup mocks
        mock_article_crud.get.return_value = mock_article
        
        # Setup mock flow instances
        mock_pipeline = Mock()
        mock_entity_flow = Mock()
        mock_pipeline_class.return_value = mock_pipeline
        mock_entity_flow_class.return_value = mock_entity_flow
        
        # Setup mock return values
        mock_entity_flow.process_article.return_value = [{"id": 1, "name": "Test Entity"}]
        
        # Call the task
        result = process_article(mock_article.id)
            
        # Verify session was used properly
        mock_session_factory.return_value.__enter__.assert_called_once()
        mock_session_factory.return_value.__exit__.assert_called_once()
        
        # Verify task called methods with session
        mock_article_crud.get.assert_called_once_with(mock_session, id=mock_article.id)
        mock_pipeline.process_url_directly.assert_called_once_with(mock_article.url)
        mock_entity_flow.process_article.assert_called_once_with(mock_article.id)
        
        # Verify result
        assert result["article_id"] == mock_article.id
        assert result["status"] == "success"
        assert result["processed"] is True
        assert result["entities_found"] == 1
        assert result["article_title"] == mock_article.title
        
    def test_process_article_not_found(self, mock_container):
        """Test that the process_article task handles a missing article properly."""
        # Unpack mock container
        _, _, mock_article_crud, _, _, _ = mock_container
        
        # Create a mock task instance with a mock session factory
        task = process_article
        mock_session = Mock()
        mock_session_factory = Mock()
        mock_session_factory.return_value.__enter__ = Mock(return_value=mock_session)
        mock_session_factory.return_value.__exit__ = Mock(return_value=None)
        task._session_factory = mock_session_factory
        
        # Setup mocks
        mock_article_crud.get.return_value = None
        
        # Call the task
        result = process_article(999)
        
        # Verify session was used properly
        mock_session_factory.return_value.__enter__.assert_called_once()
        mock_session_factory.return_value.__exit__.assert_called_once()
        
        # Verify task called methods with session
        mock_article_crud.get.assert_called_once_with(mock_session, id=999)
        
        # Verify result
        assert result["article_id"] == 999
        assert result["status"] == "error"
        assert "Article not found" in result["message"]
        
    def test_process_article_error(self, mock_article, mock_container):
        """Test that the process_article task handles errors properly."""
        # Unpack mock container
        _, _, mock_article_crud, _, _, _ = mock_container
        
        # Create a mock task instance with a mock session factory
        task = process_article
        mock_session = Mock()
        mock_session_factory = Mock()
        mock_session_factory.return_value.__enter__ = Mock(return_value=mock_session)
        mock_session_factory.return_value.__exit__ = Mock(return_value=None)
        task._session_factory = mock_session_factory
        
        # Setup mocks
        mock_article_crud.get.return_value = mock_article
        
        # Mock NewsPipelineFlow to raise an exception
        with patch("local_newsifier.tasks.NewsPipelineFlow") as mock_pipeline_class:
            mock_pipeline = Mock()
            mock_pipeline_class.return_value = mock_pipeline
            mock_pipeline.process_url_directly.side_effect = Exception("Test error")
            
            # Call the task
            result = process_article(mock_article.id)
            
            # Verify session handling occurred
            mock_session_factory.return_value.__enter__.assert_called_once()
            mock_session_factory.return_value.__exit__.assert_called_once()
            
            # Verify task called methods with session
            mock_article_crud.get.assert_called_once_with(mock_session, id=mock_article.id)
            
            # Verify result
            assert result["article_id"] == mock_article.id
            assert result["status"] == "error"
            assert "Test error" in result["message"]


class TestFetchRssFeeds:
    """Tests for the fetch_rss_feeds task."""
    
    @patch("local_newsifier.tasks.parse_rss_feed")
    def test_fetch_rss_feeds_success(
        self, mock_parse_rss, mock_container
    ):
        """Test that the fetch_rss_feeds task fetches feeds successfully."""
        # Unpack mock container
        _, mock_article_service, mock_article_crud, _, _, _ = mock_container
        
        # Create a mock task instance with a mock session factory
        task = fetch_rss_feeds
        mock_session = Mock()
        mock_session_factory = Mock()
        mock_session_factory.return_value.__enter__ = Mock(return_value=mock_session)
        mock_session_factory.return_value.__exit__ = Mock(return_value=None)
        task._session_factory = mock_session_factory
        
        # Setup mocks
        feed_urls = ["https://example.com/feed1", "https://example.com/feed2"]
        
        # Mock parse_rss_feed
        mock_parse_rss.side_effect = [
            {
                "title": "Feed 1",
                "entries": [
                    {"title": "Article 1", "link": "https://example.com/article1"},
                    {"title": "Article 2", "link": "https://example.com/article2"},
                ]
            },
            {
                "title": "Feed 2",
                "entries": [
                    {"title": "Article 3", "link": "https://example.com/article3"},
                ]
            }
        ]
        
        # Mock article_crud
        mock_article_crud.get_by_url.return_value = None
        
        # Mock create_article_from_rss_entry to return article ID
        mock_article_service.create_article_from_rss_entry.return_value = 1  # Return ID directly
        
        # Mock process_article task
        with patch("local_newsifier.tasks.process_article") as mock_process:
            mock_async_result = Mock(spec=AsyncResult)
            mock_process.delay.return_value = mock_async_result
            
            # Call the task
            result = fetch_rss_feeds(feed_urls)
            
            # Verify session was used properly
            mock_session_factory.return_value.__enter__.assert_called_once()
            mock_session_factory.return_value.__exit__.assert_called_once()
            
            # Verify methods were called with session
            assert mock_article_crud.get_by_url.call_count == 3
            calls = [call(mock_session, url="https://example.com/article1"),
                    call(mock_session, url="https://example.com/article2"),
                    call(mock_session, url="https://example.com/article3")]
            mock_article_crud.get_by_url.assert_has_calls(calls, any_order=False)
            
            # Verify other call counts
            assert mock_parse_rss.call_count == 2
            assert mock_article_service.create_article_from_rss_entry.call_count == 3
            assert mock_process.delay.call_count == 3
            
            # Verify results
            assert result["feeds_processed"] == 2
            assert result["articles_found"] == 3
            assert result["articles_added"] == 3
        
    @patch("local_newsifier.tasks.parse_rss_feed")
    def test_fetch_rss_feeds_with_existing_articles(
        self, mock_parse_rss, mock_container
    ):
        """Test that the fetch_rss_feeds task handles existing articles properly."""
        # Unpack mock container
        _, mock_article_service, mock_article_crud, _, _, _ = mock_container
        
        # Create a mock task instance with a mock session factory
        task = fetch_rss_feeds
        mock_session = Mock()
        mock_session_factory = Mock()
        mock_session_factory.return_value.__enter__ = Mock(return_value=mock_session)
        mock_session_factory.return_value.__exit__ = Mock(return_value=None)
        task._session_factory = mock_session_factory
        
        # Setup mocks
        feed_urls = ["https://example.com/feed1"]
        
        # Mock parse_rss_feed
        mock_parse_rss.return_value = {
            "title": "Feed 1",
            "entries": [
                {"title": "Article 1", "link": "https://example.com/article1"},
                {"title": "Article 2", "link": "https://example.com/article2"},
            ]
        }
        
        # Mock article_crud - first article exists, second doesn't
        existing_article = Mock()
        mock_article_crud.get_by_url.side_effect = [existing_article, None]
        
        # Mock create_article_from_rss_entry to return article ID
        mock_article_service.create_article_from_rss_entry.return_value = 2  # Return ID directly
        
        # Mock process_article task
        with patch("local_newsifier.tasks.process_article") as mock_process:
            mock_async_result = Mock(spec=AsyncResult)
            mock_process.delay.return_value = mock_async_result
            
            # Call the task
            result = fetch_rss_feeds(feed_urls)
            
            # Verify session was used properly
            mock_session_factory.return_value.__enter__.assert_called_once()
            mock_session_factory.return_value.__exit__.assert_called_once()
            
            # Verify methods were called with session
            assert mock_article_crud.get_by_url.call_count == 2
            calls = [call(mock_session, url="https://example.com/article1"),
                    call(mock_session, url="https://example.com/article2")]
            mock_article_crud.get_by_url.assert_has_calls(calls, any_order=False)
            
            # Verify other calls
            assert mock_parse_rss.call_count == 1
            assert mock_article_service.create_article_from_rss_entry.call_count == 1
            assert mock_process.delay.call_count == 1
            
            # Verify results
            assert result["feeds_processed"] == 1
            assert result["articles_found"] == 2
            assert result["articles_added"] == 1

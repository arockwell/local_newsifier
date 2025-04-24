"""
Unit tests for Celery tasks in the Local Newsifier project.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, call

from celery import Task
from celery.result import AsyncResult

from local_newsifier.tasks import (
    fetch_rss_feeds,
    process_article,
    article_crud,
    article_service, 
    entity_crud
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


@pytest.fixture
def mock_article_crud():
    """Fixture for a mock ArticleCRUD instance."""
    crud = Mock()
    return crud


@pytest.fixture
def mock_entity_crud():
    """Fixture for a mock EntityCRUD instance."""
    crud = Mock()
    return crud


class TestBaseTask:
    """Tests for the BaseTask class."""
    
    def test_db_property(self, monkeypatch):
        """Test that the db property returns a database session."""
        # Set up mock
        mock_session = Mock()
        mock_get_db = Mock(return_value=iter([mock_session]))
        monkeypatch.setattr("local_newsifier.tasks.get_db", mock_get_db)
        
        # Need to get a task instance to test
        task = process_article
        
        # Access the db property
        db = task.db
        assert db is mock_session
        
    def test_article_service_property(self):
        """Test that the article_service property returns an ArticleService instance."""
        # Need to get a task instance to test
        task = process_article
        
        # Access the article_service property
        service = task.article_service
        from local_newsifier.services.article_service import ArticleService
        assert isinstance(service, ArticleService)
        
    def test_article_crud_property(self):
        """Test that the article_crud property returns an ArticleCRUD instance."""
        # Need to get a task instance to test
        task = process_article
        
        # Access the article_crud property
        crud = task.article_crud
        from local_newsifier.crud.article import CRUDArticle
        assert isinstance(crud, CRUDArticle)
        
    def test_entity_crud_property(self):
        """Test that the entity_crud property returns an EntityCRUD instance."""
        # Need to get a task instance to test
        task = process_article
        
        # Access the entity_crud property
        crud = task.entity_crud
        from local_newsifier.crud.entity import CRUDEntity
        assert isinstance(crud, CRUDEntity)


class TestProcessArticle:
    """Tests for the process_article task."""
    
    @patch("local_newsifier.tasks.NewsPipelineFlow")
    @patch("local_newsifier.tasks.EntityTrackingFlow")
    def test_process_article_success(
        self, mock_entity_flow_class, mock_pipeline_class, 
        mock_article, mock_article_crud
    ):
        """Test that the process_article task processes an article successfully."""
        # Setup mocks
        mock_article_crud.get.return_value = mock_article
        
        # Setup mock flow instances
        mock_pipeline = Mock()
        mock_entity_flow = Mock()
        mock_pipeline_class.return_value = mock_pipeline
        mock_entity_flow_class.return_value = mock_entity_flow
        
        # Setup mock return values
        mock_entity_flow.process_article.return_value = [{"id": 1, "name": "Test Entity"}]
        
        # Patch the module-level _crud_article variable
        with patch("local_newsifier.tasks._crud_article", mock_article_crud):
            # Call the task
            result = process_article(mock_article.id)
            
            # Verify
            assert mock_article_crud.get.call_count == 1
            mock_pipeline.process_url_directly.assert_called_once_with(mock_article.url)
            mock_entity_flow.process_article.assert_called_once_with(mock_article.id)
            
            assert result["article_id"] == mock_article.id
            assert result["status"] == "success"
            assert result["processed"] is True
            assert result["entities_found"] == 1
            assert result["article_title"] == mock_article.title
        
    def test_process_article_not_found(self, mock_article_crud):
        """Test that the process_article task handles a missing article properly."""
        # Setup mocks
        mock_article_crud.get.return_value = None
        
        # Patch the module-level _crud_article variable
        with patch("local_newsifier.tasks._crud_article", mock_article_crud):
            # Call the task
            result = process_article(999)
            
            # Verify
            assert mock_article_crud.get.call_count == 1
            # Skip checking exact args, just make sure it was called
            assert result["article_id"] == 999
            assert result["status"] == "error"
            assert "Article not found" in result["message"]
        
    def test_process_article_error(self, mock_article, mock_article_crud):
        """Test that the process_article task handles errors properly."""
        # Setup mocks
        mock_article_crud.get.return_value = mock_article
        
        # Patch the module-level _crud_article variable
        with patch("local_newsifier.tasks._crud_article", mock_article_crud):
            # Mock NewsPipelineFlow to raise an exception
            with patch("local_newsifier.tasks.NewsPipelineFlow") as mock_pipeline_class:
                mock_pipeline = Mock()
                mock_pipeline_class.return_value = mock_pipeline
                mock_pipeline.process_url_directly.side_effect = Exception("Test error")
                
                # Call the task
                result = process_article(mock_article.id)
                
                # Verify
                assert mock_article_crud.get.call_count == 1
                assert result["article_id"] == mock_article.id
                assert result["status"] == "error"
                assert "Test error" in result["message"]
class TestFetchRssFeeds:
    """Tests for the fetch_rss_feeds task."""
    
    @patch("local_newsifier.tasks.parse_rss_feed")
    def test_fetch_rss_feeds_success(
        self, mock_parse_rss, mock_article_crud
    ):
        """Test that the fetch_rss_feeds task fetches feeds successfully."""
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
        
        # Mock article_service
        mock_article_service = Mock()
        
        # Mock create_article_from_rss_entry
        mock_article = Mock()
        mock_article.id = 1
        mock_article_service.create_article_from_rss_entry.return_value = mock_article
        
        # Patch the module-level CRUD and service
        with patch("local_newsifier.tasks._crud_article", mock_article_crud):
            with patch("local_newsifier.tasks._service_article", mock_article_service):
                # Mock process_article task
                with patch("local_newsifier.tasks.process_article") as mock_process:
                    mock_async_result = Mock(spec=AsyncResult)
                    mock_process.delay.return_value = mock_async_result
                    
                    # Call the task
                    result = fetch_rss_feeds(feed_urls)
                    
                    # Verify
                    assert mock_parse_rss.call_count == 2
                    assert mock_article_service.create_article_from_rss_entry.call_count == 3
                    assert mock_process.delay.call_count == 3
                    
                    assert result["feeds_processed"] == 2
                    assert result["articles_found"] == 3
                    assert result["articles_added"] == 3
        
    @patch("local_newsifier.tasks.parse_rss_feed")
    def test_fetch_rss_feeds_with_existing_articles(
        self, mock_parse_rss, mock_article_crud
    ):
        """Test that the fetch_rss_feeds task handles existing articles properly."""
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
        
        # Mock article_service
        mock_article_service = Mock()
        
        # Mock create_article_from_rss_entry
        new_article = Mock()
        new_article.id = 2
        mock_article_service.create_article_from_rss_entry.return_value = new_article
        
        # Patch the module-level CRUD and service
        with patch("local_newsifier.tasks._crud_article", mock_article_crud):
            with patch("local_newsifier.tasks._service_article", mock_article_service):
                # Mock process_article task
                with patch("local_newsifier.tasks.process_article") as mock_process:
                    mock_async_result = Mock(spec=AsyncResult)
                    mock_process.delay.return_value = mock_async_result
                    
                    # Call the task
                    result = fetch_rss_feeds(feed_urls)
                    
                    # Verify
                    assert mock_parse_rss.call_count == 1
                    assert mock_article_crud.get_by_url.call_count == 2
                    assert mock_article_service.create_article_from_rss_entry.call_count == 1
                    assert mock_process.delay.call_count == 1
                    
                    assert result["feeds_processed"] == 1
                    assert result["articles_found"] == 2
                    assert result["articles_added"] == 1

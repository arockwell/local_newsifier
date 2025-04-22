"""
Unit tests for Celery tasks in the Local Newsifier project.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, call

from celery import Task
from celery.result import AsyncResult

from local_newsifier.tasks import (
    analyze_entity_trends,
    fetch_rss_feeds,
    process_article,
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
        mock_session = Mock()
        mock_get_db = Mock(return_value=iter([mock_session]))
        monkeypatch.setattr("local_newsifier.tasks.get_db", mock_get_db)
        
        # Need to get a task instance to test
        task = process_article
        
        # Access the db property
        db = task._db
        assert db is mock_session
        
    def test_article_service_property(self):
        """Test that the article_service property returns an ArticleService instance."""
        # Need to get a task instance to test
        task = process_article
        
        # Access the article_service property
        service = task._article_service
        from local_newsifier.services.article_service import ArticleService
        assert isinstance(service, ArticleService)
        
    def test_article_crud_property(self, monkeypatch):
        """Test that the article_crud property returns an ArticleCRUD instance."""
        mock_db = Mock()
        mock_article_crud = Mock()
        
        # Mock the db property
        monkeypatch.setattr(Task, "_db", mock_db)
        
        # Mock the ArticleCRUD constructor
        def mock_init(self, db):
            self.db = db
            return None
            
        monkeypatch.setattr("local_newsifier.crud.article.ArticleCRUD.__init__", mock_init)
        
        # Need to get a task instance to test
        task = process_article
        
        # Access the article_crud property
        crud = task._article_crud
        assert crud is not None
        
    def test_entity_crud_property(self, monkeypatch):
        """Test that the entity_crud property returns an EntityCRUD instance."""
        mock_db = Mock()
        mock_entity_crud = Mock()
        
        # Mock the db property
        monkeypatch.setattr(Task, "_db", mock_db)
        
        # Mock the EntityCRUD constructor
        def mock_init(self, db):
            self.db = db
            return None
            
        monkeypatch.setattr("local_newsifier.crud.entity.EntityCRUD.__init__", mock_init)
        
        # Need to get a task instance to test
        task = process_article
        
        # Access the entity_crud property
        crud = task._entity_crud
        assert crud is not None


class TestProcessArticle:
    """Tests for the process_article task."""
    
    @patch("local_newsifier.tasks.process_article_flow")
    @patch("local_newsifier.tasks.process_entities_in_article")
    def test_process_article_success(
        self, mock_process_entities, mock_process_article_flow, 
        mock_article, mock_article_crud
    ):
        """Test that the process_article task processes an article successfully."""
        # Setup mocks
        mock_article_crud.get.return_value = mock_article
        mock_process_article_flow.return_value = {"status": "success"}
        mock_process_entities.return_value = {"entities": [{"id": 1, "name": "Test Entity"}]}
        
        # Mock the article_crud property
        with patch.object(process_article, "article_crud", mock_article_crud):
            # Call the task
            result = process_article(mock_article.id)
            
        # Verify
        mock_article_crud.get.assert_called_once_with(mock_article.id)
        mock_process_article_flow.assert_called_once_with(mock_article)
        mock_process_entities.assert_called_once_with(mock_article)
        
        assert result["article_id"] == mock_article.id
        assert result["status"] == "success"
        assert result["processed"] is True
        assert result["entities_found"] == 1
        assert result["article_title"] == mock_article.title
        
    def test_process_article_not_found(self, mock_article_crud):
        """Test that the process_article task handles a missing article properly."""
        # Setup mocks
        mock_article_crud.get.return_value = None
        
        # Mock the article_crud property
        with patch.object(process_article, "article_crud", mock_article_crud):
            # Call the task
            result = process_article(999)
            
        # Verify
        mock_article_crud.get.assert_called_once_with(999)
        assert result["article_id"] == 999
        assert result["status"] == "error"
        assert "Article not found" in result["message"]
        
    def test_process_article_error(self, mock_article, mock_article_crud):
        """Test that the process_article task handles errors properly."""
        # Setup mocks
        mock_article_crud.get.return_value = mock_article
        
        # Mock process_article_flow to raise an exception
        with patch("local_newsifier.tasks.process_article_flow") as mock_process:
            mock_process.side_effect = Exception("Test error")
            
            # Mock the article_crud property
            with patch.object(process_article, "article_crud", mock_article_crud):
                # Call the task
                result = process_article(mock_article.id)
                
        # Verify
        mock_article_crud.get.assert_called_once_with(mock_article.id)
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
        
        # Mock process_article task
        with patch("local_newsifier.tasks.process_article") as mock_process:
            mock_async_result = Mock(spec=AsyncResult)
            mock_process.delay.return_value = mock_async_result
            
            # Mock the article_crud and article_service properties
            with patch.object(fetch_rss_feeds, "article_crud", mock_article_crud):
                with patch.object(fetch_rss_feeds, "article_service", mock_article_service):
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
        
        # Mock process_article task
        with patch("local_newsifier.tasks.process_article") as mock_process:
            mock_async_result = Mock(spec=AsyncResult)
            mock_process.delay.return_value = mock_async_result
            
            # Mock the article_crud and article_service properties
            with patch.object(fetch_rss_feeds, "article_crud", mock_article_crud):
                with patch.object(fetch_rss_feeds, "article_service", mock_article_service):
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
        assert result["articles_updated"] == 1


class TestAnalyzeEntityTrends:
    """Tests for the analyze_entity_trends task."""
    
    @patch("local_newsifier.tasks.analyze_trends")
    def test_analyze_entity_trends_success(self, mock_analyze_trends):
        """Test that the analyze_entity_trends task analyzes trends successfully."""
        # Setup mocks
        mock_analyze_trends.return_value = {
            "entity_trends": [
                {
                    "entity_id": 1,
                    "entity_name": "Test Entity 1",
                    "entity_type": "PERSON",
                    "trend_direction": "up",
                    "trend_score": 0.75,
                    "mention_count": 10,
                    "average_sentiment": 0.5
                },
                {
                    "entity_id": 2,
                    "entity_name": "Test Entity 2",
                    "entity_type": "ORG",
                    "trend_direction": "down",
                    "trend_score": -0.5,
                    "mention_count": 5,
                    "average_sentiment": -0.2
                }
            ]
        }
        
        # Call the task
        result = analyze_entity_trends(time_interval="day", days_back=7)
        
        # Verify
        mock_analyze_trends.assert_called_once_with(
            time_interval="day", 
            days_back=7,
            entity_ids=None
        )
        
        assert result["status"] == "success"
        assert result["time_interval"] == "day"
        assert result["days_back"] == 7
        assert result["entities_analyzed"] == 2
        assert len(result["entity_trends"]) == 2
        
    @patch("local_newsifier.tasks.analyze_trends")
    def test_analyze_entity_trends_with_specific_entities(self, mock_analyze_trends):
        """Test that the analyze_entity_trends task handles specific entity IDs properly."""
        # Setup mocks
        entity_ids = [1, 3]
        mock_analyze_trends.return_value = {
            "entity_trends": [
                {
                    "entity_id": 1,
                    "entity_name": "Test Entity 1",
                    "entity_type": "PERSON",
                    "trend_direction": "up",
                    "trend_score": 0.75,
                    "mention_count": 10,
                    "average_sentiment": 0.5
                }
            ]
        }
        
        # Call the task
        result = analyze_entity_trends(
            time_interval="week", 
            days_back=14,
            entity_ids=entity_ids
        )
        
        # Verify
        mock_analyze_trends.assert_called_once_with(
            time_interval="week", 
            days_back=14,
            entity_ids=entity_ids
        )
        
        assert result["status"] == "success"
        assert result["time_interval"] == "week"
        assert result["days_back"] == 14
        assert result["entities_analyzed"] == 1
        
    @patch("local_newsifier.tasks.analyze_trends")
    def test_analyze_entity_trends_error(self, mock_analyze_trends):
        """Test that the analyze_entity_trends task handles errors properly."""
        # Setup mocks
        mock_analyze_trends.side_effect = Exception("Test error")
        
        # Call the task
        result = analyze_entity_trends(time_interval="day", days_back=7)
        
        # Verify
        mock_analyze_trends.assert_called_once_with(
            time_interval="day", 
            days_back=7,
            entity_ids=None
        )
        
        assert result["status"] == "error"
        assert result["time_interval"] == "day"
        assert result["days_back"] == 7
        assert "Test error" in result["message"]

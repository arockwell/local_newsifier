"""Tests for synchronous task implementations."""

from unittest.mock import Mock, patch

from local_newsifier.tasks_sync import (cleanup_old_articles_sync, fetch_rss_feeds_sync,
                                        process_article_sync, update_entity_profiles_sync)


class TestProcessArticleSync:
    """Test cases for process_article_sync function."""

    @patch("local_newsifier.tasks_sync.get_session")
    @patch("local_newsifier.tasks_sync.get_article_crud")
    @patch("local_newsifier.tasks_sync.get_news_pipeline_flow")
    @patch("local_newsifier.tasks_sync.get_entity_tracking_flow")
    def test_process_article_success(
        self, mock_entity_flow, mock_news_pipeline, mock_article_crud, mock_get_session
    ):
        """Test successful article processing."""
        # Setup mocks
        mock_session = Mock()
        mock_session.__enter__ = Mock(return_value=mock_session)
        mock_session.__exit__ = Mock(return_value=None)
        mock_get_session.return_value = iter([mock_session])

        mock_article = Mock(id=1, title="Test Article", url="https://example.com/article")
        mock_article_crud.return_value.get.return_value = mock_article

        mock_entity_flow.return_value.process_article.return_value = [
            {"name": "Entity1"},
            {"name": "Entity2"},
        ]

        # Execute
        result = process_article_sync(1)

        # Verify
        assert result["article_id"] == 1
        assert result["status"] == "success"
        assert result["processed"] is True
        assert result["entities_found"] == 2
        assert result["article_title"] == "Test Article"

        # Verify calls
        mock_article_crud.return_value.get.assert_called_once_with(mock_session, id=1)
        mock_news_pipeline.return_value.process_url_directly.assert_called_once_with(
            "https://example.com/article"
        )
        mock_entity_flow.return_value.process_article.assert_called_once_with(1)

    @patch("local_newsifier.tasks_sync.get_session")
    @patch("local_newsifier.tasks_sync.get_article_crud")
    def test_process_article_not_found(self, mock_article_crud, mock_get_session):
        """Test processing non-existent article."""
        # Setup mocks
        mock_session = Mock()
        mock_session.__enter__ = Mock(return_value=mock_session)
        mock_session.__exit__ = Mock(return_value=None)
        mock_get_session.return_value = iter([mock_session])

        mock_article_crud.return_value.get.return_value = None

        # Execute
        result = process_article_sync(999)

        # Verify
        assert result["article_id"] == 999
        assert result["status"] == "error"
        assert result["message"] == "Article not found"

    @patch("local_newsifier.tasks_sync.get_session")
    def test_process_article_exception(self, mock_get_session):
        """Test error handling during article processing."""
        # Setup mock to raise exception
        mock_get_session.side_effect = Exception("Database error")

        # Execute
        result = process_article_sync(1)

        # Verify
        assert result["article_id"] == 1
        assert result["status"] == "error"
        assert result["message"] == "Database error"
        assert result["processed"] is False


class TestFetchRSSFeedsSync:
    """Test cases for fetch_rss_feeds_sync function."""

    @patch("local_newsifier.tasks_sync.get_session")
    @patch("local_newsifier.tasks_sync.get_article_crud")
    @patch("local_newsifier.tasks_sync.get_article_service")
    @patch("local_newsifier.tasks_sync.parse_rss_feed")
    def test_fetch_rss_feeds_success(
        self, mock_parse_rss, mock_article_service, mock_article_crud, mock_get_session
    ):
        """Test successful RSS feed fetching."""
        # Setup mocks
        mock_session = Mock()
        mock_session.__enter__ = Mock(return_value=mock_session)
        mock_session.__exit__ = Mock(return_value=None)
        mock_get_session.return_value = iter([mock_session])

        mock_parse_rss.return_value = {
            "title": "Test Feed",
            "entries": [
                {"link": "https://example.com/article1", "title": "Article 1"},
                {"link": "https://example.com/article2", "title": "Article 2"},
            ],
        }

        mock_article_crud.return_value.get_by_url.return_value = None
        mock_article_service.return_value.create_article_from_rss_entry.side_effect = [1, 2]

        # Execute
        result = fetch_rss_feeds_sync(
            feed_urls=["https://example.com/feed.xml"], process_articles=False
        )

        # Verify
        assert result["status"] == "success"
        assert result["feeds_processed"] == 1
        assert result["articles_found"] == 2
        assert result["articles_added"] == 2
        assert len(result["feeds"]) == 1
        assert result["feeds"][0]["url"] == "https://example.com/feed.xml"
        assert result["feeds"][0]["articles_found"] == 2
        assert result["feeds"][0]["articles_added"] == 2

    @patch("local_newsifier.tasks_sync.parse_rss_feed")
    def test_fetch_rss_feeds_parse_error(self, mock_parse_rss):
        """Test handling of RSS parse errors."""
        # Setup mock to raise exception
        mock_parse_rss.side_effect = Exception("Parse error")

        # Execute
        result = fetch_rss_feeds_sync(feed_urls=["https://invalid.com/feed"])

        # Verify
        assert result["status"] == "error"
        assert "Parse error" in result["message"]


def test_cleanup_old_articles_sync():
    """Test cleanup_old_articles_sync placeholder."""
    result = cleanup_old_articles_sync(days=30)

    assert result["status"] == "success"
    assert result["articles_deleted"] == 0
    assert "not yet implemented" in result["message"]


def test_update_entity_profiles_sync():
    """Test update_entity_profiles_sync placeholder."""
    result = update_entity_profiles_sync()

    assert result["status"] == "success"
    assert result["profiles_updated"] == 0
    assert "not yet implemented" in result["message"]

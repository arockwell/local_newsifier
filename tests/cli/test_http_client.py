"""Tests for the NewsifierClient HTTP client."""

from unittest.mock import Mock, patch

import httpx
import pytest

from local_newsifier.cli.http_client import NewsifierAPIError, NewsifierClient


class TestNewsifierClient:
    """Test cases for NewsifierClient."""

    @pytest.fixture
    def client(self):
        """Create a test client."""
        return NewsifierClient(base_url="http://test.local")

    def test_client_initialization(self):
        """Test client initialization with different parameters."""
        # Default initialization
        client = NewsifierClient()
        assert client.base_url == "http://localhost:8000"
        assert client.timeout == 30.0
        assert client.local_mode is False

        # Custom initialization
        client = NewsifierClient(base_url="http://custom.local", timeout=60.0, local_mode=True)
        assert client.base_url == "http://custom.local"
        assert client.timeout == 60.0
        assert client.local_mode is True

    def test_context_manager(self, client):
        """Test context manager functionality."""
        with client as c:
            assert c._client is not None
            assert isinstance(c._client, httpx.Client)
        # Client should be closed after context
        assert c._client.is_closed

    @patch("httpx.Client.get")
    def test_get_db_stats(self, mock_get, client):
        """Test getting database statistics."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"articles": {"count": 100}, "rss_feeds": {"count": 10}}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        with client:
            stats = client.get_db_stats()

        assert stats["articles"]["count"] == 100
        assert stats["rss_feeds"]["count"] == 10
        mock_get.assert_called_once_with("/db/stats")

    @patch("httpx.Client.get")
    def test_api_error_handling(self, mock_get, client):
        """Test API error handling."""
        # Mock error response
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.json.return_value = {"detail": "Not found"}
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "404 Not Found", request=Mock(), response=mock_response
        )
        mock_get.return_value = mock_response

        with client:
            with pytest.raises(NewsifierAPIError) as exc_info:
                client.get_db_stats()

        assert exc_info.value.status_code == 404
        assert "Not found" in str(exc_info.value)

    @patch("httpx.Client.get")
    def test_list_articles_with_filters(self, mock_get, client):
        """Test listing articles with filters."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"id": 1, "title": "Article 1"},
            {"id": 2, "title": "Article 2"},
        ]
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        with client:
            articles = client.list_articles(source="rss", status="processed", limit=5)

        assert len(articles) == 2
        assert articles[0]["title"] == "Article 1"

        # Check that parameters were passed correctly
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert call_args[0][0] == "/db/articles"
        assert call_args[1]["params"]["source"] == "rss"
        assert call_args[1]["params"]["status"] == "processed"
        assert call_args[1]["params"]["limit"] == 5

    @patch("httpx.Client.post")
    def test_add_feed(self, mock_post, client):
        """Test adding a new RSS feed."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": 1,
            "name": "Test Feed",
            "url": "http://example.com/rss",
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        with client:
            feed = client.add_feed(url="http://example.com/rss", name="Test Feed")

        assert feed["id"] == 1
        assert feed["name"] == "Test Feed"

        # Check request
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[0][0] == "/feeds"
        assert call_args[1]["json"]["url"] == "http://example.com/rss"
        assert call_args[1]["json"]["name"] == "Test Feed"

    @patch("httpx.Client.delete")
    def test_delete_feed(self, mock_delete, client):
        """Test deleting a feed."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"message": "Feed deleted successfully"}
        mock_response.raise_for_status = Mock()
        mock_delete.return_value = mock_response

        with client:
            result = client.delete_feed(1)

        assert "Feed deleted successfully" in result["message"]
        mock_delete.assert_called_once_with("/feeds/1")

    @patch("httpx.Client.get")
    def test_health_check_connection_error(self, mock_get, client):
        """Test health check with connection error."""
        mock_get.side_effect = httpx.ConnectError("Connection refused")

        with client:
            with pytest.raises(NewsifierAPIError) as exc_info:
                client.health_check()

        assert exc_info.value.status_code == 503
        assert "Cannot connect" in str(exc_info.value)

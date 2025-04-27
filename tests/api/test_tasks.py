"""Tests for API tasks router."""
import json
from unittest.mock import MagicMock, Mock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlmodel import Session

from local_newsifier.api.dependencies import get_templates, get_session, get_article_service, get_rss_feed_service
from local_newsifier.api.routers.tasks import router
from local_newsifier.models.article import Article


@pytest.fixture
def app():
    """Create FastAPI app for testing."""
    app = FastAPI()
    app.include_router(router)
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_templates():
    """Mock templates."""
    mock = MagicMock()
    mock.TemplateResponse.return_value = "mocked template response"
    return mock


@pytest.fixture
def mock_settings():
    """Mock settings."""
    mock = MagicMock()
    mock.RSS_FEED_URLS = ["https://example.com/rss1", "https://example.com/rss2"]
    return mock


@pytest.fixture
def mock_celery_app():
    """Mock Celery app."""
    mock = MagicMock()
    mock.control = MagicMock()
    mock.control.revoke = MagicMock()
    return mock


@pytest.fixture
def mock_async_result():
    """Mock AsyncResult."""
    mock = MagicMock()
    return mock


@pytest.fixture
def mock_task():
    """Mock task object."""
    mock = MagicMock()
    mock.id = "test-task-id"
    mock.delay.return_value = mock
    return mock


@pytest.fixture
def mock_session():
    """Mock database session."""
    mock = MagicMock(spec=Session)
    return mock


@pytest.fixture
def mock_article_service():
    """Mock article service."""
    mock = MagicMock()
    return mock


@pytest.fixture
def mock_rss_feed_service():
    """Mock RSS feed service."""
    mock = MagicMock()
    return mock


@pytest.fixture
def sample_article():
    """Sample article fixture."""
    return Article(
        id=123,
        title="Test Article",
        content="This is a test article content",
        url="https://example.com/article",
    )


class TestTasksDashboard:
    """Tests for tasks dashboard endpoint."""

    @patch("local_newsifier.api.routers.tasks.settings", autospec=True)
    @patch("local_newsifier.api.routers.tasks.get_templates", return_value=None)
    def test_tasks_dashboard(self, mock_get_templates, mock_settings_module, client, mock_templates):
        """Test tasks dashboard returns template response."""
        # Set up the mock
        mock_settings_module.RSS_FEED_URLS = ["https://example.com/feed"]
        mock_get_templates.return_value = mock_templates

        # Register the dependency override
        client.app.dependency_overrides[get_templates] = lambda: mock_templates

        # Make the request
        response = client.get("/tasks/")

        # Verify response
        assert response.status_code == 200

        # Verify that the template was rendered with the correct context
        mock_templates.TemplateResponse.assert_called_once()
        template_name, context = mock_templates.TemplateResponse.call_args[0]
        assert template_name == "tasks_dashboard.html"
        assert context["title"] == "Task Dashboard"
        assert context["rss_feed_urls"] == mock_settings_module.RSS_FEED_URLS

        # Clean up
        client.app.dependency_overrides = {}


class TestProcessArticle:
    """Tests for process article endpoint."""

    @patch("local_newsifier.api.routers.tasks.process_article", autospec=True)
    def test_process_article_success(
        self, mock_process_article, client, mock_article_service, sample_article
    ):
        """Test successful article processing."""
        # Set up mocks
        mock_article_service.get_article.return_value = sample_article
        
        mock_task = MagicMock()
        mock_task.id = "test-task-id"
        mock_process_article.delay.return_value = mock_task

        # Register the dependency override
        client.app.dependency_overrides[get_article_service] = lambda: mock_article_service

        # Make the request
        article_id = 123
        response = client.post(f"/tasks/process-article/{article_id}")

        # Verify response
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["task_id"] == "test-task-id"
        assert response_data["article_id"] == article_id
        assert response_data["article_title"] == sample_article.title
        assert response_data["status"] == "queued"
        assert response_data["task_url"] == f"/tasks/status/test-task-id"

        # Verify mocks were called
        mock_article_service.get_article.assert_called_once_with(article_id)
        mock_process_article.delay.assert_called_once_with(article_id)

        # Clean up
        client.app.dependency_overrides = {}

    def test_process_article_not_found(self, client, mock_article_service):
        """Test article not found error."""
        # Set up mocks
        mock_article_service.get_article.return_value = None
        
        # Register the dependency override
        client.app.dependency_overrides[get_article_service] = lambda: mock_article_service

        # Make the request
        article_id = 999
        response = client.post(f"/tasks/process-article/{article_id}")

        # Verify response
        assert response.status_code == 404
        response_data = response.json()
        assert "not found" in response_data["detail"]

        # Clean up
        client.app.dependency_overrides = {}


class TestFetchRSSFeeds:
    """Tests for fetch RSS feeds endpoint."""

    @patch("local_newsifier.api.routers.tasks.fetch_rss_feeds", autospec=True)
    @patch("local_newsifier.api.routers.tasks.settings", autospec=True)
    def test_fetch_rss_feeds_with_default_urls(
        self, mock_settings, mock_fetch_rss_feeds, client, mock_rss_feed_service
    ):
        """Test fetching RSS feeds with default URLs from settings."""
        # Set up mocks
        mock_settings.RSS_FEED_URLS = ["https://example.com/rss1", "https://example.com/rss2"]
        
        mock_task = MagicMock()
        mock_task.id = "test-task-id"
        mock_fetch_rss_feeds.delay.return_value = mock_task

        # Register the dependency override
        client.app.dependency_overrides[get_rss_feed_service] = lambda: mock_rss_feed_service

        # Make the request
        response = client.post("/tasks/fetch-rss-feeds")

        # Verify response
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["task_id"] == "test-task-id"
        assert response_data["feed_count"] == len(mock_settings.RSS_FEED_URLS)
        assert response_data["status"] == "queued"
        assert response_data["task_url"] == f"/tasks/status/test-task-id"

        # Verify mocks were called
        mock_fetch_rss_feeds.delay.assert_called_once_with(mock_settings.RSS_FEED_URLS)

        # Clean up
        client.app.dependency_overrides = {}

    @patch("local_newsifier.api.routers.tasks.fetch_rss_feeds", autospec=True)
    def test_fetch_rss_feeds_with_custom_urls(
        self, mock_fetch_rss_feeds, client, mock_rss_feed_service
    ):
        """Test fetching RSS feeds with custom URLs."""
        # Set up mocks
        custom_urls = ["https://example.com/custom1", "https://example.com/custom2"]
        
        mock_task = MagicMock()
        mock_task.id = "test-task-id"
        mock_fetch_rss_feeds.delay.return_value = mock_task

        # Register the dependency override
        client.app.dependency_overrides[get_rss_feed_service] = lambda: mock_rss_feed_service

        # Make the request with query parameters
        url_params = "&".join([f"feed_urls={url}" for url in custom_urls])
        response = client.post(f"/tasks/fetch-rss-feeds?{url_params}")

        # Verify response
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["task_id"] == "test-task-id"
        assert response_data["feed_count"] == len(custom_urls)
        assert response_data["status"] == "queued"
        assert response_data["task_url"] == f"/tasks/status/test-task-id"

        # Verify mocks were called
        mock_fetch_rss_feeds.delay.assert_called_once_with(custom_urls)

        # Clean up
        client.app.dependency_overrides = {}

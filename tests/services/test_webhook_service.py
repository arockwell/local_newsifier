"""Test webhook service functionality."""

import datetime
import uuid
from unittest.mock import MagicMock, Mock, patch

import pytest
from sqlmodel import Session

from local_newsifier.models.apify import ApifyJob, ApifyDatasetItem
from local_newsifier.models.article import Article
from local_newsifier.models.webhook import (
    ApifyWebhookPayload, 
    ApifyDatasetTransformationConfig
)
from local_newsifier.services.webhook_service import ApifyWebhookHandler


@pytest.fixture
def mock_apify_service():
    """Mock the ApifyService."""
    mock = Mock()
    mock._test_mode = False
    return mock


@pytest.fixture
def mock_article_service():
    """Mock the ArticleService."""
    return Mock()


@pytest.fixture
def mock_session():
    """Mock a database session."""
    mock = Mock()
    # Setup session to be used as context manager
    mock.__enter__ = Mock(return_value=mock)
    mock.__exit__ = Mock(return_value=None)
    mock.add = Mock()
    mock.commit = Mock()
    mock.refresh = Mock()
    mock.exec = Mock()
    return mock


@pytest.fixture
def webhook_handler(mock_apify_service, mock_article_service, mock_session):
    """Create a webhook handler with mocked dependencies."""
    session_factory = lambda: mock_session
    
    return ApifyWebhookHandler(
        apify_service=mock_apify_service,
        article_service=mock_article_service,
        session_factory=session_factory,
        transformation_config=ApifyDatasetTransformationConfig()
    )


class TestApifyWebhookHandler:
    """Test suite for ApifyWebhookHandler."""

    def test_validate_webhook_with_valid_secret(self, webhook_handler, monkeypatch):
        """Test webhook validation with valid secret."""
        monkeypatch.setattr("local_newsifier.config.settings.settings.APIFY_WEBHOOK_SECRET", "test_secret")
        
        payload = ApifyWebhookPayload(
            createdAt=datetime.datetime.now(),
            eventType="ACTOR.RUN.SUCCEEDED",
            actorId="test_actor",
            actorRunId=str(uuid.uuid4()),
            userId="test_user",
            defaultKeyValueStoreId="test_kvs",
            defaultDatasetId="test_dataset",
            startedAt=datetime.datetime.now(),
            status="SUCCEEDED",
            webhookId=str(uuid.uuid4()),
            secret="test_secret"  # Correct secret
        )
        
        assert webhook_handler.validate_webhook(payload) is True

    def test_validate_webhook_with_invalid_secret(self, webhook_handler, monkeypatch):
        """Test webhook validation with invalid secret."""
        monkeypatch.setattr("local_newsifier.config.settings.settings.APIFY_WEBHOOK_SECRET", "test_secret")
        
        payload = ApifyWebhookPayload(
            createdAt=datetime.datetime.now(),
            eventType="ACTOR.RUN.SUCCEEDED",
            actorId="test_actor",
            actorRunId=str(uuid.uuid4()),
            userId="test_user",
            defaultKeyValueStoreId="test_kvs",
            defaultDatasetId="test_dataset",
            startedAt=datetime.datetime.now(),
            status="SUCCEEDED",
            webhookId=str(uuid.uuid4()),
            secret="wrong_secret"  # Wrong secret
        )
        
        assert webhook_handler.validate_webhook(payload) is False

    def test_handle_webhook_success(self, webhook_handler, mock_session):
        """Test successful webhook handling."""
        # Setup mock session to return no existing job
        mock_session.exec.return_value.first.return_value = None
        
        # Create new job with ID
        mock_new_job = MagicMock(spec=ApifyJob)
        mock_new_job.id = 123
        
        def mock_refresh(obj):
            """Mock session.refresh to set id."""
            obj.id = 123
        
        mock_session.refresh.side_effect = mock_refresh
        
        payload = ApifyWebhookPayload(
            createdAt=datetime.datetime.now(),
            eventType="ACTOR.RUN.SUCCEEDED",
            actorId="test_actor",
            actorRunId="test_run_id",
            userId="test_user",
            defaultKeyValueStoreId="test_kvs",
            defaultDatasetId="test_dataset",
            startedAt=datetime.datetime.now(),
            status="SUCCEEDED",
            webhookId="test_webhook_id"
        )
        
        success, job_id, message = webhook_handler.handle_webhook(payload)
        
        assert success is True
        assert job_id == 123
        assert "Successfully recorded job" in message
        assert mock_session.add.called
        assert mock_session.commit.called

    def test_transform_dataset_item_success(self, webhook_handler):
        """Test successful dataset item transformation."""
        item_data = {
            "url": "https://example.com/test-article",
            "title": "Test Article Title",
            "content": "This is the content of the test article. It should be long enough to pass the minimum length check.",
            "publishedAt": "2023-01-01T12:00:00Z",
            "source": "Example News"
        }
        
        success, article, error = webhook_handler.transform_dataset_item(item_data)
        
        assert success is True
        assert article is not None
        assert error is None
        assert article.url == "https://example.com/test-article"
        assert article.title == "Test Article Title"
        assert article.content == "This is the content of the test article. It should be long enough to pass the minimum length check."
        assert article.source == "Example News"
        assert article.published_at is not None

    def test_transform_dataset_item_missing_fields(self, webhook_handler):
        """Test dataset item transformation with missing fields."""
        # Missing title
        item_data = {
            "url": "https://example.com/test-article",
            "content": "Test content"
        }
        
        success, article, error = webhook_handler.transform_dataset_item(item_data)
        
        assert success is False
        assert article is None
        assert "Title field missing" in error

    @patch("local_newsifier.services.webhook_service.ApifyWebhookHandler.transform_dataset_item")
    def test_process_dataset(self, mock_transform, webhook_handler, mock_apify_service, mock_session):
        """Test dataset processing."""
        # Setup mock apify service to return dataset items
        mock_apify_service.get_dataset_items.return_value = {
            "items": [
                {"id": "1", "url": "https://example.com/1", "title": "Article 1", "content": "Content 1"},
                {"id": "2", "url": "https://example.com/2", "title": "Article 2", "content": "Content 2"}
            ]
        }
        
        # Setup mock to return successful transformations
        article1 = Article(id=101, url="https://example.com/1", title="Article 1", content="Content 1")
        article2 = Article(id=102, url="https://example.com/2", title="Article 2", content="Content 2")
        
        mock_transform.side_effect = [
            (True, article1, None),
            (True, article2, None)
        ]
        
        # Setup mock article service
        webhook_handler.article_service.get_by_url.return_value = None
        
        # Mock session get for dataset item
        mock_session.get.return_value = MagicMock(spec=ApifyDatasetItem)
        
        # Process dataset
        success, items_processed, articles_created, error = webhook_handler.process_dataset("test_dataset", 123)
        
        assert success is True
        assert items_processed == 2
        assert articles_created == 2
        assert error is None
        assert mock_apify_service.get_dataset_items.called
        assert mock_transform.call_count == 2
        assert webhook_handler.article_service.process_article.call_count == 2
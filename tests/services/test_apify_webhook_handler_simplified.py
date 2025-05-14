"""Tests for the ApifyWebhookHandler service."""

import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime, timezone
from typing import Dict, Any

from tests.fixtures.event_loop import event_loop_fixture
from tests.ci_skip_config import ci_skip_async
from local_newsifier.services.apify_webhook_handler import ApifyWebhookHandler
from local_newsifier.models.apify import ApifyJob, ApifyDatasetItem
from local_newsifier.models.article import Article


@ci_skip_async
class TestApifyWebhookHandler:
    """Test class for ApifyWebhookHandler with simplified scope."""

    @pytest.fixture
    def mock_apify_service(self):
        """Create a mock Apify service."""
        mock = MagicMock()
        # Mock the get_dataset_items method
        mock.get_dataset_items.return_value = {
            "items": [
                {
                    "id": "item1",
                    "url": "https://example.com/article1",
                    "title": "Test Article 1",
                    "content": "This is test content for article 1",
                    "publishedAt": "2023-01-01T12:00:00Z",
                    "source": "Example News"
                }
            ]
        }
        return mock

    @pytest.fixture
    def mock_article_service(self):
        """Create a mock Article service."""
        mock = MagicMock()
        # Mock the process_article method
        mock.process_article.return_value = None
        return mock

    @pytest.fixture
    def mock_session(self):
        """Create a mock database session."""
        session = MagicMock()
        
        # Mock the exec method to return expected query results
        session.exec.return_value.first.return_value = None  # Default: No existing job/item
        
        # Mock the add method
        session.add.return_value = None
        
        # Mock the commit method
        session.commit.return_value = None
        
        # Mock the refresh method to set IDs
        def mock_refresh(obj):
            if not hasattr(obj, 'id') or obj.id is None:
                if isinstance(obj, ApifyJob):
                    obj.id = 1
                elif isinstance(obj, ApifyDatasetItem):
                    obj.id = 1
                elif isinstance(obj, Article):
                    obj.id = 1
        session.refresh.side_effect = mock_refresh
        
        return session

    @pytest.fixture
    def mock_session_factory(self, mock_session):
        """Create a mock session factory that returns the mock session."""
        # Create a context manager that yields the mock session
        class MockSessionContext:
            def __enter__(self):
                return mock_session
                
            def __exit__(self, exc_type, exc_val, exc_tb):
                return False
        
        return lambda: MockSessionContext()

    @pytest.fixture
    def handler(self, mock_apify_service, mock_article_service, mock_session_factory):
        """Create an ApifyWebhookHandler instance with mocked dependencies."""
        return ApifyWebhookHandler(
            apify_service=mock_apify_service,
            article_service=mock_article_service,
            session_factory=mock_session_factory
        )

    @pytest.fixture
    def valid_webhook_data(self):
        """Valid webhook payload fixture."""
        return {
            "createdAt": "2023-05-14T10:00:00.000Z",
            "eventType": "RUN.SUCCEEDED",
            "userId": "test_user",
            "webhookId": "test_webhook_123",
            "actorId": "test_actor",
            "actorRunId": "test_run_123",
            "datasetId": "test_dataset_123"
        }

    def test_process_webhook_success(self, handler, valid_webhook_data, mock_session, mock_apify_service, event_loop_fixture):
        """Test successful webhook processing."""
        # Act
        result = event_loop_fixture.run_until_complete(handler.process_webhook(valid_webhook_data))
        
        # Assert
        assert result["status"] == "success"
        assert "job_id" in result
        assert "dataset_id" in result
        assert "processed_count" in result
        
        # Verify apify_service was called correctly
        mock_apify_service.get_dataset_items.assert_called_once_with("test_dataset_123")

    def test_process_webhook_skipped(self, handler, event_loop_fixture):
        """Test webhook processing skipped for non-succeeded events."""
        # Arrange
        webhook_data = {
            "eventType": "RUN.FAILED",
            "datasetId": "test_dataset_123"
        }
        
        # Act
        result = event_loop_fixture.run_until_complete(handler.process_webhook(webhook_data))
        
        # Assert
        assert result["status"] == "skipped"
        assert "Event type RUN.FAILED" in result["reason"]

    def test_process_webhook_missing_dataset(self, handler, event_loop_fixture):
        """Test webhook processing skipped when dataset ID is missing."""
        # Arrange
        webhook_data = {
            "eventType": "RUN.SUCCEEDED",
            # No datasetId
        }
        
        # Act
        result = event_loop_fixture.run_until_complete(handler.process_webhook(webhook_data))
        
        # Assert
        assert result["status"] == "skipped"
        assert "missing dataset id" in result["reason"].lower()

    def test_process_webhook_error(self, handler, valid_webhook_data, mock_apify_service, event_loop_fixture):
        """Test error handling during webhook processing."""
        # Arrange
        mock_apify_service.get_dataset_items.side_effect = Exception("API error")
        
        # Act
        result = event_loop_fixture.run_until_complete(handler.process_webhook(valid_webhook_data))
        
        # Assert
        assert result["status"] == "error"
        assert "API error" in result["error"]

    def test_create_or_update_job_new(self, handler, mock_session, event_loop_fixture):
        """Test creating a new job."""
        # Arrange
        mock_session.exec.return_value.first.return_value = None  # No existing job
        
        # Act
        job_id = event_loop_fixture.run_until_complete(handler._create_or_update_job("test_actor", "test_run", "test_dataset"))
        
        # Assert
        assert job_id == 1  # From the mock_refresh logic
        
        # Verify a new job was created and saved
        job = mock_session.add.call_args[0][0]
        assert isinstance(job, ApifyJob)
        assert job.actor_id == "test_actor"
        assert job.run_id == "test_run"
        assert job.dataset_id == "test_dataset"
        assert job.status == "SUCCEEDED"
"""Tests for the ApifyWebhookHandler service."""

import pytest
import json
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple

from tests.fixtures.event_loop import event_loop_fixture
from tests.ci_skip_config import ci_skip_async
from local_newsifier.services.apify_webhook_handler import ApifyWebhookHandler
from local_newsifier.models.apify import ApifyJob, ApifyDatasetItem
from local_newsifier.models.article import Article


@ci_skip_async
class TestApifyWebhookHandler:
    """Test class for ApifyWebhookHandler."""

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
                },
                {
                    "id": "item2",
                    "url": "https://example.com/article2",
                    "title": "Test Article 2",
                    "content": "This is test content for article 2",
                    "publishedAt": "2023-01-02T12:00:00Z",
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
        # Arrange - everything is set up in fixtures
        
        # Act
        result = event_loop_fixture.run_until_complete(handler.process_webhook(valid_webhook_data))
        
        # Assert
        assert result["status"] == "success"
        assert "job_id" in result
        assert "dataset_id" in result
        assert "processed_count" in result
        assert result["processed_count"] == 2  # Two items in the mock dataset
        
        # Verify apify_service was called correctly
        mock_apify_service.get_dataset_items.assert_called_once_with("test_dataset_123")
        
        # Verify session operations
        assert mock_session.add.call_count >= 3  # At least job, dataset items, and articles
        assert mock_session.commit.call_count >= 3
        assert mock_session.refresh.call_count >= 3

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
        assert mock_session.add.call_count == 1
        assert mock_session.commit.call_count == 1
        assert mock_session.refresh.call_count == 1
        
        # Verify the job properties
        job = mock_session.add.call_args[0][0]
        assert isinstance(job, ApifyJob)
        assert job.actor_id == "test_actor"
        assert job.run_id == "test_run"
        assert job.dataset_id == "test_dataset"
        assert job.status == "SUCCEEDED"

    def test_create_or_update_job_existing(self, handler, mock_session, event_loop_fixture):
        """Test updating an existing job."""
        # Arrange
        existing_job = ApifyJob(
            id=1,
            actor_id="old_actor",
            run_id="test_run",  # Same run_id for matching
            status="STARTED",
            dataset_id="old_dataset",
            started_at=datetime.now(timezone.utc)
        )
        mock_session.exec.return_value.first.return_value = existing_job
        
        # Act
        job_id = event_loop_fixture.run_until_complete(handler._create_or_update_job("test_actor", "test_run", "test_dataset"))
        
        # Assert
        assert job_id == 1  # The existing job ID
        
        # Verify the job was updated
        assert existing_job.status == "SUCCEEDED"
        assert existing_job.dataset_id == "test_dataset"
        assert existing_job.finished_at is not None
        
        # Verify session operations
        assert mock_session.add.call_count == 1
        assert mock_session.commit.call_count == 1
        assert mock_session.refresh.call_count == 1

    @pytest.mark.asyncio
    async def test_process_dataset_items(self, handler, mock_session, mock_apify_service, mock_article_service):
        """Test processing dataset items."""
        # Act
        processed_items = await handler._process_dataset_items("test_dataset", 1)
        
        # Assert
        assert len(processed_items) == 2  # Two items in the mock dataset
        
        # Verify each item was processed and stored
        for item_result in processed_items:
            assert isinstance(item_result, tuple)
            assert len(item_result) == 2
            assert item_result[0] == 1  # Dataset item ID from mock
            assert item_result[1] == 1  # Article ID from mock
        
        # Verify article service was called
        assert mock_article_service.process_article.call_count == 2
        
        # Verify dataset items were created
        dataset_item_calls = [call for call in mock_session.add.call_args_list 
                             if isinstance(call[0][0], ApifyDatasetItem)]
        assert len(dataset_item_calls) == 2

    @pytest.mark.asyncio
    async def test_process_dataset_items_error(self, handler, mock_session, mock_apify_service):
        """Test error handling during dataset item processing."""
        # Arrange
        # Simulate an error when processing the second item
        original_side_effect = mock_session.refresh.side_effect
        call_count = 0
        
        def raise_on_second_item(obj):
            nonlocal call_count
            if isinstance(obj, ApifyDatasetItem):
                call_count += 1
                if call_count == 2:
                    raise Exception("Error processing item")
            return original_side_effect(obj)
            
        mock_session.refresh.side_effect = raise_on_second_item
        
        # Act
        processed_items = await handler._process_dataset_items("test_dataset", 1)
        
        # Assert
        # Should have two items, but one with error (None for article_id)
        assert len(processed_items) == 2
        # The first item should be processed successfully
        assert processed_items[0] == (1, 1)
        # The second item should have an error (0 is the default ID for error case)
        assert processed_items[1] == (0, None)

    @pytest.mark.asyncio
    async def test_transform_to_article(self, handler, mock_session):
        """Test transforming dataset item to article."""
        # Arrange
        item = {
            "url": "https://example.com/article",
            "title": "Test Article",
            "content": "This is test content",
            "publishedAt": "2023-01-01T12:00:00Z",
            "source": "Example News"
        }
        
        # Act
        article_id = await handler._transform_to_article(item, 1, mock_session)
        
        # Assert
        assert article_id == 1  # From mock
        
        # Verify article was created correctly
        article = mock_session.add.call_args[0][0]
        assert isinstance(article, Article)
        assert article.url == "https://example.com/article"
        assert article.title == "Test Article"
        assert article.content == "This is test content"
        assert article.source == "Example News"
        assert article.apify_dataset_item_id == 1

    @pytest.mark.asyncio
    async def test_transform_to_article_missing_url(self, handler, mock_session):
        """Test handling missing URL in dataset item."""
        # Arrange
        item = {
            "title": "Test Article",
            "content": "This is test content"
        }
        
        # Act
        article_id = await handler._transform_to_article(item, 1, mock_session)
        
        # Assert
        assert article_id is None  # Should return None when URL is missing
        assert mock_session.add.call_count == 0  # No article should be created

    @pytest.mark.asyncio
    async def test_transform_to_article_missing_title(self, handler, mock_session):
        """Test handling missing title in dataset item."""
        # Arrange
        item = {
            "url": "https://example.com/article",
            "content": "This is test content",
            "pageTitle": "Page Title"  # Fallback title
        }
        
        # Act
        article_id = await handler._transform_to_article(item, 1, mock_session)
        
        # Assert
        assert article_id == 1  # From mock
        
        # Verify article was created with fallback title
        article = mock_session.add.call_args[0][0]
        assert article.title == "Page Title"

    @pytest.mark.asyncio
    async def test_transform_to_article_missing_content(self, handler, mock_session):
        """Test handling missing content in dataset item."""
        # Arrange
        item = {
            "url": "https://example.com/article",
            "title": "Test Article",
            # Missing content, should try alternative fields
            "text": "This is alternative text content"
        }
        
        # Act
        article_id = await handler._transform_to_article(item, 1, mock_session)
        
        # Assert
        assert article_id == 1  # From mock
        
        # Verify article was created with alternative content field
        article = mock_session.add.call_args[0][0]
        assert article.content == "This is alternative text content"

    @pytest.mark.asyncio
    async def test_transform_to_article_all_content_fields(self, handler, mock_session):
        """Test content field priority in dataset item."""
        # Arrange
        item = {
            "url": "https://example.com/article",
            "title": "Test Article",
            "content": "Primary content",
            "text": "Secondary content",
            "articleBody": "Tertiary content",
            "description": "Fallback content"
        }
        
        # Act
        article_id = await handler._transform_to_article(item, 1, mock_session)
        
        # Assert
        article = mock_session.add.call_args[0][0]
        assert article.content == "Primary content"  # Should use primary field

    @pytest.mark.asyncio
    async def test_transform_to_article_date_parsing(self, handler, mock_session):
        """Test date parsing in dataset item."""
        # Arrange
        item = {
            "url": "https://example.com/article",
            "title": "Test Article",
            "content": "Test content",
            "datePublished": "2023-01-01T12:00:00Z"
        }
        
        # Act
        article_id = await handler._transform_to_article(item, 1, mock_session)
        
        # Assert
        article = mock_session.add.call_args[0][0]
        assert article.published_at is not None
        assert article.published_at.year == 2023
        assert article.published_at.month == 1
        assert article.published_at.day == 1

    @pytest.mark.asyncio
    async def test_transform_to_article_date_parsing_error(self, handler, mock_session):
        """Test handling invalid date in dataset item."""
        # Arrange
        item = {
            "url": "https://example.com/article",
            "title": "Test Article",
            "content": "Test content",
            "publishedAt": "invalid-date-format"
        }
        
        # Act
        with patch('local_newsifier.services.apify_webhook_handler.logger') as mock_logger:
            article_id = await handler._transform_to_article(item, 1, mock_session)
        
        # Assert
        article = mock_session.add.call_args[0][0]
        assert article.published_at is not None  # Should use current date as fallback
        mock_logger.warning.assert_called_once()  # Should log a warning

    @pytest.mark.asyncio
    async def test_transform_to_article_source_from_url(self, handler, mock_session):
        """Test extracting source from URL when not provided."""
        # Arrange
        item = {
            "url": "https://example-news.com/article",
            "title": "Test Article",
            "content": "Test content"
        }
        
        # Act
        article_id = await handler._transform_to_article(item, 1, mock_session)
        
        # Assert
        article = mock_session.add.call_args[0][0]
        assert article.source == "example-news.com"  # Extracted from URL

    @pytest.mark.asyncio
    async def test_transform_to_article_error(self, handler, mock_session):
        """Test error handling during article transformation."""
        # Arrange
        item = {
            "url": "https://example.com/article",
            "title": "Test Article",
            "content": "Test content"
        }
        
        # Make session.add raise an exception
        mock_session.add.side_effect = Exception("Database error")
        
        # Act
        with patch('local_newsifier.services.apify_webhook_handler.logger') as mock_logger:
            article_id = await handler._transform_to_article(item, 1, mock_session)
        
        # Assert
        assert article_id is None  # Should return None on error
        mock_logger.exception.assert_called_once()  # Should log an exception

    @pytest.mark.asyncio
    async def test_update_job_processing_status(self, handler, mock_session):
        """Test updating job processing status."""
        # Arrange
        job = ApifyJob(
            id=1,
            actor_id="test_actor",
            run_id="test_run",
            status="SUCCEEDED",
            dataset_id="test_dataset",
            started_at=datetime.now(timezone.utc),
            finished_at=datetime.now(timezone.utc),
            processed=False
        )
        mock_session.exec.return_value.first.return_value = job
        
        processed_items = [(1, 1), (2, 2), (3, None)]
        
        # Act
        await handler._update_job_processing_status(1, processed_items)
        
        # Assert
        assert job.processed is True
        assert job.processed_at is not None
        assert job.item_count == 3
        assert job.articles_created == 2  # Only two items with article IDs
        
        # Verify session operations
        assert mock_session.add.call_count == 1
        assert mock_session.commit.call_count == 1

    @pytest.mark.asyncio
    async def test_update_job_processing_status_not_found(self, handler, mock_session):
        """Test handling job not found when updating status."""
        # Arrange
        mock_session.exec.return_value.first.return_value = None  # Job not found
        
        # Act
        with patch('local_newsifier.services.apify_webhook_handler.logger') as mock_logger:
            await handler._update_job_processing_status(999, [(1, 1)])
        
        # Assert
        mock_logger.error.assert_called_once()  # Should log an error
        assert "not found" in mock_logger.error.call_args[0][0]
        
        # Verify no session operations
        assert mock_session.add.call_count == 0
        assert mock_session.commit.call_count == 0
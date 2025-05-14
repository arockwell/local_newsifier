"""Integration tests for ApifyWebhookHandler with database operations."""

import pytest
import json
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple

from tests.fixtures.event_loop import event_loop_fixture
from tests.ci_skip_config import ci_skip_async

from local_newsifier.services.apify_webhook_handler import ApifyWebhookHandler
from local_newsifier.services.apify_service import ApifyService
from local_newsifier.services.article_service import ArticleService
from local_newsifier.models.apify import ApifyJob, ApifyDatasetItem
from local_newsifier.models.article import Article
from local_newsifier.models.base import SQLModel
from sqlmodel import Session, select


@ci_skip_async
class TestApifyWebhookHandlerIntegration:
    """Integration tests for ApifyWebhookHandler using an in-memory database."""

    @pytest.fixture
    def mock_apify_service(self):
        """Create a mock Apify service with realistic responses."""
        mock = MagicMock(spec=ApifyService)
        
        # Mock dataset items with realistic structure
        mock.get_dataset_items.return_value = {
            "items": [
                {
                    "id": "item1",
                    "url": "https://example.com/article1",
                    "title": "Test Article 1",
                    "content": "This is test content for article 1",
                    "publishedAt": datetime.now(timezone.utc).isoformat(),
                    "source": "Example News"
                },
                {
                    "id": "item2",
                    "url": "https://example.com/article2",
                    "title": "Test Article 2",
                    "content": "This is test content for article 2",
                    "publishedAt": (datetime.now(timezone.utc) - timedelta(days=1)).isoformat(),
                    "source": "Example News"
                }
            ]
        }
        return mock

    @pytest.fixture
    def mock_article_service(self):
        """Create a mock Article service."""
        mock = MagicMock(spec=ArticleService)
        mock.process_article.return_value = None
        return mock

    @pytest.fixture
    def in_memory_db(self):
        """Create an in-memory SQLite database for testing."""
        from sqlalchemy import create_engine
        from sqlalchemy.pool import StaticPool
        
        # Create in-memory database
        engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool
        )
        
        # Create tables
        SQLModel.metadata.create_all(engine)
        
        # Create session factory
        def get_session():
            with Session(engine) as session:
                yield session
        
        # Return session factory
        return get_session

    @pytest.fixture
    def handler(self, mock_apify_service, mock_article_service, in_memory_db):
        """Create an ApifyWebhookHandler with the in-memory database."""
        # Get a session from the factory
        session = next(in_memory_db())
        
        # Create session factory that reuses the same session
        def session_factory():
            class SessionContext:
                def __enter__(self):
                    return session
                def __exit__(self, exc_type, exc_val, exc_tb):
                    if exc_type:
                        session.rollback()
                    else:
                        session.commit()
                    return False
            return SessionContext()
        
        # Create the handler
        return ApifyWebhookHandler(
            apify_service=mock_apify_service,
            article_service=mock_article_service,
            session_factory=session_factory
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

    @pytest.mark.asyncio
    async def test_end_to_end_webhook_processing(
        self, handler, valid_webhook_data, mock_apify_service, event_loop_fixture
    ):
        """Test end-to-end webhook processing flow."""
        # Process webhook
        result = await handler.process_webhook(valid_webhook_data)
        
        # Verify success
        assert result["status"] == "success"
        assert "job_id" in result
        assert "dataset_id" in result
        assert "processed_count" in result
        assert result["processed_count"] == 2  # Two items in the mock dataset
        
        # Get session
        with handler.session_factory() as session:
            # Verify job record was created
            job_statement = select(ApifyJob).where(
                ApifyJob.actor_id == "test_actor",
                ApifyJob.run_id == "test_run_123"
            )
            job = session.exec(job_statement).first()
            
            assert job is not None
            assert job.dataset_id == "test_dataset_123"
            assert job.status == "SUCCEEDED"
            assert job.processed is True
            assert job.item_count == 2
            assert job.articles_created == 2
            
            # Verify dataset items were created
            items_statement = select(ApifyDatasetItem).where(
                ApifyDatasetItem.job_id == job.id
            )
            items = session.exec(items_statement).all()
            
            assert len(items) == 2
            for item in items:
                assert item.transformed is True
                assert item.article_id is not None
                
            # Verify articles were created
            article_statement = select(Article).where(
                Article.apify_dataset_item_id.in_([item.id for item in items])
            )
            articles = session.exec(article_statement).all()
            
            assert len(articles) == 2
            for article in articles:
                assert article.title.startswith("Test Article")
                assert article.content.startswith("This is test content")
                assert article.url.startswith("https://example.com/article")
                assert article.source == "Example News"

    @pytest.mark.asyncio
    async def test_idempotent_processing(
        self, handler, valid_webhook_data, mock_apify_service, event_loop_fixture
    ):
        """Test idempotent webhook processing (calling twice with same webhook)."""
        # Process webhook first time
        first_result = await handler.process_webhook(valid_webhook_data)
        
        # Get the job ID
        first_job_id = first_result["job_id"]
        
        # Process same webhook again
        second_result = await handler.process_webhook(valid_webhook_data)
        
        # Verify second result
        assert second_result["status"] == "success"
        assert second_result["job_id"] == first_job_id  # Should be same job ID
        
        # Get session
        with handler.session_factory() as session:
            # Verify only one job exists
            job_statement = select(ApifyJob).where(
                ApifyJob.actor_id == "test_actor",
                ApifyJob.run_id == "test_run_123"
            )
            jobs = session.exec(job_statement).all()
            
            assert len(jobs) == 1  # Should only have one job
            
            # Verify dataset items
            items_statement = select(ApifyDatasetItem).where(
                ApifyDatasetItem.job_id == jobs[0].id
            )
            items = session.exec(items_statement).all()
            
            # Should have 4 items (2 from each processing)
            assert len(items) == 4
            
            # Verify articles (should be deduped by URL)
            article_statement = select(Article)
            articles = session.exec(article_statement).all()
            
            # Should have 2 articles (deduped by URL uniqueness)
            assert len(articles) == 2

    @pytest.mark.asyncio
    async def test_error_recovery(
        self, handler, valid_webhook_data, mock_apify_service, event_loop_fixture
    ):
        """Test recovery from errors during processing."""
        # Make the first attempt fail
        mock_apify_service.get_dataset_items.side_effect = Exception("API error")
        
        # Process webhook - should fail
        result = await handler.process_webhook(valid_webhook_data)
        
        # Verify error result
        assert result["status"] == "error"
        assert "API error" in result["error"]
        
        # Fix the error for second attempt
        mock_apify_service.get_dataset_items.side_effect = None
        
        # Process webhook again - should succeed
        retry_result = await handler.process_webhook(valid_webhook_data)
        
        # Verify success
        assert retry_result["status"] == "success"
        
        # Verify database state
        with handler.session_factory() as session:
            # Should have one job
            job_statement = select(ApifyJob).where(
                ApifyJob.actor_id == "test_actor",
                ApifyJob.run_id == "test_run_123"
            )
            jobs = session.exec(job_statement).all()
            
            assert len(jobs) == 1
            assert jobs[0].processed is True  # Successfully processed
            
            # Should have dataset items
            items_statement = select(ApifyDatasetItem).where(
                ApifyDatasetItem.job_id == jobs[0].id
            )
            items = session.exec(items_statement).all()
            
            assert len(items) == 2
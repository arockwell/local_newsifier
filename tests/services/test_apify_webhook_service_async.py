"""Tests for the async Apify webhook service."""

import hashlib
import hmac
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from local_newsifier.models.apify import ApifyWebhookRaw
from local_newsifier.models.article import Article
from local_newsifier.services.apify_webhook_service_async import ApifyWebhookServiceAsync


@pytest_asyncio.fixture
async def async_memory_session():
    """Create an in-memory async SQLite session for testing."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with AsyncSessionLocal() as session:
        yield session

    await engine.dispose()


@pytest.mark.asyncio
class TestApifyWebhookServiceAsync:
    """Test the async Apify webhook service."""

    async def test_validate_signature_no_secret(self, async_memory_session):
        """Test signature validation when no secret is configured."""
        service = ApifyWebhookServiceAsync(async_memory_session, webhook_secret=None)

        # Should always return True when no secret
        assert service.validate_signature("payload", "signature") is True

    async def test_validate_signature_valid(self, async_memory_session):
        """Test signature validation with valid signature."""
        secret = "test_secret"
        payload = '{"test": "payload"}'

        # Calculate expected signature
        expected_sig = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()

        service = ApifyWebhookServiceAsync(async_memory_session, webhook_secret=secret)
        assert service.validate_signature(payload, expected_sig) is True

    async def test_validate_signature_invalid(self, async_memory_session):
        """Test signature validation with invalid signature."""
        service = ApifyWebhookServiceAsync(async_memory_session, webhook_secret="test_secret")
        assert service.validate_signature("payload", "wrong_signature") is False

    async def test_handle_webhook_invalid_signature(self, async_memory_session):
        """Test webhook handling with invalid signature."""
        service = ApifyWebhookServiceAsync(async_memory_session, webhook_secret="test_secret")

        # Mock the apify service close method
        service.apify_service.close = AsyncMock()

        payload = {"actorRunId": "run123", "actorId": "actor123", "status": "SUCCEEDED"}
        result = await service.handle_webhook(payload, json.dumps(payload), "wrong_sig")

        assert result["status"] == "error"
        assert result["message"] == "Invalid signature"

    async def test_handle_webhook_missing_fields(self, async_memory_session):
        """Test webhook handling with missing required fields."""
        service = ApifyWebhookServiceAsync(async_memory_session)

        # Mock the apify service close method
        service.apify_service.close = AsyncMock()

        payload = {"actorId": "actor123"}  # Missing run_id and status
        result = await service.handle_webhook(payload, json.dumps(payload))

        assert result["status"] == "error"
        assert result["message"] == "Missing required fields"

    async def test_handle_webhook_duplicate(self, async_memory_session):
        """Test webhook handling with duplicate run_id."""
        service = ApifyWebhookServiceAsync(async_memory_session)

        # Mock the apify service close method
        service.apify_service.close = AsyncMock()

        # Create existing webhook
        existing = ApifyWebhookRaw(
            run_id="run123", actor_id="actor123", status="SUCCEEDED", data={}
        )
        async_memory_session.add(existing)
        await async_memory_session.commit()

        # Try to process duplicate
        payload = {"actorRunId": "run123", "actorId": "actor123", "status": "SUCCEEDED"}
        result = await service.handle_webhook(payload, json.dumps(payload))

        assert result["status"] == "ok"
        assert result["message"] == "Duplicate webhook ignored"

    async def test_handle_webhook_save_raw_data(self, async_memory_session):
        """Test that webhook raw data is saved correctly."""
        service = ApifyWebhookServiceAsync(async_memory_session)

        # Mock the apify service close method
        service.apify_service.close = AsyncMock()

        payload = {
            "actorRunId": "run123",
            "actorId": "actor123",
            "status": "FAILED",
            "extra": "data",
        }

        result = await service.handle_webhook(payload, json.dumps(payload))

        # Check webhook was saved
        stmt = select(ApifyWebhookRaw).where(ApifyWebhookRaw.run_id == "run123")
        result_query = await async_memory_session.execute(stmt)
        webhook = result_query.scalar_one_or_none()

        assert webhook is not None
        assert webhook.run_id == "run123"
        assert webhook.actor_id == "actor123"
        assert webhook.status == "FAILED"
        assert webhook.data == payload

        assert result["status"] == "ok"
        assert result["articles_created"] == 0

    @patch("local_newsifier.services.apify_webhook_service_async.ApifyServiceAsync")
    async def test_handle_webhook_create_articles_success(
        self, mock_apify_class, async_memory_session
    ):
        """Test successful article creation from webhook."""
        # Setup mock Apify client
        mock_apify_instance = AsyncMock()
        mock_apify_class.return_value = mock_apify_instance

        mock_dataset_client = MagicMock()
        mock_items_result = MagicMock()
        mock_items_result.items = [
            {
                "url": "https://example.com/article1",
                "title": "Test Article 1",
                "content": "This is test article content that is long enough to be valid. " * 10,
                "source": "test",
            },
            {
                "url": "https://example.com/article2",
                "title": "Test Article 2",
                "content": "Another test article with sufficient content. " * 10,
            },
        ]

        # Make list_items async
        mock_dataset_client.list_items = AsyncMock(return_value=mock_items_result)
        mock_apify_instance.client.dataset = MagicMock(return_value=mock_dataset_client)
        mock_apify_instance.close = AsyncMock()

        service = ApifyWebhookServiceAsync(async_memory_session)

        payload = {
            "actorRunId": "run123",
            "actorId": "actor123",
            "status": "SUCCEEDED",
            "defaultDatasetId": "dataset123",
        }

        result = await service.handle_webhook(payload, json.dumps(payload))

        # Check articles were created
        stmt = select(Article)
        result_query = await async_memory_session.execute(stmt)
        articles = result_query.scalars().all()

        assert len(articles) == 2
        assert articles[0].url == "https://example.com/article1"
        assert articles[1].url == "https://example.com/article2"

        assert result["status"] == "ok"
        assert result["articles_created"] == 2

    @patch("local_newsifier.services.apify_webhook_service_async.ApifyServiceAsync")
    async def test_handle_webhook_create_articles_error(
        self, mock_apify_class, async_memory_session
    ):
        """Test article creation error handling."""
        # Setup mock to raise error
        mock_apify_instance = AsyncMock()
        mock_apify_class.return_value = mock_apify_instance

        mock_dataset_client = MagicMock()
        mock_dataset_client.list_items = AsyncMock(side_effect=Exception("API Error"))
        mock_apify_instance.client.dataset.return_value = mock_dataset_client
        mock_apify_instance.close = AsyncMock()

        service = ApifyWebhookServiceAsync(async_memory_session)

        payload = {
            "actorRunId": "run123",
            "actorId": "actor123",
            "status": "SUCCEEDED",
            "defaultDatasetId": "dataset123",
        }

        # Should not raise, just log error
        result = await service.handle_webhook(payload, json.dumps(payload))

        # Webhook should still be saved
        stmt = select(ApifyWebhookRaw).where(ApifyWebhookRaw.run_id == "run123")
        result_query = await async_memory_session.execute(stmt)
        webhook = result_query.scalar_one_or_none()

        assert webhook is not None
        assert result["status"] == "ok"
        assert result["articles_created"] == 0

"""Tests for the minimal Apify webhook service."""

import hashlib
import hmac
import json
from unittest.mock import MagicMock, patch

import pytest
from sqlmodel import Session, create_engine, select
from sqlmodel.pool import StaticPool

from local_newsifier.models import SQLModel
from local_newsifier.models.apify import ApifyWebhookRaw
from local_newsifier.models.article import Article
from local_newsifier.services.apify_webhook_service import ApifyWebhookService


@pytest.fixture
def memory_session():
    """Create an in-memory SQLite session for testing."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        yield session


class TestApifyWebhookService:
    """Test the minimal Apify webhook service."""

    def test_validate_signature_no_secret(self, memory_session):
        """Test signature validation when no secret is configured."""
        service = ApifyWebhookService(memory_session, webhook_secret=None)

        # Should always return True when no secret
        assert service.validate_signature("payload", "signature") is True

    def test_validate_signature_valid(self, memory_session):
        """Test signature validation with valid signature."""
        secret = "test_secret"
        payload = '{"test": "payload"}'

        # Calculate expected signature
        expected_sig = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()

        service = ApifyWebhookService(memory_session, webhook_secret=secret)
        assert service.validate_signature(payload, expected_sig) is True

    def test_validate_signature_invalid(self, memory_session):
        """Test signature validation with invalid signature."""
        service = ApifyWebhookService(memory_session, webhook_secret="test_secret")
        assert service.validate_signature("payload", "wrong_signature") is False

    def test_handle_webhook_invalid_signature(self, memory_session):
        """Test webhook handling with invalid signature."""
        service = ApifyWebhookService(memory_session, webhook_secret="test_secret")

        payload = {"actorRunId": "run123", "actorId": "actor123", "status": "SUCCEEDED"}
        result = service.handle_webhook(payload, json.dumps(payload), "wrong_sig")

        assert result["status"] == "error"
        assert result["message"] == "Invalid signature"

    def test_handle_webhook_missing_fields(self, memory_session):
        """Test webhook handling with missing required fields."""
        service = ApifyWebhookService(memory_session)

        # Nested structure missing required fields
        payload = {
            "eventData": {"actorId": "actor123"},  # Missing actorRunId
            "resource": {},  # Missing status
        }
        result = service.handle_webhook(payload, json.dumps(payload))

        assert result["status"] == "error"
        assert "Missing required field" in result["message"]

    def test_handle_webhook_duplicate(self, memory_session):
        """Test webhook handling with duplicate run_id."""
        service = ApifyWebhookService(memory_session)

        # Create existing webhook
        existing = ApifyWebhookRaw(
            run_id="run123", actor_id="actor123", status="SUCCEEDED", data={}
        )
        memory_session.add(existing)
        memory_session.commit()

        # Try to process duplicate with resource structure
        payload = {"resource": {"id": "run123", "actId": "actor123", "status": "SUCCEEDED"}}
        result = service.handle_webhook(payload, json.dumps(payload))

        assert result["status"] == "ok"
        assert result["message"] == "Duplicate webhook ignored"

    def test_handle_webhook_save_raw_data(self, memory_session):
        """Test that webhook raw data is saved correctly."""
        service = ApifyWebhookService(memory_session)

        # Resource structure payload
        payload = {
            "resource": {
                "id": "run123",
                "actId": "actor123",
                "status": "FAILED",
                "defaultDatasetId": "dataset123",
            },
            "extra": "data",
        }

        result = service.handle_webhook(payload, json.dumps(payload))

        assert result["status"] == "ok"
        assert result["run_id"] == "run123"
        assert result["articles_created"] == 0

        # Check database
        webhook = memory_session.exec(
            select(ApifyWebhookRaw).where(ApifyWebhookRaw.run_id == "run123")
        ).first()

        assert webhook is not None
        assert webhook.actor_id == "actor123"
        assert webhook.status == "FAILED"
        assert webhook.data == payload

    @patch("local_newsifier.services.apify_webhook_service.ApifyService")
    def test_handle_webhook_create_articles_success(self, mock_apify_class, memory_session):
        """Test successful article creation from webhook."""
        # Mock Apify client
        mock_apify = MagicMock()
        mock_apify_class.return_value = mock_apify

        # Mock dataset items
        mock_items = MagicMock()
        mock_items.items = [
            {
                "url": "https://example.com/article1",
                "title": "Test Article 1",
                "content": (
                    "This is a test article with enough content to pass the minimum "
                    "length requirement of 500 characters. " * 10
                ),
                "source": "example.com",
            },
            {
                "url": "https://example.com/article2",
                "title": "Test Article 2",
                "text": "Another test article using text field instead of content field. " * 10,
            },
        ]
        mock_apify.client.dataset.return_value.list_items.return_value = mock_items

        service = ApifyWebhookService(memory_session)

        # Use resource structure as expected by the service
        payload = {
            "resource": {
                "id": "run123",
                "actId": "actor123",
                "status": "SUCCEEDED",
                "defaultDatasetId": "dataset123",
            }
        }

        result = service.handle_webhook(payload, json.dumps(payload))

        assert result["status"] == "ok"
        assert result["articles_created"] == 2

        # Check articles were created
        articles = memory_session.exec(select(Article)).all()
        assert len(articles) == 2
        assert articles[0].url == "https://example.com/article1"
        assert articles[1].url == "https://example.com/article2"

    @patch("local_newsifier.services.apify_webhook_service.ApifyService")
    def test_handle_webhook_skip_invalid_articles(self, mock_apify_class, memory_session):
        """Test that invalid articles are skipped."""
        # Mock Apify client
        mock_apify = MagicMock()
        mock_apify_class.return_value = mock_apify

        # Mock dataset items with some invalid entries
        mock_items = MagicMock()
        mock_items.items = [
            {
                # Missing URL
                "title": "No URL Article",
                "content": "Content without URL",
            },
            {
                # Missing title
                "url": "https://example.com/no-title",
                "content": "Content without title",
            },
            {
                # Content too short (less than 500 chars)
                "url": "https://example.com/short",
                "title": "Short Content",
                "content": "Too short",
            },
            {
                # Valid article (needs 500+ chars)
                "url": "https://example.com/valid",
                "title": "Valid Article",
                "content": (
                    "This is a valid article with enough content to meet the new "
                    "minimum requirement. " * 10
                ),
            },
        ]
        mock_apify.client.dataset.return_value.list_items.return_value = mock_items

        service = ApifyWebhookService(memory_session)

        # Use resource structure as expected by the service
        payload = {
            "resource": {
                "id": "run123",
                "actId": "actor123",
                "status": "SUCCEEDED",
                "defaultDatasetId": "dataset123",
            }
        }

        result = service.handle_webhook(payload, json.dumps(payload))

        assert result["status"] == "ok"
        assert result["articles_created"] == 1

        # Only valid article should be created
        articles = memory_session.exec(select(Article)).all()
        assert len(articles) == 1
        assert articles[0].url == "https://example.com/valid"

    @patch("local_newsifier.services.apify_webhook_service.ApifyService")
    def test_handle_webhook_dataset_error(self, mock_apify_class, memory_session):
        """Test handling of dataset fetch errors."""
        # Mock Apify client to raise an error
        mock_apify = MagicMock()
        mock_apify_class.return_value = mock_apify
        mock_apify.client.dataset.side_effect = Exception("API Error")

        service = ApifyWebhookService(memory_session)

        # Use resource structure as expected by the service
        payload = {
            "resource": {
                "id": "run123",
                "actId": "actor123",
                "status": "SUCCEEDED",
                "defaultDatasetId": "dataset123",
            }
        }

        result = service.handle_webhook(payload, json.dumps(payload))

        # Should still succeed but with 0 articles
        assert result["status"] == "ok"
        assert result["articles_created"] == 0

        # Webhook should still be saved
        webhook = memory_session.exec(
            select(ApifyWebhookRaw).where(ApifyWebhookRaw.run_id == "run123")
        ).first()
        assert webhook is not None

    @patch("local_newsifier.services.apify_webhook_service.ApifyService")
    def test_field_mapping_variations(self, mock_apify_class, memory_session):
        """Test that content is extracted from various field names."""
        # Mock Apify client
        mock_apify = MagicMock()
        mock_apify_class.return_value = mock_apify

        # Mock dataset items with different field variations
        mock_items = MagicMock()
        mock_items.items = [
            {
                # Uses 'text' field
                "url": "https://example.com/text-field",
                "title": "Text Field Article",
                "text": "This article uses the text field for content. " * 20,
            },
            {
                # Uses 'markdown' field
                "url": "https://example.com/markdown-field",
                "title": "Markdown Field Article",
                "markdown": "# This article uses the markdown field\n\nContent here. " * 20,
            },
            {
                # Uses 'body' field
                "url": "https://example.com/body-field",
                "title": "Body Field Article",
                "body": "This article uses the body field for content. " * 20,
            },
            {
                # Uses metadata.description as fallback
                "url": "https://example.com/metadata-field",
                "title": "Metadata Description Article",
                "metadata": {
                    "description": "This article uses metadata.description for content. " * 20,
                    "author": "Test Author",
                },
            },
        ]
        mock_apify.client.dataset.return_value.list_items.return_value = mock_items

        service = ApifyWebhookService(memory_session)

        payload = {
            "resource": {
                "id": "run123",
                "actId": "actor123",
                "status": "SUCCEEDED",
                "defaultDatasetId": "dataset123",
            }
        }

        result = service.handle_webhook(payload, json.dumps(payload))

        assert result["status"] == "ok"
        assert result["articles_created"] == 4

        # Check all articles were created
        articles = memory_session.exec(select(Article)).all()
        assert len(articles) == 4

        # Verify each article has content
        for article in articles:
            assert len(article.content) >= 500

    @patch("local_newsifier.services.apify_webhook_service.ApifyService")
    def test_minimum_content_length_increased(self, mock_apify_class, memory_session):
        """Test that minimum content length is now 500 characters."""
        # Mock Apify client
        mock_apify = MagicMock()
        mock_apify_class.return_value = mock_apify

        # Mock dataset items with various content lengths
        mock_items = MagicMock()
        mock_items.items = [
            {
                # Content with 499 chars - should be skipped
                "url": "https://example.com/short1",
                "title": "Short Article 1",
                "text": "a" * 499,
            },
            {
                # Content with exactly 500 chars - should be accepted
                "url": "https://example.com/exact",
                "title": "Exact Length Article",
                "text": "b" * 500,
            },
            {
                # Content with 501 chars - should be accepted
                "url": "https://example.com/long",
                "title": "Long Article",
                "text": "c" * 501,
            },
        ]
        mock_apify.client.dataset.return_value.list_items.return_value = mock_items

        service = ApifyWebhookService(memory_session)

        payload = {
            "resource": {
                "id": "run123",
                "actId": "actor123",
                "status": "SUCCEEDED",
                "defaultDatasetId": "dataset123",
            }
        }

        result = service.handle_webhook(payload, json.dumps(payload))

        assert result["status"] == "ok"
        assert result["articles_created"] == 2  # Only 500+ char articles

        # Check which articles were created
        articles = memory_session.exec(select(Article)).all()
        assert len(articles) == 2
        urls = [a.url for a in articles]
        assert "https://example.com/exact" in urls
        assert "https://example.com/long" in urls
        assert "https://example.com/short1" not in urls

    @patch("local_newsifier.services.apify_webhook_service.ApifyService")
    def test_metadata_published_date_parsing(self, mock_apify_class, memory_session):
        """Test that published date is parsed from metadata when available."""
        # Mock Apify client
        mock_apify = MagicMock()
        mock_apify_class.return_value = mock_apify

        # Mock dataset items with metadata
        mock_items = MagicMock()
        mock_items.items = [
            {
                "url": "https://example.com/with-date",
                "title": "Article with Published Date",
                "text": "Content with published date in metadata. " * 20,
                "metadata": {
                    "publishedAt": "2024-01-15T10:30:00Z",
                },
            },
            {
                "url": "https://example.com/no-date",
                "title": "Article without Published Date",
                "text": "Content without published date. " * 20,
            },
        ]
        mock_apify.client.dataset.return_value.list_items.return_value = mock_items

        service = ApifyWebhookService(memory_session)

        payload = {
            "resource": {
                "id": "run123",
                "actId": "actor123",
                "status": "SUCCEEDED",
                "defaultDatasetId": "dataset123",
            }
        }

        result = service.handle_webhook(payload, json.dumps(payload))

        assert result["status"] == "ok"
        assert result["articles_created"] == 2

        # Check articles and their published dates
        articles = memory_session.exec(select(Article)).all()
        assert len(articles) == 2

        # Find article with metadata date
        article_with_date = next(a for a in articles if "with-date" in a.url)
        assert article_with_date.published_at.year == 2024
        assert article_with_date.published_at.month == 1
        assert article_with_date.published_at.day == 15

    @patch("local_newsifier.services.apify_webhook_service.ApifyService")
    def test_handle_webhook_duplicate_still_creates_articles(
        self, mock_apify_class, memory_session
    ):
        """Test that duplicate webhooks still trigger article creation."""
        # Create mock apify service
        mock_apify = MagicMock()
        mock_apify_class.return_value = mock_apify

        service = ApifyWebhookService(memory_session)

        # Create existing webhook (simulating a previous webhook)
        existing = ApifyWebhookRaw(
            run_id="run123", actor_id="actor123", status="SUCCEEDED", data={}
        )
        memory_session.add(existing)
        memory_session.commit()

        # Mock the apify service to return dataset items
        mock_dataset = MagicMock()
        mock_dataset.list_items.return_value.items = [
            {
                "url": "https://example.com/article1",
                "title": "Test Article",
                "text": "A" * 1000,  # Long enough content
            }
        ]
        mock_apify.client.dataset.return_value = mock_dataset

        # Process duplicate webhook with dataset
        payload = {
            "resource": {
                "id": "run123",
                "actId": "actor123",
                "status": "SUCCEEDED",
                "defaultDatasetId": "dataset123",
            }
        }
        result = service.handle_webhook(payload, json.dumps(payload))

        # Should still create articles even though webhook is duplicate
        assert result["status"] == "ok"
        assert result["articles_created"] == 1
        assert result["is_new"] is False  # Webhook was not saved (duplicate)

        # Verify article was created
        articles = memory_session.exec(select(Article)).all()
        assert len(articles) == 1
        assert articles[0].url == "https://example.com/article1"

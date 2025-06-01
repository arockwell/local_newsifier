"""Tests for the simplified webhook implementation."""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from local_newsifier.api.dependencies import get_session
from local_newsifier.api.main import app
from local_newsifier.models.apify import ApifyWebhookRaw
from local_newsifier.models.article import Article


@pytest.fixture
def override_db_session(db_session: Session):
    """Override the database session dependency to use test session."""

    def _get_test_session():
        return db_session

    # Override the dependency
    app.dependency_overrides[get_session] = _get_test_session

    yield db_session

    # Clean up
    app.dependency_overrides.clear()


class TestSimplifiedWebhook:
    """Test the simplified webhook endpoint."""

    def test_webhook_accepts_valid_payload(
        self, client: TestClient, override_db_session: Session, mock_apify_client
    ):
        """Test that webhook accepts and stores valid payload."""
        # Mock empty dataset so it doesn't try to fetch
        mock_apify_client.dataset.return_value.list_items.return_value.items = []

        payload = {
            "resource": {
                "id": "test-run-001",
                "actId": "test-actor",
                "status": "SUCCEEDED",
                "defaultDatasetId": "test-dataset-001",
            }
        }

        response = client.post("/webhooks/apify", json=payload)

        assert response.status_code == 202
        data = response.json()
        assert data["status"] == "accepted"
        assert data["run_id"] == "test-run-001"

        # Verify webhook was stored
        webhook = override_db_session.exec(
            select(ApifyWebhookRaw).where(ApifyWebhookRaw.run_id == "test-run-001")
        ).first()
        assert webhook is not None
        assert webhook.actor_id == "test-actor"
        assert webhook.status == "SUCCEEDED"

    def test_webhook_handles_duplicates_gracefully(
        self, client: TestClient, override_db_session: Session, mock_apify_client
    ):
        """Test that duplicate webhooks are handled idempotently."""
        # Mock empty dataset
        mock_apify_client.dataset.return_value.list_items.return_value.items = []

        payload = {
            "resource": {
                "id": "test-run-002",
                "actId": "test-actor",
                "status": "SUCCEEDED",
                "defaultDatasetId": "test-dataset-002",
            }
        }

        # Send webhook twice
        response1 = client.post("/webhooks/apify", json=payload)
        response2 = client.post("/webhooks/apify", json=payload)

        # Both should succeed
        assert response1.status_code == 202
        assert response2.status_code == 202

        # Only one webhook should be stored
        webhooks = override_db_session.exec(
            select(ApifyWebhookRaw).where(ApifyWebhookRaw.run_id == "test-run-002")
        ).all()
        assert len(webhooks) == 1

    def test_webhook_rejects_missing_run_id(self, client: TestClient):
        """Test that webhook rejects payload without run_id."""
        payload = {"resource": {"actId": "test-actor", "status": "SUCCEEDED"}}

        response = client.post("/webhooks/apify", json=payload)

        assert response.status_code == 400
        assert "Missing required field: run_id" in response.json()["detail"]

    def test_webhook_creates_articles_from_dataset(
        self, client: TestClient, override_db_session: Session, mock_apify_client
    ):
        """Test that webhook creates articles from successful runs."""
        # Mock dataset items
        mock_dataset_items = [
            {
                "url": "https://example.com/article1",
                "title": "Test Article 1",
                "content": "This is test content that is long enough to pass validation. " * 10,
            },
            {
                "url": "https://example.com/article2",
                "title": "Test Article 2",
                "text": (
                    "This is another test article with enough content. " * 10
                ),  # Different field name
            },
        ]

        mock_apify_client.dataset.return_value.list_items.return_value.items = mock_dataset_items

        payload = {
            "resource": {
                "id": "test-run-003",
                "actId": "test-actor",
                "status": "SUCCEEDED",
                "defaultDatasetId": "test-dataset-003",
            }
        }

        response = client.post("/webhooks/apify", json=payload)

        assert response.status_code == 202
        data = response.json()
        assert data["articles_created"] == 2

        # Verify articles were created
        articles = override_db_session.exec(select(Article)).all()
        assert len(articles) == 2
        assert articles[0].url == "https://example.com/article1"
        assert articles[1].url == "https://example.com/article2"

    def test_webhook_skips_articles_with_missing_fields(
        self, client: TestClient, db_session: Session, mock_apify_client
    ):
        """Test that webhook skips articles with missing required fields."""
        mock_dataset_items = [
            {
                "url": "https://example.com/article1",
                # Missing title
                "content": "This is test content.",
            },
            {
                # Missing URL
                "title": "Test Article 2",
                "content": "This is test content.",
            },
            {
                "url": "https://example.com/article3",
                "title": "Test Article 3",
                # Content too short
                "content": "Short",
            },
            {
                "url": "https://example.com/article4",
                "title": "Test Article 4",
                "content": "This is valid test content that is long enough. " * 10,
            },
        ]

        mock_apify_client.dataset.return_value.list_items.return_value.items = mock_dataset_items

        payload = {
            "resource": {
                "id": "test-run-004",
                "actId": "test-actor",
                "status": "SUCCEEDED",
                "defaultDatasetId": "test-dataset-004",
            }
        }

        response = client.post("/webhooks/apify", json=payload)

        assert response.status_code == 202
        data = response.json()
        assert data["articles_created"] == 1  # Only one valid article

        # Verify only valid article was created
        articles = override_db_session.exec(select(Article)).all()
        assert len(articles) == 1
        assert articles[0].url == "https://example.com/article4"

    def test_webhook_handles_failed_runs(self, client: TestClient, override_db_session: Session):
        """Test that webhook handles failed actor runs."""
        payload = {"resource": {"id": "test-run-005", "actId": "test-actor", "status": "FAILED"}}

        response = client.post("/webhooks/apify", json=payload)

        assert response.status_code == 202
        data = response.json()
        assert data["articles_created"] == 0

        # Webhook should still be stored
        webhook = override_db_session.exec(
            select(ApifyWebhookRaw).where(ApifyWebhookRaw.run_id == "test-run-005")
        ).first()
        assert webhook is not None
        assert webhook.status == "FAILED"

    def test_webhook_validates_signature(self, client: TestClient):
        """Test that webhook validates signature when configured."""
        with patch("local_newsifier.config.settings.get_settings") as mock_settings:
            mock_settings.return_value.apify_webhook_secret = "test-secret"

            payload = {
                "resource": {"id": "test-run-006", "actId": "test-actor", "status": "SUCCEEDED"}
            }

            # Send with invalid signature
            response = client.post(
                "/webhooks/apify",
                json=payload,
                headers={"Apify-Webhook-Signature": "invalid-signature"},
            )

            assert response.status_code == 400
            assert "Invalid signature" in response.json()["detail"]

    def test_webhook_handles_dataset_fetch_error(
        self, client: TestClient, override_db_session: Session, mock_apify_client
    ):
        """Test that webhook handles errors when fetching dataset."""
        # Mock dataset fetch to raise error
        mock_apify_client.dataset.return_value.list_items.side_effect = Exception("API Error")

        payload = {
            "resource": {
                "id": "test-run-007",
                "actId": "test-actor",
                "status": "SUCCEEDED",
                "defaultDatasetId": "test-dataset-007",
            }
        }

        response = client.post("/webhooks/apify", json=payload)

        # Should still accept webhook even if article creation fails
        assert response.status_code == 202
        data = response.json()
        assert data["articles_created"] == 0

        # Webhook should be stored
        webhook = override_db_session.exec(
            select(ApifyWebhookRaw).where(ApifyWebhookRaw.run_id == "test-run-007")
        ).first()
        assert webhook is not None

    def test_webhook_handles_duplicate_articles(
        self, client: TestClient, override_db_session: Session, mock_apify_client
    ):
        """Test that webhook skips duplicate articles."""
        # Create existing article
        existing_article = Article(
            url="https://example.com/existing",
            title="Existing Article",
            content="Existing content",
            source="manual",
            status="published",
        )
        override_db_session.add(existing_article)
        override_db_session.commit()

        # Mock dataset with duplicate URL
        mock_dataset_items = [
            {
                "url": "https://example.com/existing",  # Duplicate
                "title": "Duplicate Article",
                "content": "This is duplicate content. " * 10,
            },
            {
                "url": "https://example.com/new",
                "title": "New Article",
                "content": "This is new content. " * 10,
            },
        ]

        mock_apify_client.dataset.return_value.list_items.return_value.items = mock_dataset_items

        payload = {
            "resource": {
                "id": "test-run-008",
                "actId": "test-actor",
                "status": "SUCCEEDED",
                "defaultDatasetId": "test-dataset-008",
            }
        }

        response = client.post("/webhooks/apify", json=payload)

        assert response.status_code == 202
        data = response.json()
        assert data["articles_created"] == 1  # Only new article created

        # Verify only new article was created
        articles = override_db_session.exec(
            select(Article).where(Article.url == "https://example.com/new")
        ).all()
        assert len(articles) == 1


@pytest.fixture
def mock_apify_client():
    """Mock Apify client for testing."""
    with patch(
        "local_newsifier.services.apify_webhook_service_simple.ApifyService"
    ) as mock_service:
        mock_client = MagicMock()
        mock_service.return_value.client = mock_client
        yield mock_client

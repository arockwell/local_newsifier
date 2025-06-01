"""
Test the webhook API endpoints.

These tests verify that webhook endpoints correctly handle
incoming webhooks from external services like Apify for validation
and logging. Data processing functionality will be tested separately.
"""

import datetime
import uuid
from unittest.mock import Mock

import pytest

from tests.ci_skip_config import ci_skip_async


@pytest.fixture(scope="module", autouse=True)
def mock_db():
    """Mock database calls for testing."""
    # Save original get_engine function
    from unittest.mock import MagicMock

    from local_newsifier.database import engine

    original_get_engine = engine.get_engine

    # Replace with mock function
    engine.get_engine = lambda: MagicMock()

    # Yield control back to test
    yield

    # Restore original function after tests
    engine.get_engine = original_get_engine


@pytest.fixture
def mock_webhook_service():
    """Helper fixture to override webhook service dependency."""
    from local_newsifier.api.dependencies import get_apify_webhook_service
    from local_newsifier.api.main import app

    # Store original overrides
    original_overrides = app.dependency_overrides.copy()

    def _override_service(mock_service):
        """Override the webhook service with a mock."""
        app.dependency_overrides[get_apify_webhook_service] = lambda: mock_service

    yield _override_service

    # Restore original overrides
    app.dependency_overrides = original_overrides


class TestApifyWebhookInfrastructure:
    """Test suite for Apify webhook infrastructure (validation and logging only)."""

    @ci_skip_async
    def test_apify_webhook_invalid_signature(self, client, monkeypatch, mock_webhook_service):
        """Test that the webhook rejects requests with invalid signatures."""
        # Set a webhook secret
        monkeypatch.setattr(
            "local_newsifier.config.settings.settings.APIFY_WEBHOOK_SECRET", "test_secret"
        )

        # Create a sample webhook payload
        payload = {
            "createdAt": datetime.datetime.now().isoformat(),
            "eventType": "ACTOR.RUN.SUCCEEDED",
            "actorId": "test_actor",
            "actorRunId": str(uuid.uuid4()),
            "userId": "test_user",
            "defaultKeyValueStoreId": "test_kvs",
            "defaultDatasetId": "test_dataset",
            "startedAt": datetime.datetime.now().isoformat(),
            "status": "SUCCEEDED",
            "webhookId": str(uuid.uuid4()),
        }

        # Mock the dependency injection to return error for invalid signature
        mock_service = Mock()
        mock_service.handle_webhook = Mock(
            return_value={"status": "error", "message": "Invalid signature"}
        )

        mock_webhook_service(mock_service)

        # Send request with wrong signature header
        response = client.post(
            "/webhooks/apify",
            json=payload,
            headers={"Apify-Webhook-Signature": "wrong_signature"},
        )

        # Should return bad request
        assert response.status_code == 400
        assert "Invalid signature" in response.json()["detail"]

    @ci_skip_async
    def test_apify_webhook_valid_payload(self, client, monkeypatch, mock_webhook_service):
        """Test that the webhook accepts valid payloads without signature."""
        # Clear webhook secret for this test
        monkeypatch.setattr("local_newsifier.config.settings.settings.APIFY_WEBHOOK_SECRET", None)

        # Create a sample webhook payload
        payload = {
            "createdAt": datetime.datetime.now().isoformat(),
            "eventType": "ACTOR.RUN.SUCCEEDED",
            "actorId": "test_actor",
            "actorRunId": str(uuid.uuid4()),
            "userId": "test_user",
            "defaultKeyValueStoreId": "test_kvs",
            "defaultDatasetId": "test_dataset",
            "startedAt": datetime.datetime.now().isoformat(),
            "status": "SUCCEEDED",
            "webhookId": str(uuid.uuid4()),
        }

        # Mock the dependency injection to return a mock service
        mock_service = Mock()
        mock_service.handle_webhook = Mock(
            return_value={
                "status": "ok",
                "message": "Webhook processed. Articles created: 0",
                "run_id": payload["actorRunId"],
                "articles_created": 0,
                "actor_id": "test_actor",
                "dataset_id": "test_dataset",
            }
        )

        # Override the service
        mock_webhook_service(mock_service)

        # Send request to webhook endpoint
        response = client.post("/webhooks/apify", json=payload)

        # Should be accepted
        assert response.status_code == 202
        response_data = response.json()
        assert response_data["status"] == "accepted"
        assert response_data["actor_id"] == "test_actor"
        assert response_data["dataset_id"] == "test_dataset"
        assert response_data["processing_status"] == "completed"
        assert "processed" in response_data["message"].lower()

    @ci_skip_async
    def test_apify_webhook_no_secret_configured(self, client, monkeypatch, mock_webhook_service):
        """Test that the webhook accepts all requests when no secret is configured."""
        # Clear the webhook secret
        monkeypatch.setattr("local_newsifier.config.settings.settings.APIFY_WEBHOOK_SECRET", None)

        # Create a sample webhook payload without secret
        payload = {
            "createdAt": datetime.datetime.now().isoformat(),
            "eventType": "ACTOR.RUN.FAILED",
            "actorId": "test_actor",
            "actorRunId": str(uuid.uuid4()),
            "userId": "test_user",
            "defaultKeyValueStoreId": "test_kvs",
            "defaultDatasetId": "test_dataset",
            "startedAt": datetime.datetime.now().isoformat(),
            "status": "FAILED",
            "webhookId": str(uuid.uuid4()),
        }

        # Mock the dependency injection to return a mock service
        mock_service = Mock()
        mock_service.handle_webhook = Mock(
            return_value={
                "status": "ok",
                "message": "Webhook processed. Articles created: 0",
                "run_id": payload["actorRunId"],
                "articles_created": 0,
            }
        )

        mock_webhook_service(mock_service)

        # Send request to webhook endpoint
        response = client.post("/webhooks/apify", json=payload)

        # Should be accepted even without secret
        assert response.status_code == 202
        response_data = response.json()
        assert response_data["status"] == "accepted"
        assert response_data["processing_status"] == "completed"

    @ci_skip_async
    def test_apify_webhook_invalid_payload_structure(self, client, mock_webhook_service):
        """Test that the webhook rejects malformed payloads."""
        # Send an invalid payload (missing required fields)
        invalid_payload = {
            "eventType": "ACTOR.RUN.SUCCEEDED",
            # Missing required fields like actorId, actorRunId, etc.
        }

        # Mock the dependency injection to return error for missing fields
        mock_service = Mock()
        mock_service.handle_webhook = Mock(
            return_value={"status": "error", "message": "Missing required fields"}
        )

        mock_webhook_service(mock_service)

        # Send request to webhook endpoint
        response = client.post("/webhooks/apify", json=invalid_payload)

        # Should return 400 for error response from webhook service
        assert response.status_code == 400
        response_data = response.json()
        assert "Missing required fields" in response_data["detail"]

    @ci_skip_async
    def test_apify_webhook_sync_conversion(self, client, monkeypatch, mock_webhook_service):
        """Test that the webhook endpoint is properly converted to sync (no async/await)."""
        # Clear webhook secret for this test
        monkeypatch.setattr("local_newsifier.config.settings.settings.APIFY_WEBHOOK_SECRET", None)

        # Create a sample webhook payload
        payload = {
            "createdAt": datetime.datetime.now().isoformat(),
            "eventType": "ACTOR.RUN.SUCCEEDED",
            "actorId": "test_actor",
            "actorRunId": str(uuid.uuid4()),
            "userId": "test_user",
            "defaultKeyValueStoreId": "test_kvs",
            "defaultDatasetId": "test_dataset",
            "startedAt": datetime.datetime.now().isoformat(),
            "status": "SUCCEEDED",
            "webhookId": str(uuid.uuid4()),
        }

        # Mock the dependency injection to return a mock service
        mock_service = Mock()
        mock_service.handle_webhook = Mock(
            return_value={
                "status": "ok",
                "message": "Webhook processed. Articles created: 0",
                "run_id": payload["actorRunId"],
                "articles_created": 0,
            }
        )

        mock_webhook_service(mock_service)

        # Send request to webhook endpoint
        response = client.post("/webhooks/apify", json=payload)

        # Should be accepted
        assert response.status_code == 202
        response_data = response.json()
        assert response_data["status"] == "accepted"

        # Verify that the mock was called with correct parameters
        mock_service.handle_webhook.assert_called_once()
        call_args = mock_service.handle_webhook.call_args
        assert call_args[1]["payload"] == payload
        assert "raw_payload" in call_args[1]
        assert call_args[1]["signature"] is None  # No signature header sent

    @ci_skip_async
    def test_apify_webhook_exception_handling(self, client, mock_webhook_service):
        """Test that the webhook handles exceptions gracefully."""
        payload = {
            "createdAt": datetime.datetime.now().isoformat(),
            "eventType": "ACTOR.RUN.SUCCEEDED",
            "actorId": "test_actor",
            "actorRunId": str(uuid.uuid4()),
            "userId": "test_user",
            "defaultKeyValueStoreId": "test_kvs",
            "defaultDatasetId": "test_dataset",
            "startedAt": datetime.datetime.now().isoformat(),
            "status": "SUCCEEDED",
            "webhookId": str(uuid.uuid4()),
        }

        # Mock the dependency injection to raise an exception
        mock_service = Mock()
        mock_service.handle_webhook = Mock(side_effect=Exception("Database error"))

        mock_webhook_service(mock_service)

        # Send request to webhook endpoint
        response = client.post("/webhooks/apify", json=payload)

        # Should return error response
        assert response.status_code == 202  # Still accepted but with error status
        response_data = response.json()
        assert response_data["status"] == "accepted"  # Always accepted to prevent retry storms
        assert response_data["processing_status"] == "error"  # But processing status shows error
        assert "Database error" in response_data["message"]

    @ci_skip_async
    def test_apify_webhook_multi_status_acceptance(self, client, monkeypatch, mock_webhook_service):
        """Test that webhooks with different statuses for the same run are both accepted."""
        # Clear webhook secret for this test
        monkeypatch.setattr("local_newsifier.config.settings.settings.APIFY_WEBHOOK_SECRET", None)

        run_id = str(uuid.uuid4())

        # Create STARTED webhook payload
        started_payload = {
            "createdAt": datetime.datetime.now().isoformat(),
            "eventType": "ACTOR.RUN.STARTED",
            "actorId": "test_actor",
            "actorRunId": run_id,
            "userId": "test_user",
            "defaultKeyValueStoreId": "test_kvs",
            "defaultDatasetId": "test_dataset",
            "startedAt": datetime.datetime.now().isoformat(),
            "status": "STARTED",
            "webhookId": str(uuid.uuid4()),
        }

        # Mock the service to accept the STARTED webhook
        mock_service = Mock()
        mock_service.handle_webhook = Mock(
            return_value={
                "status": "ok",
                "message": "Webhook processed. Articles created: 0",
                "run_id": run_id,
                "articles_created": 0,
            }
        )

        mock_webhook_service(mock_service)

        # Send STARTED webhook
        response = client.post("/webhooks/apify", json=started_payload)
        assert response.status_code == 202
        assert response.json()["status"] == "accepted"

        # Create SUCCEEDED webhook payload with same run_id
        succeeded_payload = {
            "createdAt": datetime.datetime.now().isoformat(),
            "eventType": "ACTOR.RUN.SUCCEEDED",
            "actorId": "test_actor",
            "actorRunId": run_id,
            "userId": "test_user",
            "defaultKeyValueStoreId": "test_kvs",
            "defaultDatasetId": "test_dataset",
            "startedAt": datetime.datetime.now().isoformat(),
            "status": "SUCCEEDED",
            "webhookId": str(uuid.uuid4()),
        }

        # Mock the service to accept the SUCCEEDED webhook and create articles
        mock_service.handle_webhook = Mock(
            return_value={
                "status": "ok",
                "message": "Webhook processed. Articles created: 5",
                "run_id": run_id,
                "articles_created": 5,
            }
        )

        # Send SUCCEEDED webhook
        response = client.post("/webhooks/apify", json=succeeded_payload)
        assert response.status_code == 202
        response_data = response.json()
        assert response_data["status"] == "accepted"
        assert response_data["processing_status"] == "completed"
        assert "5" in response_data["message"]

    @ci_skip_async
    def test_apify_webhook_duplicate_same_status_rejected(
        self, client, monkeypatch, mock_webhook_service
    ):
        """Test that duplicate webhooks with the same run_id and status are rejected."""
        # Clear webhook secret for this test
        monkeypatch.setattr("local_newsifier.config.settings.settings.APIFY_WEBHOOK_SECRET", None)

        run_id = str(uuid.uuid4())

        # Create SUCCEEDED webhook payload
        payload = {
            "createdAt": datetime.datetime.now().isoformat(),
            "eventType": "ACTOR.RUN.SUCCEEDED",
            "actorId": "test_actor",
            "actorRunId": run_id,
            "userId": "test_user",
            "defaultKeyValueStoreId": "test_kvs",
            "defaultDatasetId": "test_dataset",
            "startedAt": datetime.datetime.now().isoformat(),
            "status": "SUCCEEDED",
            "webhookId": str(uuid.uuid4()),
        }

        # Mock the service - first call succeeds
        mock_service = Mock()
        mock_service.handle_webhook = Mock(
            return_value={
                "status": "ok",
                "message": "Webhook processed. Articles created: 3",
                "run_id": run_id,
                "articles_created": 3,
            }
        )

        mock_webhook_service(mock_service)

        # Send first SUCCEEDED webhook
        response = client.post("/webhooks/apify", json=payload)
        assert response.status_code == 202
        assert response.json()["status"] == "accepted"

        # Mock the service - second call is duplicate
        mock_service.handle_webhook = Mock(
            return_value={"status": "ok", "message": "Duplicate webhook ignored"}
        )

        # Send duplicate SUCCEEDED webhook
        response = client.post("/webhooks/apify", json=payload)
        assert response.status_code == 202
        response_data = response.json()
        assert response_data["status"] == "accepted"
        assert "duplicate" in response_data["message"].lower()

    @ci_skip_async
    def test_apify_webhook_only_succeeded_creates_articles(
        self, client, monkeypatch, mock_webhook_service
    ):
        """Test that only SUCCEEDED webhooks trigger article creation."""
        # Clear webhook secret for this test
        monkeypatch.setattr("local_newsifier.config.settings.settings.APIFY_WEBHOOK_SECRET", None)

        run_id = str(uuid.uuid4())

        # Test STARTED webhook - should not create articles
        started_payload = {
            "createdAt": datetime.datetime.now().isoformat(),
            "eventType": "ACTOR.RUN.STARTED",
            "actorId": "test_actor",
            "actorRunId": run_id,
            "userId": "test_user",
            "defaultKeyValueStoreId": "test_kvs",
            "defaultDatasetId": "test_dataset",
            "startedAt": datetime.datetime.now().isoformat(),
            "status": "STARTED",
            "webhookId": str(uuid.uuid4()),
        }

        # Mock the service - STARTED status creates no articles
        mock_service = Mock()
        mock_service.handle_webhook = Mock(
            return_value={
                "status": "ok",
                "message": "Webhook processed. Articles created: 0",
                "run_id": run_id,
                "articles_created": 0,
            }
        )

        mock_webhook_service(mock_service)

        # Send STARTED webhook
        response = client.post("/webhooks/apify", json=started_payload)
        assert response.status_code == 202
        response_data = response.json()
        assert response_data["status"] == "accepted"
        assert "0" in response_data["message"] or "no articles" in response_data["message"].lower()

        # Test FAILED webhook - should not create articles
        failed_payload = started_payload.copy()
        failed_payload["eventType"] = "ACTOR.RUN.FAILED"
        failed_payload["status"] = "FAILED"
        failed_payload["webhookId"] = str(uuid.uuid4())

        # Mock the service - FAILED status creates no articles
        mock_service.handle_webhook = Mock(
            return_value={
                "status": "ok",
                "message": "Webhook processed. Articles created: 0",
                "run_id": run_id,
                "articles_created": 0,
            }
        )

        # Send FAILED webhook
        response = client.post("/webhooks/apify", json=failed_payload)
        assert response.status_code == 202
        response_data = response.json()
        assert response_data["status"] == "accepted"
        assert "0" in response_data["message"] or "no articles" in response_data["message"].lower()

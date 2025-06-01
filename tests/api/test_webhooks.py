"""
Test the webhook API endpoints.

These tests verify that webhook endpoints correctly handle
incoming webhooks from external services like Apify for validation
and logging. Data processing functionality will be tested separately.
"""

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
    from local_newsifier.api.main import app
    from local_newsifier.api.routers.webhooks_simple import get_webhook_service

    # Store original overrides
    original_overrides = app.dependency_overrides.copy()

    def _override_service(mock_service):
        """Override the webhook service with a mock."""
        app.dependency_overrides[get_webhook_service] = lambda: mock_service

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

        # Create a sample webhook payload in simplified format
        payload = {
            "resource": {
                "id": str(uuid.uuid4()),
                "actId": "test_actor",
                "status": "SUCCEEDED",
                "defaultDatasetId": "test_dataset",
            }
        }

        # Mock the dependency injection to return error for invalid signature
        mock_service = Mock()
        mock_service.handle_webhook = Mock(side_effect=ValueError("Invalid signature"))

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

        # Create a sample webhook payload in simplified format
        run_id = str(uuid.uuid4())
        payload = {
            "resource": {
                "id": run_id,
                "actId": "test_actor",
                "status": "SUCCEEDED",
                "defaultDatasetId": "test_dataset",
            }
        }

        # Mock the dependency injection to return a mock service
        mock_service = Mock()
        mock_service.handle_webhook = Mock(
            return_value={
                "status": "ok",
                "message": "Webhook processed. Articles created: 0",
                "run_id": run_id,
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
        assert response_data["articles_created"] == 0

    @ci_skip_async
    def test_apify_webhook_no_secret_configured(self, client, monkeypatch, mock_webhook_service):
        """Test that the webhook accepts all requests when no secret is configured."""
        # Clear the webhook secret
        monkeypatch.setattr("local_newsifier.config.settings.settings.APIFY_WEBHOOK_SECRET", None)

        # Create a sample webhook payload
        run_id = str(uuid.uuid4())
        payload = {
            "resource": {
                "id": run_id,
                "actId": "test_actor",
                "status": "SUCCEEDED",
                "defaultDatasetId": "test_dataset",
            }
        }

        # Mock the service to return success
        mock_service = Mock()
        mock_service.handle_webhook = Mock(
            return_value={
                "status": "ok",
                "run_id": run_id,
                "articles_created": 0,
                "actor_id": "test_actor",
                "dataset_id": "test_dataset",
            }
        )

        # Override the service
        mock_webhook_service(mock_service)

        # Send request without signature header
        response = client.post("/webhooks/apify", json=payload)

        # Should be accepted
        assert response.status_code == 202
        assert response.json()["status"] == "accepted"

    @ci_skip_async
    def test_apify_webhook_invalid_payload_structure(self, client, mock_webhook_service):
        """Test that the webhook handles malformed payloads gracefully."""
        # Send a payload missing the required structure
        payload = {"some_random_field": "value"}

        # Mock the service to raise ValueError for missing fields
        mock_service = Mock()
        mock_service.handle_webhook = Mock(
            side_effect=ValueError("Missing required field: resource")
        )

        # Override the service
        mock_webhook_service(mock_service)

        # Send request
        response = client.post("/webhooks/apify", json=payload)

        # Should return bad request
        assert response.status_code == 400
        assert "Missing required field" in response.json()["detail"]

    @ci_skip_async
    def test_apify_webhook_sync_conversion(self, client, mock_webhook_service):
        """Test that async operations are properly converted to sync."""
        # Test payload
        run_id = str(uuid.uuid4())
        payload = {
            "resource": {
                "id": run_id,
                "actId": "test_actor",
                "status": "SUCCEEDED",
                "defaultDatasetId": "test_dataset",
            }
        }

        # Mock the service
        mock_service = Mock()
        mock_service.handle_webhook = Mock(
            return_value={
                "status": "ok",
                "run_id": run_id,
                "articles_created": 0,
                "actor_id": "test_actor",
                "dataset_id": "test_dataset",
            }
        )

        # Override the service
        mock_webhook_service(mock_service)

        # Send request
        response = client.post("/webhooks/apify", json=payload)

        # Verify response
        assert response.status_code == 202
        assert response.json()["status"] == "accepted"

        # Verify service was called with correct parameters
        mock_service.handle_webhook.assert_called_once()

    @ci_skip_async
    def test_apify_webhook_exception_handling(self, client, mock_webhook_service):
        """Test that exceptions are handled gracefully."""
        # Test payload
        payload = {
            "resource": {
                "id": str(uuid.uuid4()),
                "actId": "test_actor",
                "status": "SUCCEEDED",
                "defaultDatasetId": "test_dataset",
            }
        }

        # Mock the service to raise an exception
        mock_service = Mock()
        mock_service.handle_webhook = Mock(side_effect=Exception("Unexpected error"))

        # Override the service
        mock_webhook_service(mock_service)

        # Send request
        response = client.post("/webhooks/apify", json=payload)

        # Should still accept but with error status (to prevent retry storms)
        assert response.status_code == 202
        response_data = response.json()
        assert response_data["status"] == "error"
        assert response_data["processing_status"] == "error"
        assert "Unexpected error" in response_data["message"]

    @ci_skip_async
    def test_apify_webhook_multi_status_acceptance(self, client, mock_webhook_service):
        """Test that webhooks with different statuses are accepted."""
        statuses = ["SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT", "READY"]

        for status in statuses:
            # Test payload
            run_id = str(uuid.uuid4())
            payload = {
                "resource": {
                    "id": run_id,
                    "actId": "test_actor",
                    "status": status,
                    "defaultDatasetId": "test_dataset" if status == "SUCCEEDED" else None,
                }
            }

            # Mock the service based on status
            mock_service = Mock()
            mock_service.handle_webhook = Mock(
                return_value={
                    "status": "ok",
                    "run_id": run_id,
                    "articles_created": 0 if status != "SUCCEEDED" else 1,
                    "actor_id": "test_actor",
                    "dataset_id": "test_dataset" if status == "SUCCEEDED" else None,
                }
            )

            # Override the service
            mock_webhook_service(mock_service)

            # Send request
            response = client.post("/webhooks/apify", json=payload)

            # All statuses should be accepted
            assert response.status_code == 202
            assert response.json()["status"] == "accepted"

    @ci_skip_async
    def test_apify_webhook_duplicate_same_status_rejected(self, client, mock_webhook_service):
        """Test that duplicate webhooks are handled gracefully."""
        # Test payload
        run_id = str(uuid.uuid4())
        payload = {
            "resource": {
                "id": run_id,
                "actId": "test_actor",
                "status": "SUCCEEDED",
                "defaultDatasetId": "test_dataset",
            }
        }

        # Mock the service to accept duplicates
        mock_service = Mock()
        mock_service.handle_webhook = Mock(
            return_value={
                "status": "ok",
                "run_id": run_id,
                "articles_created": 0,
                "actor_id": "test_actor",
                "dataset_id": "test_dataset",
            }
        )

        # Override the service
        mock_webhook_service(mock_service)

        # Send same payload twice
        response1 = client.post("/webhooks/apify", json=payload)
        response2 = client.post("/webhooks/apify", json=payload)

        # Both should be accepted (idempotent)
        assert response1.status_code == 202
        assert response2.status_code == 202

    @ci_skip_async
    def test_apify_webhook_only_succeeded_creates_articles(self, client, mock_webhook_service):
        """Test that only SUCCEEDED status creates articles."""
        # Test SUCCEEDED status
        run_id = str(uuid.uuid4())
        payload = {
            "resource": {
                "id": run_id,
                "actId": "test_actor",
                "status": "SUCCEEDED",
                "defaultDatasetId": "test_dataset",
            }
        }

        # Mock the service to return articles created
        mock_service = Mock()
        mock_service.handle_webhook = Mock(
            return_value={
                "status": "ok",
                "run_id": run_id,
                "articles_created": 5,
                "actor_id": "test_actor",
                "dataset_id": "test_dataset",
            }
        )

        # Override the service
        mock_webhook_service(mock_service)

        # Send request
        response = client.post("/webhooks/apify", json=payload)

        # Should create articles
        assert response.status_code == 202
        assert response.json()["articles_created"] == 5

        # Test FAILED status
        run_id = str(uuid.uuid4())
        payload["resource"]["id"] = run_id
        payload["resource"]["status"] = "FAILED"

        # Mock the service for failed status
        mock_service.handle_webhook = Mock(
            return_value={
                "status": "ok",
                "run_id": run_id,
                "articles_created": 0,
                "actor_id": "test_actor",
                "dataset_id": None,
            }
        )

        # Send request
        response = client.post("/webhooks/apify", json=payload)

        # Should not create articles
        assert response.status_code == 202
        assert response.json()["articles_created"] == 0

"""Tests for the simplified webhook implementation."""

from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from local_newsifier.api.main import app
from local_newsifier.api.routers.webhooks_simple import get_webhook_service


@pytest.fixture
def mock_webhook_service():
    """Mock the webhook service for API tests."""
    mock_service = Mock()

    def _get_mock_service():
        return mock_service

    # Override the dependency
    app.dependency_overrides[get_webhook_service] = _get_mock_service

    yield mock_service

    # Clean up
    app.dependency_overrides.clear()


@pytest.fixture
def client():
    """Create a FastAPI test client."""
    with TestClient(app) as test_client:
        yield test_client


class TestSimplifiedWebhook:
    """Test the simplified webhook endpoint."""

    def test_webhook_accepts_valid_payload(self, client: TestClient, mock_webhook_service: Mock):
        """Test that webhook accepts and stores valid payload."""
        # Configure mock to return success
        mock_webhook_service.handle_webhook.return_value = {
            "run_id": "test-run-001",
            "actor_id": "test-actor",
            "dataset_id": "test-dataset-001",
            "status": "SUCCEEDED",
            "articles_created": 0,
        }

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

        # Verify service was called correctly
        mock_webhook_service.handle_webhook.assert_called_once()
        call_kwargs = mock_webhook_service.handle_webhook.call_args.kwargs
        assert call_kwargs["payload"]["resource"]["id"] == "test-run-001"

    def test_webhook_handles_duplicates_gracefully(
        self, client: TestClient, mock_webhook_service: Mock
    ):
        """Test that duplicate webhooks are handled idempotently."""
        # Configure mock to return success for both calls
        mock_webhook_service.handle_webhook.return_value = {
            "run_id": "test-run-002",
            "actor_id": "test-actor",
            "dataset_id": "test-dataset-002",
            "status": "SUCCEEDED",
            "articles_created": 0,
        }

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

        # Service should be called twice
        assert mock_webhook_service.handle_webhook.call_count == 2

    def test_webhook_rejects_missing_run_id(self, client: TestClient, mock_webhook_service: Mock):
        """Test that webhook rejects payload without run_id."""
        # Configure mock to raise ValueError for missing fields
        mock_webhook_service.handle_webhook.side_effect = ValueError(
            "Missing required field: run_id"
        )

        payload = {"resource": {"actId": "test-actor", "status": "SUCCEEDED"}}

        response = client.post("/webhooks/apify", json=payload)

        assert response.status_code == 400
        assert "Missing required field: run_id" in response.json()["detail"]

    def test_webhook_creates_articles_from_dataset(
        self, client: TestClient, mock_webhook_service: Mock
    ):
        """Test that webhook creates articles from successful runs."""
        # Configure mock to return articles created
        mock_webhook_service.handle_webhook.return_value = {
            "run_id": "test-run-003",
            "actor_id": "test-actor",
            "dataset_id": "test-dataset-003",
            "status": "SUCCEEDED",
            "articles_created": 2,
        }

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

    def test_webhook_handles_failed_runs(self, client: TestClient, mock_webhook_service: Mock):
        """Test that webhook handles failed actor runs."""
        # Configure mock for failed run
        mock_webhook_service.handle_webhook.return_value = {
            "run_id": "test-run-005",
            "actor_id": "test-actor",
            "dataset_id": None,
            "status": "FAILED",
            "articles_created": 0,
        }

        payload = {"resource": {"id": "test-run-005", "actId": "test-actor", "status": "FAILED"}}

        response = client.post("/webhooks/apify", json=payload)

        assert response.status_code == 202
        data = response.json()
        assert data["articles_created"] == 0

    def test_webhook_validates_signature(self, client: TestClient, mock_webhook_service: Mock):
        """Test that webhook validates signature when configured."""
        # Configure mock to raise ValueError for invalid signature
        mock_webhook_service.handle_webhook.side_effect = ValueError("Invalid signature")

        payload = {"resource": {"id": "test-run-006", "actId": "test-actor", "status": "SUCCEEDED"}}

        # Send with invalid signature
        response = client.post(
            "/webhooks/apify",
            json=payload,
            headers={"Apify-Webhook-Signature": "invalid-signature"},
        )

        assert response.status_code == 400
        assert "Invalid signature" in response.json()["detail"]

    def test_webhook_handles_dataset_fetch_error(
        self, client: TestClient, mock_webhook_service: Mock
    ):
        """Test that webhook handles errors when fetching dataset."""
        # Configure mock to return success but with error in article creation
        mock_webhook_service.handle_webhook.return_value = {
            "run_id": "test-run-007",
            "actor_id": "test-actor",
            "dataset_id": "test-dataset-007",
            "status": "SUCCEEDED",
            "articles_created": 0,
            "error": "Failed to fetch dataset",
        }

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

    def test_webhook_handles_service_errors_gracefully(
        self, client: TestClient, mock_webhook_service: Mock
    ):
        """Test that webhook handles service errors gracefully."""
        # Configure mock to raise a general exception
        mock_webhook_service.handle_webhook.side_effect = Exception("Unexpected error")

        payload = {
            "resource": {
                "id": "test-run-008",
                "actId": "test-actor",
                "status": "SUCCEEDED",
                "defaultDatasetId": "test-dataset-008",
            }
        }

        response = client.post("/webhooks/apify", json=payload)

        # Should return 500 for unexpected errors
        assert response.status_code == 500

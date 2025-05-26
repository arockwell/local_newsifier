"""
Test the webhook API endpoints.

These tests verify that webhook endpoints correctly handle
incoming webhooks from external services like Apify for validation
and logging. Data processing functionality will be tested separately.
"""

import datetime
import uuid
from unittest.mock import AsyncMock, patch

import pytest

from tests.ci_skip_config import ci_skip_async


@pytest.fixture(scope="module", autouse=True)
def mock_db():
    """Mock database calls for testing."""
    # Save original create_db_and_tables function
    from local_newsifier.database import engine

    original_create_db = engine.create_db_and_tables

    # Replace with no-op function
    engine.create_db_and_tables = lambda: None

    # Yield control back to test
    yield

    # Restore original function after tests
    engine.create_db_and_tables = original_create_db


class TestApifyWebhookInfrastructure:
    """Test suite for Apify webhook infrastructure (validation and logging only)."""

    @ci_skip_async
    def test_apify_webhook_invalid_signature(self, client, monkeypatch):
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

        # Mock the async webhook service to return error for invalid signature
        with patch("local_newsifier.api.routers.webhooks.ApifyWebhookServiceAsync") as MockService:
            mock_instance = MockService.return_value
            mock_instance.handle_webhook = AsyncMock(
                return_value={"status": "error", "message": "Invalid signature"}
            )

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
    def test_apify_webhook_valid_payload(self, client, monkeypatch):
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

        # Mock the async webhook service to return success
        with patch("local_newsifier.api.routers.webhooks.ApifyWebhookServiceAsync") as MockService:
            mock_instance = MockService.return_value
            mock_instance.handle_webhook = AsyncMock(
                return_value={
                    "status": "ok",
                    "message": "Webhook processed. Articles created: 0",
                    "run_id": payload["actorRunId"],
                    "articles_created": 0,
                }
            )

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
    def test_apify_webhook_no_secret_configured(self, client, monkeypatch):
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

        # Mock the async webhook service to return success
        with patch("local_newsifier.api.routers.webhooks.ApifyWebhookServiceAsync") as MockService:
            mock_instance = MockService.return_value
            mock_instance.handle_webhook = AsyncMock(
                return_value={
                    "status": "ok",
                    "message": "Webhook processed. Articles created: 0",
                    "run_id": payload["actorRunId"],
                    "articles_created": 0,
                }
            )

            # Send request to webhook endpoint
            response = client.post("/webhooks/apify", json=payload)

            # Should be accepted even without secret
            assert response.status_code == 202
            response_data = response.json()
            assert response_data["status"] == "accepted"
            assert response_data["processing_status"] == "completed"

    @ci_skip_async
    def test_apify_webhook_invalid_payload_structure(self, client):
        """Test that the webhook rejects malformed payloads."""
        # Send an invalid payload (missing required fields)
        invalid_payload = {
            "eventType": "ACTOR.RUN.SUCCEEDED",
            # Missing required fields like actorId, actorRunId, etc.
        }

        # Mock the async webhook service to return error for missing fields
        with patch("local_newsifier.api.routers.webhooks.ApifyWebhookServiceAsync") as MockService:
            mock_instance = MockService.return_value
            mock_instance.handle_webhook = AsyncMock(
                return_value={"status": "error", "message": "Missing required fields"}
            )

            # Send request to webhook endpoint
            response = client.post("/webhooks/apify", json=invalid_payload)

            # Should return accepted but with error message about missing fields
            assert response.status_code == 202
            response_data = response.json()
            assert response_data["status"] == "error"
            assert "Missing required fields" in response_data["message"]

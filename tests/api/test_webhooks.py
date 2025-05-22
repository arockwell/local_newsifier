"""
Test the webhook API endpoints.

These tests verify that webhook endpoints correctly handle
incoming webhooks from external services like Apify for validation
and logging. Data processing functionality will be tested separately.
"""

import datetime
import uuid

import pytest


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

    def test_apify_webhook_invalid_secret(self, client, monkeypatch):
        """Test that the webhook rejects requests with invalid secrets."""
        # Set a webhook secret
        monkeypatch.setattr(
            "local_newsifier.config.settings.settings.APIFY_WEBHOOK_SECRET", "test_secret"
        )

        # Create a sample webhook payload with wrong secret
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
            "secret": "wrong_secret",  # Wrong secret
        }

        # Send request to webhook endpoint
        response = client.post("/webhooks/apify", json=payload)

        # Should be unauthorized
        assert response.status_code == 401
        assert "Invalid webhook secret" in response.json()["detail"]

    def test_apify_webhook_valid_payload(self, client, monkeypatch):
        """Test that the webhook accepts valid payloads."""
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
            "secret": "test_secret",  # Correct secret
        }

        # Send request to webhook endpoint
        response = client.post("/webhooks/apify", json=payload)

        # Should be accepted
        assert response.status_code == 202
        response_data = response.json()
        assert response_data["status"] == "accepted"
        assert response_data["actor_id"] == "test_actor"
        assert response_data["dataset_id"] == "test_dataset"
        assert response_data["processing_status"] == "webhook_recorded"
        assert "received and validated" in response_data["message"]

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

        # Send request to webhook endpoint
        response = client.post("/webhooks/apify", json=payload)

        # Should be accepted even without secret
        assert response.status_code == 202
        response_data = response.json()
        assert response_data["status"] == "accepted"
        assert response_data["processing_status"] == "webhook_recorded"

    def test_apify_webhook_logs_details(self, client, monkeypatch, caplog):
        """Test that the webhook properly logs webhook details."""
        # Clear the webhook secret to simplify test
        monkeypatch.setattr("local_newsifier.config.settings.settings.APIFY_WEBHOOK_SECRET", None)

        # Create a sample webhook payload
        payload = {
            "createdAt": datetime.datetime.now().isoformat(),
            "eventType": "ACTOR.RUN.SUCCEEDED",
            "actorId": "test_actor_123",
            "actorRunId": str(uuid.uuid4()),
            "userId": "test_user",
            "defaultKeyValueStoreId": "test_kvs",
            "defaultDatasetId": "test_dataset_456",
            "startedAt": datetime.datetime.now().isoformat(),
            "status": "SUCCEEDED",
            "webhookId": str(uuid.uuid4()),
        }

        # Send request to webhook endpoint
        response = client.post("/webhooks/apify", json=payload)

        # Should be accepted
        assert response.status_code == 202

        # Check that appropriate logs were generated
        log_messages = [record.message for record in caplog.records]

        # Should log webhook receipt
        assert any(
            "Received Apify webhook: ACTOR.RUN.SUCCEEDED for actor test_actor_123" in msg
            for msg in log_messages
        )

        # Should log webhook details
        # Debug: Print all log messages to understand what's happening in CI
        print(f"All log messages: {log_messages}")
        webhook_detail_messages = [
            msg for msg in log_messages if "test_actor_123" in msg and "test_dataset_456" in msg
        ]
        print(f"Webhook detail messages: {webhook_detail_messages}")

        # More explicit check
        has_both_details = any(
            "test_actor_123" in msg and "test_dataset_456" in msg for msg in log_messages
        )
        if not has_both_details:
            # More helpful error message
            actor_messages = [msg for msg in log_messages if "test_actor_123" in msg]
            dataset_messages = [msg for msg in log_messages if "test_dataset_456" in msg]
            raise AssertionError(
                f"Expected log message with both actor and dataset IDs. "
                f"Actor messages: {actor_messages}, Dataset messages: {dataset_messages}, "
                f"All messages: {log_messages}"
            )

        assert has_both_details

    def test_apify_webhook_invalid_payload_structure(self, client):
        """Test that the webhook rejects malformed payloads."""
        # Send an invalid payload (missing required fields)
        invalid_payload = {
            "eventType": "ACTOR.RUN.SUCCEEDED",
            # Missing required fields like actorId, createdAt, etc.
        }

        # Send request to webhook endpoint
        response = client.post("/webhooks/apify", json=invalid_payload)

        # Should return validation error
        assert response.status_code == 422  # Unprocessable Entity

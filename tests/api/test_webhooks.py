"""
Test the webhook API endpoints.

These tests verify that webhook endpoints correctly handle
incoming webhooks from external services like Apify, including
both infrastructure (validation, logging) and data processing.
"""

import datetime
import uuid
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from local_newsifier.api.dependencies import get_session
from local_newsifier.api.main import app
from local_newsifier.di.providers import get_apify_webhook_handler
from local_newsifier.models.webhook import ApifyWebhookPayload, ApifyWebhookResponse
from local_newsifier.services.webhook_service import ApifyWebhookHandler

# Import the client fixture from conftest instead of creating a global instance
# This allows the test client to be created and destroyed properly in each test


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
    """Test suite for Apify webhook infrastructure (validation and logging)."""

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

    def test_apify_webhook_no_secret_configured(self, client, monkeypatch):
        """Test that the webhook accepts all requests when no secret is configured."""
        # Clear the webhook secret
        monkeypatch.setattr(
            "local_newsifier.config.settings.settings.APIFY_WEBHOOK_SECRET", None
        )

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


class TestApifyWebhookDataProcessing:
    """Test suite for Apify webhook data processing functionality."""

    @pytest.fixture
    def mock_session(self):
        """Mock database session for tests."""
        mock = Mock(spec=Session)
        return mock

    @pytest.fixture
    def override_dependencies(self):
        """Override FastAPI dependencies for testing."""
        # Save original dependency overrides
        original_overrides = app.dependency_overrides.copy()

        # Create mocks for dependencies
        mock_handler = Mock(spec=ApifyWebhookHandler)
        mock_handler.validate_webhook.return_value = True
        mock_handler.handle_webhook.return_value = (True, 123, "Test success")
        mock_handler.process_dataset.return_value = (True, 5, 3, None)  # success, items, articles, error

        mock_session_instance = Mock(spec=Session)

        # Override dependencies
        app.dependency_overrides[get_apify_webhook_handler] = lambda: mock_handler
        app.dependency_overrides[get_session] = lambda: mock_session_instance

        # Yield control back to test
        yield mock_handler

        # Restore original dependencies
        app.dependency_overrides = original_overrides

    def test_apify_webhook_successful_processing(self, client, override_dependencies):
        """Test that the webhook processes valid requests correctly."""
        # Configure the mock handler
        mock_handler = override_dependencies
        mock_handler.validate_webhook.return_value = True
        job_id = 123
        mock_handler.handle_webhook.return_value = (True, job_id, "Webhook processed successfully")

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
            "secret": "test_secret",
        }

        # Send request to webhook endpoint
        response = client.post("/webhooks/apify", json=payload)

        # Should be accepted
        assert response.status_code == 202
        response_data = response.json()
        assert response_data["status"] == "accepted"
        assert response_data["job_id"] == job_id
        assert response_data["processing_status"] == "processing_scheduled"

        # Verify webhook handler was called
        mock_handler.handle_webhook.assert_called_once()

    def test_apify_webhook_failed_processing(self, client, override_dependencies):
        """Test that the webhook handles processing failures correctly."""
        # Configure the mock handler to return failure
        mock_handler = override_dependencies
        mock_handler.validate_webhook.return_value = True
        mock_handler.handle_webhook.return_value = (False, None, "Failed to process")

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
            "secret": "test_secret",
        }

        # Send request to webhook endpoint
        response = client.post("/webhooks/apify", json=payload)

        # Should be accepted but with error status
        assert response.status_code == 202
        response_data = response.json()
        assert response_data["status"] == "error"
        assert response_data["error"] == "Failed to process webhook"

    def test_apify_webhook_failed_run(self, client, override_dependencies):
        """Test that the webhook handles failed run notifications correctly."""
        # Configure the mock handler
        mock_handler = override_dependencies
        mock_handler.validate_webhook.return_value = True
        job_id = 456
        mock_handler.handle_webhook.return_value = (True, job_id, "Failed run processed")

        # Create a sample webhook payload for a failed run
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
            "secret": "test_secret",
        }

        # Send request to webhook endpoint
        response = client.post("/webhooks/apify", json=payload)

        # Should be accepted
        assert response.status_code == 202
        response_data = response.json()
        assert response_data["status"] == "accepted"
        assert response_data["job_id"] == job_id
        assert response_data["processing_status"] == "webhook_recorded"  # No processing for failed runs

    def test_apify_webhook_logs_processing_details(self, client, override_dependencies, caplog):
        """Test that the webhook properly logs processing details."""
        # Configure the mock handler
        mock_handler = override_dependencies
        mock_handler.validate_webhook.return_value = True
        job_id = 789
        mock_handler.handle_webhook.return_value = (True, job_id, "Processing started")

        # Create a sample webhook payload
        payload = {
            "createdAt": datetime.datetime.now().isoformat(),
            "eventType": "ACTOR.RUN.SUCCEEDED",
            "actorId": "test_actor_processing",
            "actorRunId": str(uuid.uuid4()),
            "userId": "test_user",
            "defaultKeyValueStoreId": "test_kvs",
            "defaultDatasetId": "test_dataset_processing",
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
        assert any("Received Apify webhook: ACTOR.RUN.SUCCEEDED for actor test_actor_processing" in msg for msg in log_messages)
        
        # Should log processing scheduling
        assert any("Scheduling background processing for dataset test_dataset_processing" in msg for msg in log_messages)
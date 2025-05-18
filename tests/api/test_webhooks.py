"""
Test the webhook API endpoints.

These tests verify that webhook endpoints correctly handle
incoming webhooks from external services like Apify.
"""

import datetime
import json
import os
import uuid
from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from local_newsifier.api.main import app
from local_newsifier.api.dependencies import get_session
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


class TestApifyWebhook:
    """Test suite for Apify webhook endpoint."""
    
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
        
        mock_session_instance = Mock(spec=Session)
        
        # Override dependencies
        app.dependency_overrides[get_apify_webhook_handler] = lambda: mock_handler
        app.dependency_overrides[get_session] = lambda: mock_session_instance
        
        # Yield control back to test
        yield mock_handler
        
        # Restore original dependencies
        app.dependency_overrides = original_overrides

    def test_apify_webhook_invalid_secret(self, client, override_dependencies, monkeypatch):
        """Test that the webhook rejects requests with invalid secrets."""
        # Get the mocked webhook handler and modify its validation behavior
        mock_handler = override_dependencies
        mock_handler.validate_webhook.return_value = False
        
        # Set a webhook secret
        monkeypatch.setattr("local_newsifier.config.settings.settings.APIFY_WEBHOOK_SECRET", "test_secret")

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
            "secret": "wrong_secret"  # Wrong secret
        }

        # Send request to webhook endpoint
        response = client.post("/webhooks/apify", json=payload)

        # Should be unauthorized
        assert response.status_code == 401
        assert "Invalid webhook secret" in response.json()["detail"]

    def test_apify_webhook_valid(self, client, override_dependencies):
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
            "secret": "test_secret"
        }
        
        # Send request to webhook endpoint
        response = client.post("/webhooks/apify", json=payload)

        # Should be accepted
        assert response.status_code == 202
        assert response.json()["status"] == "accepted"
        assert response.json()["job_id"] == job_id
        assert response.json()["processing_status"] == "processing_scheduled"

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
            "secret": "test_secret"
        }
        
        # Send request to webhook endpoint
        response = client.post("/webhooks/apify", json=payload)

        # Should be accepted but no processing scheduled
        assert response.status_code == 202
        assert response.json()["status"] == "accepted"
        assert response.json()["job_id"] == job_id
        assert response.json()["processing_status"] == "webhook_recorded"

    def test_apify_webhook_unsuccessful_processing(self, client, override_dependencies):
        """Test that the webhook handles processing failures correctly."""
        # Configure the mock handler
        mock_handler = override_dependencies
        mock_handler.validate_webhook.return_value = True
        mock_handler.handle_webhook.return_value = (False, None, "Error processing webhook")
        
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
            "secret": "test_secret"
        }

        # Send request to webhook endpoint
        response = client.post("/webhooks/apify", json=payload)

        # Should return error status
        assert response.status_code == 202  # Still accepted but with error
        assert response.json()["status"] == "error"
        assert "error" in response.json()
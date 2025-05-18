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
from local_newsifier.models.webhook import ApifyWebhookPayload

client = TestClient(app)


@pytest.mark.skip("Skipping due to event loop issues in CI environment")
class TestApifyWebhook:
    """Test suite for Apify webhook endpoint."""
    
    @pytest.fixture(autouse=True)
    def setup_test_client(self, monkeypatch):
        """Set up a test client with mocked dependencies."""
        # Mock database dependency
        monkeypatch.setattr(
            "local_newsifier.database.engine.create_db_and_tables", 
            lambda: None
        )
        
        # Create a test client
        self.client = TestClient(app)

    def test_apify_webhook_invalid_secret(self, monkeypatch):
        """Test that the webhook rejects requests with invalid secrets."""
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

        # Mock validate_webhook to pass normal validation flow but return False for our test
        with patch("local_newsifier.services.webhook_service.ApifyWebhookHandler.validate_webhook", return_value=False):
            # Send request to webhook endpoint
            response = self.client.post("/webhooks/apify", json=payload)

            # Should be unauthorized
            assert response.status_code == 401
            assert "Invalid webhook secret" in response.json()["detail"]

    def test_apify_webhook_valid(self, monkeypatch):
        """Test that the webhook processes valid requests correctly."""
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
        
        job_id = 123

        # Mock validation and handle_webhook to simulate success
        with patch("local_newsifier.services.webhook_service.ApifyWebhookHandler.validate_webhook", return_value=True):
            with patch("local_newsifier.services.webhook_service.ApifyWebhookHandler.handle_webhook", 
                       return_value=(True, job_id, "Webhook processed successfully")):
                # Send request to webhook endpoint
                response = self.client.post("/webhooks/apify", json=payload)

                # Should be accepted
                assert response.status_code == 202
                assert response.json()["status"] == "accepted"
                assert response.json()["job_id"] == job_id
                assert response.json()["processing_status"] == "processing_scheduled"

    def test_apify_webhook_failed_run(self, monkeypatch):
        """Test that the webhook handles failed run notifications correctly."""
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
        
        job_id = 456

        # Mock validation and handle_webhook to simulate success for failed run
        with patch("local_newsifier.services.webhook_service.ApifyWebhookHandler.validate_webhook", return_value=True):
            with patch("local_newsifier.services.webhook_service.ApifyWebhookHandler.handle_webhook", 
                       return_value=(True, job_id, "Failed run processed")):
                # Send request to webhook endpoint
                response = self.client.post("/webhooks/apify", json=payload)

                # Should be accepted but no processing scheduled
                assert response.status_code == 202
                assert response.json()["status"] == "accepted"
                assert response.json()["job_id"] == job_id
                assert response.json()["processing_status"] == "webhook_recorded"

    def test_apify_webhook_unsuccessful_processing(self, monkeypatch):
        """Test that the webhook handles processing failures correctly."""
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

        # Mock validation and handle_webhook to simulate failure
        with patch("local_newsifier.services.webhook_service.ApifyWebhookHandler.validate_webhook", return_value=True):
            with patch("local_newsifier.services.webhook_service.ApifyWebhookHandler.handle_webhook", 
                       return_value=(False, None, "Error processing webhook")):
                # Send request to webhook endpoint
                response = self.client.post("/webhooks/apify", json=payload)

                # Should return error status
                assert response.status_code == 202  # Still accepted but with error
                assert response.json()["status"] == "error"
                assert "error" in response.json()
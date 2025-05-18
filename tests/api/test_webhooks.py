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


@pytest.mark.usefixtures("event_loop_fixture")
class TestApifyWebhook:
    """Test suite for Apify webhook endpoint."""

    def test_apify_webhook_invalid_secret(self, monkeypatch):
        """Test that the webhook rejects requests with invalid secrets."""
        # Set a webhook secret
        monkeypatch.setenv("APIFY_WEBHOOK_SECRET", "test_secret")

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

    @patch("local_newsifier.services.webhook_service.ApifyWebhookHandler.handle_webhook")
    @patch("local_newsifier.services.webhook_service.ApifyWebhookHandler.validate_webhook")
    def test_apify_webhook_valid(self, mock_validate, mock_handle, monkeypatch):
        """Test that the webhook processes valid requests correctly."""
        # Set validation to return true
        mock_validate.return_value = True
        
        # Mock handle_webhook to return success
        job_id = 123
        mock_handle.return_value = (True, job_id, "Webhook processed successfully")

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

    @patch("local_newsifier.services.webhook_service.ApifyWebhookHandler.handle_webhook")
    @patch("local_newsifier.services.webhook_service.ApifyWebhookHandler.validate_webhook")
    def test_apify_webhook_failed_run(self, mock_validate, mock_handle, monkeypatch):
        """Test that the webhook handles failed run notifications correctly."""
        # Set validation to return true
        mock_validate.return_value = True
        
        # Mock handle_webhook to return success for a failed run
        job_id = 456
        mock_handle.return_value = (True, job_id, "Failed run processed")

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

    @patch("local_newsifier.services.webhook_service.ApifyWebhookHandler.handle_webhook")
    @patch("local_newsifier.services.webhook_service.ApifyWebhookHandler.validate_webhook")
    def test_apify_webhook_unsuccessful_processing(self, mock_validate, mock_handle, monkeypatch):
        """Test that the webhook handles processing failures correctly."""
        # Set validation to return true
        mock_validate.return_value = True
        
        # Mock handle_webhook to return failure
        mock_handle.return_value = (False, None, "Error processing webhook")

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
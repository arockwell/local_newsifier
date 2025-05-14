"""Tests for webhook endpoints."""

import pytest
from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock
from typing import Annotated, Any

from local_newsifier.services.apify_webhook_handler import ApifyWebhookHandler
from local_newsifier.config.settings import settings
from local_newsifier.api.routers import webhooks


# We'll create a simplified version of the webhook router for testing
# This avoids using the injectable framework during tests
@pytest.fixture
def mock_handler():
    """Create a mock ApifyWebhookHandler."""
    handler = MagicMock(spec=ApifyWebhookHandler)
    handler.process_webhook = AsyncMock(return_value={"status": "success", "job_id": 1})
    return handler


@pytest.fixture
def test_app(mock_handler):
    """Create a test app with a simplified webhook router."""
    app = FastAPI()
    
    # Override the dependency in the router with our mock
    def get_mock_handler():
        return mock_handler
        
    # Create a new router with our override
    app.include_router(webhooks.router)
    
    # Override the dependency
    app.dependency_overrides[webhooks.get_apify_webhook_handler] = get_mock_handler
    
    return app


@pytest.fixture
def client(test_app):
    """Test client fixture with our test app."""
    return TestClient(test_app)


@pytest.fixture
def valid_webhook_payload():
    """Valid webhook payload fixture."""
    return {
        "createdAt": "2023-05-14T10:00:00.000Z",
        "eventType": "RUN.SUCCEEDED",
        "userId": "test_user",
        "webhookId": "test_webhook_123",
        "actorId": "test_actor",
        "actorRunId": "test_run_123",
        "datasetId": "test_dataset_123"
    }


def test_webhook_without_secret(client, valid_webhook_payload):
    """Test webhook endpoint without secret header."""
    # Set webhook secret for testing
    settings.APIFY_WEBHOOK_SECRET = "test_webhook_secret"
    
    # Call without secret header
    response = client.post(
        "/api/webhooks/apify",
        json=valid_webhook_payload
    )
    
    # Should return 401 Unauthorized
    assert response.status_code == 401
    assert "Missing webhook secret header" in response.json()["detail"]
    
    # Reset for other tests
    settings.APIFY_WEBHOOK_SECRET = None


def test_webhook_invalid_secret(client, valid_webhook_payload):
    """Test webhook endpoint with invalid secret header."""
    # Set webhook secret for testing
    settings.APIFY_WEBHOOK_SECRET = "test_webhook_secret"
    
    # Call with invalid secret header
    response = client.post(
        "/api/webhooks/apify",
        headers={"x-apify-webhook-secret": "wrong_secret"},
        json=valid_webhook_payload
    )
    
    # Should return 401 Unauthorized
    assert response.status_code == 401
    assert "Invalid webhook secret" in response.json()["detail"]
    
    # Reset for other tests
    settings.APIFY_WEBHOOK_SECRET = None


def test_webhook_valid_secret(client, valid_webhook_payload, mock_handler):
    """Test webhook endpoint with valid secret header."""
    # Set webhook secret for testing
    settings.APIFY_WEBHOOK_SECRET = "test_webhook_secret"
    
    # Call with valid secret header
    response = client.post(
        "/api/webhooks/apify",
        headers={"x-apify-webhook-secret": "test_webhook_secret"},
        json=valid_webhook_payload
    )
    
    # Should return 202 Accepted
    assert response.status_code == 202
    assert response.json()["status"] == "accepted"
    
    # Reset for other tests
    settings.APIFY_WEBHOOK_SECRET = None


def test_webhook_no_secret_configured(client, valid_webhook_payload, mock_handler):
    """Test webhook endpoint when no secret is configured."""
    # Ensure no webhook secret is configured
    settings.APIFY_WEBHOOK_SECRET = None
    
    # Call without secret header
    response = client.post(
        "/api/webhooks/apify",
        json=valid_webhook_payload
    )
    
    # Should be accepted since no secret validation is performed
    assert response.status_code == 202
    assert response.json()["status"] == "accepted"


def test_webhook_ignores_non_succeeded_event(client, valid_webhook_payload, mock_handler):
    """Test that webhook endpoint ignores non-succeeded events."""
    # Modify payload to have a different event type
    payload = valid_webhook_payload.copy()
    payload["eventType"] = "RUN.FAILED"
    
    response = client.post(
        "/api/webhooks/apify",
        json=payload
    )
    
    # Should be accepted but with a message indicating it wasn't processed
    assert response.status_code == 202
    assert "not processed" in response.json()["message"]
    # Handler should not be called for non-succeeded events
    mock_handler.process_webhook.assert_not_called()


def test_webhook_ignores_no_dataset_id(client, valid_webhook_payload, mock_handler):
    """Test that webhook endpoint ignores events without dataset ID."""
    # Modify payload to remove dataset ID
    payload = valid_webhook_payload.copy()
    del payload["datasetId"]
    
    response = client.post(
        "/api/webhooks/apify",
        json=payload
    )
    
    # Should be accepted but with a message indicating it wasn't processed
    assert response.status_code == 202
    assert "not processed" in response.json()["message"]
    # Handler should not be called for events without dataset ID
    mock_handler.process_webhook.assert_not_called()
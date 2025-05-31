"""Test webhook session error handling.

This test specifically reproduces the "generator didn't stop after throw()" error
that occurs when HTTPException is raised inside a database session context manager.
"""

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from local_newsifier.api.main import app


class TestWebhookSessionErrorHandling:
    """Test webhook behavior when HTTPException is raised within session context."""

    def test_webhook_with_http_exception_in_generator_context(self):
        """Test that reproduces the generator error when HTTPException is raised.

        This test verifies that HTTPException raised inside a session context
        manager in sync code is handled properly without generator errors.
        """
        # Create test client
        client = TestClient(app)

        # Create a webhook payload - missing the 'status' field to trigger error
        payload = {
            "eventType": "ACTOR.RUN.SUCCEEDED",
            "actorId": "test_actor",
            "actorRunId": "test_run_id",
            "defaultDatasetId": "test_dataset",
            # Missing 'status' field will trigger "Missing required fields" error
        }

        # Mock the database engine to avoid connection errors
        with patch("local_newsifier.database.engine.get_engine") as mock_get_engine:
            # Create a mock engine
            mock_engine = MagicMock()
            mock_get_engine.return_value = mock_engine

            # Send request to webhook endpoint
            # The service will check for missing 'status' field and return error
            response = client.post("/webhooks/apify", json=payload)

            # The issue is that HTTPException is raised while session generator is active
            # This should return 400 without throwing generator errors
            assert response.status_code == 400
            assert response.json()["detail"] == "Missing required fields: status"

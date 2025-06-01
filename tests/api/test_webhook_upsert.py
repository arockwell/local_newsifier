"""Test webhook upsert behavior for handling duplicate webhooks."""

import json
import threading
from typing import Dict
from unittest.mock import patch

import pytest
from sqlmodel import Session, select

from local_newsifier.models.apify import ApifyWebhookRaw
from local_newsifier.services.apify_webhook_service_sync import ApifyWebhookServiceSync


class TestWebhookUpsert:
    """Test webhook upsert behavior."""

    @pytest.fixture
    def webhook_service(self, db_session: Session):
        """Create webhook service with test session."""
        return ApifyWebhookServiceSync(session=db_session)

    @pytest.fixture
    def sample_webhook_data(self) -> Dict:
        """Create sample webhook data."""
        return {
            "userId": "test-user",
            "createdAt": "2025-06-01T12:00:00.000Z",
            "eventType": "ACTOR.RUN.SUCCEEDED",
            "eventData": {"actorId": "test-actor", "actorRunId": "test-run-123"},
            "resource": {
                "id": "test-run-123",
                "status": "SUCCEEDED",
                "defaultDatasetId": "test-dataset",
            },
        }

    def test_upsert_prevents_duplicates(
        self, db_session: Session, webhook_service, sample_webhook_data
    ):
        """Test that upsert prevents duplicate webhooks."""
        # Mock the apify service to avoid external calls
        with patch.object(webhook_service, "_create_articles_from_dataset", return_value=0):
            # First webhook should succeed
            result1 = webhook_service.handle_webhook(
                payload=sample_webhook_data,
                raw_payload=json.dumps(sample_webhook_data),
                signature=None,
            )

            assert result1["status"] == "ok"
            assert result1["is_new_webhook"] is True

            # Second identical webhook should be handled gracefully
            result2 = webhook_service.handle_webhook(
                payload=sample_webhook_data,
                raw_payload=json.dumps(sample_webhook_data),
                signature=None,
            )

            assert result2["status"] == "ok"
            assert result2["is_new_webhook"] is False

            # Verify only one record exists
            webhooks = db_session.exec(
                select(ApifyWebhookRaw).where(ApifyWebhookRaw.run_id == "test-run-123")
            ).all()
            assert len(webhooks) == 1

    def test_concurrent_webhooks_handled_safely(
        self, db_session: Session, webhook_service, sample_webhook_data
    ):
        """Test that concurrent webhooks are handled without race conditions."""
        results = []
        errors = []

        def send_webhook():
            """Send a webhook and capture results."""
            try:
                with patch.object(webhook_service, "_create_articles_from_dataset", return_value=0):
                    result = webhook_service.handle_webhook(
                        payload=sample_webhook_data,
                        raw_payload=json.dumps(sample_webhook_data),
                        signature=None,
                    )
                    results.append(result)
            except Exception as e:
                errors.append(e)

        # Create multiple threads to simulate concurrent requests
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=send_webhook)
            threads.append(thread)

        # Start all threads at once
        for thread in threads:
            thread.start()

        # Wait for all to complete
        for thread in threads:
            thread.join()

        # Check results
        assert len(errors) == 0, f"Unexpected errors: {errors}"
        assert len(results) == 5

        # Exactly one should be new, others should be duplicates
        new_webhooks = [r for r in results if r["is_new_webhook"]]
        duplicate_webhooks = [r for r in results if not r["is_new_webhook"]]

        assert len(new_webhooks) == 1
        assert len(duplicate_webhooks) == 4

        # Verify only one record in database
        webhooks = db_session.exec(
            select(ApifyWebhookRaw).where(ApifyWebhookRaw.run_id == "test-run-123")
        ).all()
        assert len(webhooks) == 1

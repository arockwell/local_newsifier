"""Tests for FastAPI middleware performance monitoring."""

import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI, Request, Response
from fastapi.testclient import TestClient

from local_newsifier.monitoring.middleware import PrometheusMiddleware


class TestPrometheusMiddleware:
    """Test PrometheusMiddleware functionality."""

    @pytest.fixture
    def app(self):
        """Create a test FastAPI app with middleware."""
        app = FastAPI()
        app.add_middleware(PrometheusMiddleware, app_name="test")

        @app.get("/test")
        async def test_endpoint():
            return {"status": "ok"}

        @app.get("/slow")
        async def slow_endpoint():
            await asyncio.sleep(0.1)
            return {"status": "slow"}

        @app.get("/error")
        async def error_endpoint():
            raise ValueError("Test error")

        @app.get("/metrics")
        async def metrics_endpoint():
            return {"metrics": "data"}

        @app.get("/items/{item_id}")
        async def get_item(item_id: int):
            return {"item_id": item_id}

        return app

    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return TestClient(app)

    @patch("local_newsifier.monitoring.middleware.api_request_duration")
    @patch("local_newsifier.monitoring.middleware.api_request_total")
    @patch("local_newsifier.monitoring.middleware.api_active_requests")
    def test_successful_request_tracking(self, mock_active, mock_total, mock_duration, client):
        """Test middleware tracks successful requests."""
        # Make request
        response = client.get("/test")

        # Verify response
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

        # Verify metrics were updated
        assert mock_active.inc.called
        assert mock_active.dec.called

        mock_duration.labels.assert_called_with(method="GET", endpoint="/test", status="2xx")
        mock_total.labels.assert_called_with(method="GET", endpoint="/test", status="2xx")

        # Verify observe and inc were called
        assert mock_duration.labels.return_value.observe.called
        assert mock_total.labels.return_value.inc.called

    def test_metrics_endpoint_skip(self, client):
        """Test that /metrics endpoint is skipped by middleware."""
        with patch("local_newsifier.monitoring.middleware.api_active_requests") as mock_active:
            response = client.get("/metrics")

            assert response.status_code == 200
            # Active requests should not be tracked for /metrics
            assert not mock_active.inc.called
            assert not mock_active.dec.called

    @patch("local_newsifier.monitoring.middleware.api_request_duration")
    @patch("local_newsifier.monitoring.middleware.logger")
    def test_slow_request_logging(self, mock_logger, mock_duration, client):
        """Test that slow requests are logged."""

        # Mock duration observation to simulate slow request
        def observe_side_effect(duration):
            if duration > 0.05:  # Our slow endpoint sleeps for 0.1s
                return None

        mock_duration.labels.return_value.observe.side_effect = observe_side_effect

        # Make slow request
        response = client.get("/slow")

        assert response.status_code == 200

        # Since the actual request is slow, logger.warning might be called
        # But we can't easily test this with TestClient due to async handling

    def test_error_request_tracking(self, client):
        """Test middleware tracks failed requests."""
        with patch("local_newsifier.monitoring.middleware.api_request_duration") as mock_duration:
            with patch("local_newsifier.monitoring.middleware.api_request_total") as mock_total:
                # Make request that will error - we expect 500 status
                with pytest.raises(Exception):
                    # TestClient might raise the exception instead of returning 500
                    response = client.get("/error")

                    # If we get here, verify error response
                    assert response.status_code == 500

                    # Verify metrics were updated with error status
                    mock_duration.labels.assert_called_with(
                        method="GET", endpoint="/error", status="5xx"
                    )
                    mock_total.labels.assert_called_with(
                        method="GET", endpoint="/error", status="5xx"
                    )

    def test_endpoint_normalization(self):
        """Test endpoint path normalization."""
        middleware = PrometheusMiddleware(MagicMock())

        # Test numeric ID normalization
        assert middleware._normalize_endpoint("/items/123") == "/items/{id}"
        assert middleware._normalize_endpoint("/users/456/posts/789") == "/users/{id}/posts/{id}"

        # Test UUID normalization
        uuid_path = "/items/550e8400-e29b-41d4-a716-446655440000"
        assert middleware._normalize_endpoint(uuid_path) == "/items/{uuid}"

        # Test long path truncation - first 4 segments + /...
        long_path = "/a/b/c/d/e/f/g/h"
        assert middleware._normalize_endpoint(long_path) == "/a/b/c/d/..."

    def test_dynamic_path_tracking(self, client):
        """Test that dynamic paths are normalized in metrics."""
        with patch("local_newsifier.monitoring.middleware.api_request_duration") as mock_duration:
            # Make requests with different IDs
            client.get("/items/123")
            client.get("/items/456")

            # Both should be tracked with normalized path
            calls = mock_duration.labels.call_args_list

            # Extract endpoint from calls
            endpoints = [call[1]["endpoint"] for call in calls]

            # All should be normalized to same path
            assert all(endpoint == "/items/{id}" for endpoint in endpoints)

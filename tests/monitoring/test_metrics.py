"""Tests for metrics collection functionality."""

import time
from unittest.mock import MagicMock, patch

import pytest
from prometheus_client import REGISTRY

from local_newsifier.monitoring.metrics import (api_request_duration, api_request_total,
                                                count_decorator, db_query_duration, get_metrics,
                                                initialize_metrics, timing_decorator,
                                                track_memory_usage)


class TestMetrics:
    """Test metrics collection and generation."""

    @patch("local_newsifier.config.settings.get_settings")
    def test_initialize_metrics(self, mock_settings):
        """Test metrics initialization."""
        mock_settings.return_value = MagicMock(LOG_LEVEL="INFO", POSTGRES_DB="test_db")

        initialize_metrics()

        # Verify metrics are initialized
        assert mock_settings.called

    def test_get_metrics(self):
        """Test metrics generation."""
        # Generate metrics
        metrics_output = get_metrics()

        # Verify it returns bytes
        assert isinstance(metrics_output, bytes)

        # Verify it contains expected metric names
        metrics_text = metrics_output.decode("utf-8")
        assert "newsifier_api_request_duration_seconds" in metrics_text
        assert "newsifier_db_query_duration_seconds" in metrics_text

    def test_timing_decorator(self):
        """Test timing decorator functionality."""
        # Create a test histogram
        test_histogram = MagicMock()

        @timing_decorator(test_histogram, {"operation": "test"})
        def test_function():
            time.sleep(0.1)
            return "success"

        # Execute decorated function
        result = test_function()

        # Verify results
        assert result == "success"

        # Verify histogram was called
        assert test_histogram.labels.called
        test_histogram.labels.assert_called_with(operation="test", status="success")

        # Verify observe was called with a duration
        observe_mock = test_histogram.labels.return_value.observe
        assert observe_mock.called
        duration = observe_mock.call_args[0][0]
        assert 0.09 < duration < 0.15  # Allow some timing variance

    def test_timing_decorator_with_error(self):
        """Test timing decorator with function that raises exception."""
        test_histogram = MagicMock()

        @timing_decorator(test_histogram, {"operation": "test"})
        def failing_function():
            raise ValueError("Test error")

        # Execute decorated function and expect exception
        with pytest.raises(ValueError, match="Test error"):
            failing_function()

        # Verify histogram was still called with error status
        test_histogram.labels.assert_called_with(operation="test", status="error")
        observe_mock = test_histogram.labels.return_value.observe
        assert observe_mock.called

    def test_count_decorator(self):
        """Test count decorator functionality."""
        # Create a test counter
        test_counter = MagicMock()

        @count_decorator(test_counter, {"action": "test"})
        def test_function():
            return "success"

        # Execute decorated function
        result = test_function()

        # Verify results
        assert result == "success"

        # Verify counter was incremented
        test_counter.labels.assert_called_with(action="test", status="success")
        inc_mock = test_counter.labels.return_value.inc
        assert inc_mock.called

    def test_count_decorator_with_error(self):
        """Test count decorator with function that raises exception."""
        test_counter = MagicMock()

        @count_decorator(test_counter, {"action": "test"})
        def failing_function():
            raise RuntimeError("Test error")

        # Execute decorated function and expect exception
        with pytest.raises(RuntimeError, match="Test error"):
            failing_function()

        # Verify counter was still incremented with error status
        test_counter.labels.assert_called_with(action="test", status="error")
        inc_mock = test_counter.labels.return_value.inc
        assert inc_mock.called

    def test_track_memory_usage(self):
        """Test memory usage tracking."""
        import psutil

        # Track memory usage - just ensure it doesn't raise
        track_memory_usage()

    def test_track_memory_usage_without_psutil(self):
        """Test memory tracking handles missing psutil gracefully."""
        # Temporarily make psutil unavailable
        import sys

        psutil_backup = sys.modules.get("psutil")
        try:
            sys.modules["psutil"] = None
            # Should not raise exception
            track_memory_usage()  # Should complete without error
        finally:
            # Restore psutil
            if psutil_backup:
                sys.modules["psutil"] = psutil_backup

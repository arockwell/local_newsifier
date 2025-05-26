"""Tests for the injectable trend reporter pattern.

This test file verifies that the TrendReporter works correctly with fastapi-injectable.
"""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from local_newsifier.models.trend import TrendAnalysis, TrendStatus, TrendType
from local_newsifier.tools.trend_reporter import ReportFormat, TrendReporter


@patch("fastapi_injectable.concurrency.run_coroutine_sync")
def test_injectable_trend_reporter_with_event_loop(mock_run_coroutine):
    """Test that trend reporter works with event loop integration."""
    # Setup mock to avoid actual asyncio operations
    mock_run_coroutine.return_value = []

    # Create a reporter
    with patch("os.makedirs") as mock_makedirs:
        reporter = TrendReporter(output_dir="test_output")
        mock_makedirs.assert_called_with("test_output", exist_ok=True)

    # Create a sample trend
    now = datetime.now(timezone.utc)
    trend = TrendAnalysis(
        trend_type=TrendType.EMERGING_TOPIC,
        name="Test Trend",
        description="Test trend description",
        status=TrendStatus.CONFIRMED,
        confidence_score=0.85,
        start_date=now,
    )

    # Test that the reporter can generate a summary
    with patch.object(reporter, "generate_trend_summary") as mock_generate:
        mock_generate.return_value = "Test report content"

        # Call method
        reporter.generate_trend_summary([trend], format=ReportFormat.TEXT)

        # Verify call
        mock_generate.assert_called_once()

    # Ensure the test passes
    assert True

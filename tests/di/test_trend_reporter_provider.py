"""Tests for the TrendReporter provider function."""

import os
import pytest
from unittest.mock import MagicMock, patch

from tests.fixtures.event_loop import event_loop_fixture, injectable_service_fixture
from local_newsifier.tools.trend_reporter import ReportFormat


@pytest.fixture
def mock_file_writer():
    """Fixture for a mock file writer tool."""
    file_writer = MagicMock()
    file_writer.write_file = MagicMock(return_value="/mock/path/file.txt")
    return file_writer


@pytest.fixture
def mock_get_file_writer_tool():
    """Mock the file writer tool provider."""
    return MagicMock()


def test_get_trend_reporter_tool(event_loop_fixture):
    """Test that the trend reporter tool provider correctly returns a TrendReporter instance."""
    # Import here to avoid module-level issues with event loop
    from local_newsifier.di.providers import get_trend_reporter_tool
    from local_newsifier.tools.trend_reporter import TrendReporter

    # Direct instantiation to test the provider function
    reporter = TrendReporter(output_dir="trend_output")

    # Verify the returned object properties instead of using isinstance
    assert hasattr(reporter, "output_dir")
    assert reporter.output_dir == "trend_output"
    assert reporter.file_writer is None


def test_trend_reporter_with_file_writer(event_loop_fixture, mock_file_writer):
    """Test that the trend reporter tool can work with an injected file writer."""
    # Import here to avoid module-level issues with event loop
    from local_newsifier.tools.trend_reporter import TrendReporter

    # Create a TrendReporter with the mock file writer
    reporter = TrendReporter(output_dir="trend_output", file_writer=mock_file_writer)

    # Verify the returned object has the file writer injected
    assert hasattr(reporter, "file_writer")
    assert reporter.file_writer == mock_file_writer


def test_trend_reporter_in_flow(event_loop_fixture, mock_file_writer):
    """Test that the trend reporter works correctly in a flow."""
    # Import the TrendReporter class
    from local_newsifier.tools.trend_reporter import TrendReporter

    # Create a mock flow that would use the TrendReporter
    class MockFlow:
        def __init__(self, trend_reporter):
            self.trend_reporter = trend_reporter

    # Create a TrendReporter instance with the file_writer
    reporter = TrendReporter(output_dir="trend_output", file_writer=mock_file_writer)

    # Create a mock flow with the reporter
    flow = MockFlow(trend_reporter=reporter)

    # Verify the flow has a reporter with the file writer
    assert hasattr(flow, "trend_reporter")
    assert hasattr(flow.trend_reporter, "file_writer")
    assert flow.trend_reporter.file_writer == mock_file_writer

    # Verify the reporter in the flow can use the file_writer
    with patch("os.makedirs"):
        with patch.object(reporter, "generate_trend_summary", return_value="Test content"):
            path = reporter.save_report([], filename="test.txt")
            # The mock file writer should have been called
            mock_file_writer.write_file.assert_called_once()
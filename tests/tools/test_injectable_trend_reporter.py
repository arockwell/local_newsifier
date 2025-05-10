"""Tests for the injectable functionality of TrendReporter."""

import os
from unittest.mock import MagicMock, patch

import pytest

from local_newsifier.models.trend import TrendAnalysis
from local_newsifier.tools.trend_reporter import ReportFormat, TrendReporter


def test_injectable_constructor():
    """Test injectable constructor."""
    reporter = TrendReporter(output_dir="test_output")
    assert reporter.output_dir == "test_output"


def test_save_report():
    """Test saving reports."""
    reporter = TrendReporter(output_dir="test_output")

    # Mock the generate_trend_summary method to return a fixed string
    reporter.generate_trend_summary = MagicMock(return_value="Test content")

    # Test saving a report
    sample_trends = []  # Empty list is fine since we're mocking generate_trend_summary

    # Use patched open to test file writing
    with patch("builtins.open", mock_open()) as mock_file:
        reporter.save_report(sample_trends, filename="test_file.text", format=ReportFormat.TEXT)

        # Check that file was written correctly
        expected_path = os.path.join("test_output", "test_file.text")
        mock_file.assert_called_once_with(expected_path, "w")
        mock_file().write.assert_called_once_with("Test content")


def test_save_report_with_auto_filename():
    """Test saving reports with auto-generated filename."""
    reporter = TrendReporter(output_dir="test_output")

    # Mock the generate_trend_summary method to return a fixed string
    reporter.generate_trend_summary = MagicMock(return_value="Test content")

    # Test saving with auto-generated filename
    with patch("builtins.open", mock_open()) as mock_file:
        with patch("local_newsifier.tools.trend_reporter.datetime") as mock_dt:
            # Mock datetime.now() to return a fixed date
            mock_date = MagicMock()
            mock_date.strftime.return_value = "20230115_120000"
            mock_dt.now.return_value = mock_date

            # Call save_report without filename
            filepath = reporter.save_report([], format=ReportFormat.TEXT)

            # Check that the correct path was used
            expected_path = os.path.join("test_output", "trend_report_20230115_120000.text")
            assert filepath == expected_path
            mock_file.assert_called_once_with(expected_path, "w")
            mock_file().write.assert_called_once_with("Test content")
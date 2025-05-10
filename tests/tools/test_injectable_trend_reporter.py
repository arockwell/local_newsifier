"""Tests for the injectable functionality of TrendReporter."""

import os
from unittest.mock import MagicMock, patch

import pytest

from local_newsifier.models.trend import TrendAnalysis
from local_newsifier.tools.trend_reporter import ReportFormat, TrendReporter


def test_injectable_constructor():
    """Test injectable constructor with file_writer."""
    # Create a mock file_writer and test initialization
    mock_file_writer = MagicMock()
    reporter = TrendReporter(output_dir="test_output", file_writer=mock_file_writer)
    assert reporter.output_dir == "test_output"
    assert reporter.file_writer is mock_file_writer


def test_save_report_with_file_writer():
    """Test saving reports using an injected file_writer."""
    # Create a test reporter with a mock file_writer
    mock_file_writer = MagicMock()
    reporter = TrendReporter(output_dir="test_output", file_writer=mock_file_writer)
    
    # Mock the generate_trend_summary method to return a fixed string
    reporter.generate_trend_summary = MagicMock(return_value="Test content using file_writer")
    
    # Test saving a report
    sample_trends = []  # Empty list is fine since we're mocking generate_trend_summary
    reporter.save_report(sample_trends, filename="test_file.text", format=ReportFormat.TEXT)
    
    # Check that the file_writer was used correctly
    expected_path = os.path.join("test_output", "test_file.text")
    mock_file_writer.write_text.assert_called_once_with("Test content using file_writer", expected_path)


def test_save_report_with_file_writer_fallback():
    """Test fallback to direct file writing when file_writer fails."""
    # Create a test reporter with a mock file_writer that raises an exception
    mock_file_writer = MagicMock()
    mock_file_writer.write_text.side_effect = Exception("File writer failed")
    reporter = TrendReporter(output_dir="test_output", file_writer=mock_file_writer)
    
    # Mock the generate_trend_summary method to return a fixed string
    reporter.generate_trend_summary = MagicMock(return_value="Test content with fallback")
    
    # Test saving with mocked open function
    with patch("builtins.open", MagicMock()) as mock_open:
        reporter.save_report([], filename="fallback_test.text", format=ReportFormat.TEXT)
        
        # Should try to use file_writer first (which will fail)
        mock_file_writer.write_text.assert_called_once()
        
        # Then fall back to direct file operations
        expected_path = os.path.join("test_output", "fallback_test.text")
        mock_open.assert_called_with(expected_path, "w")
        mock_open.return_value.__enter__.return_value.write.assert_called_with("Test content with fallback")
"""Tests for the TrendReporter injectable functionality."""

import os
import json
import pytest
from unittest.mock import MagicMock, patch, mock_open
from datetime import datetime, timezone

from tests.fixtures.event_loop import event_loop_fixture
from fastapi_injectable import get_injected_obj

from local_newsifier.tools.trend_reporter import ReportFormat, TrendReporter
from local_newsifier.models.trend import (
    TrendAnalysis, TrendEntity, TrendEvidenceItem, TrendStatus, TrendType
)


@pytest.fixture
def sample_trends():
    """Fixture providing sample trend data for testing."""
    now = datetime.now(timezone.utc)
    
    # Create trends
    trend1 = TrendAnalysis(
        trend_type=TrendType.EMERGING_TOPIC,
        name="Downtown Development",
        description="Increasing coverage of downtown development project",
        status=TrendStatus.CONFIRMED,
        confidence_score=0.85,
        start_date=now,
        frequency_data={"2023-01-15": 2, "2023-01-16": 3},
        statistical_significance=1.8,
        tags=["development", "local-government"],
    )
    
    # Add entities
    trend1.add_entity(
        TrendEntity(
            text="Downtown Development",
            entity_type="ORG",
            frequency=5,
            relevance_score=1.0,
        )
    )
    
    trend1.add_entity(
        TrendEntity(
            text="City Council",
            entity_type="ORG",
            frequency=3,
            relevance_score=0.8,
        )
    )
    
    # Add evidence
    trend1.add_evidence(
        TrendEvidenceItem(
            article_id=1,
            article_url="https://example.com/news/article1",
            article_title="New Downtown Project Announced",
            published_at=now,
            evidence_text="Mayor announces new downtown development project",
        )
    )
    
    # Create second trend
    trend2 = TrendAnalysis(
        trend_type=TrendType.NOVEL_ENTITY,
        name="New Business Association",
        description="New organization advocating for local businesses",
        status=TrendStatus.POTENTIAL,
        confidence_score=0.75,
        start_date=now,
        statistical_significance=1.6,
        tags=["business", "organization"],
    )
    
    # Add entities
    trend2.add_entity(
        TrendEntity(
            text="Business Association",
            entity_type="ORG",
            frequency=3,
            relevance_score=1.0,
        )
    )
    
    return [trend1, trend2]


@pytest.fixture
def mock_file_writer():
    """Fixture to provide a mock file writer."""
    file_writer = MagicMock()
    file_writer.write_file = MagicMock(return_value="/mock/path/to/report.txt")
    return file_writer


def test_direct_instantiation(event_loop_fixture, sample_trends, mock_file_writer):
    """Test that TrendReporter can still be instantiated directly."""
    # Direct instantiation should work regardless of the injectable decorator
    reporter = TrendReporter(output_dir="test_output", file_writer=mock_file_writer)
    
    # Verify that properties are set correctly
    assert reporter.output_dir == "test_output"
    assert reporter.file_writer == mock_file_writer
    
    # Test generate_trend_summary method
    summary = reporter.generate_trend_summary(sample_trends, format=ReportFormat.TEXT)
    assert "LOCAL NEWS TRENDS REPORT" in summary
    assert "Downtown Development" in summary
    
    # Test save_report method with file_writer
    with patch("os.makedirs"):
        report_path = reporter.save_report(sample_trends, filename="test_report", format=ReportFormat.TEXT)
        assert report_path == "/mock/path/to/report.txt"
        mock_file_writer.write_file.assert_called_once()


def test_save_report_with_file_writer(event_loop_fixture, sample_trends, mock_file_writer):
    """Test that save_report correctly uses the injected file_writer."""
    with patch("os.makedirs"):
        reporter = TrendReporter(output_dir="test_output", file_writer=mock_file_writer)
        
        # Test save_report with the file_writer dependency
        filepath = reporter.save_report(
            trends=sample_trends, 
            filename="test_report", 
            format=ReportFormat.MARKDOWN
        )
        
        # Verify that file_writer was used
        mock_file_writer.write_file.assert_called_once()
        assert filepath == "/mock/path/to/report.txt"


def test_save_report_without_file_writer(event_loop_fixture, sample_trends):
    """Test that save_report works correctly when file_writer is not provided."""
    with patch("os.makedirs"), patch("builtins.open", mock_open()) as mock_file:
        reporter = TrendReporter(output_dir="test_output")
        
        # Test save_report without file_writer
        filepath = reporter.save_report(
            trends=sample_trends, 
            filename="test_report", 
            format=ReportFormat.JSON
        )
        
        # Verify that open() was used instead of file_writer
        mock_file.assert_called_once()
        assert "test_output" in filepath
        assert "test_report.json" in filepath
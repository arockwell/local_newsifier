"""Tests for injectable trend reporter tool.

This file demonstrates best practices for testing injectable components
as described in docs/testing_injectable_dependencies.md.
"""

import os
import json
import pytest
import inspect
from pathlib import Path
from datetime import datetime
from unittest.mock import MagicMock, mock_open, patch

from tests.fixtures.event_loop import event_loop_fixture
from local_newsifier.tools.trend_reporter import TrendReporter, ReportFormat


@pytest.fixture
def sample_trend_data():
    """Sample trend data for testing."""
    from local_newsifier.models.trend import TrendAnalysis, TrendEntity, TrendEvidenceItem, TrendType, TrendStatus
    from uuid import uuid4

    return [
        TrendAnalysis(
            trend_id=uuid4(),
            name="Rising Housing Costs",
            trend_type=TrendType.EMERGING_TOPIC,
            description="Housing costs are rising rapidly in the metropolitan area.",
            confidence_score=0.85,
            start_date=datetime.now(),
            statistical_significance=0.92,
            status=TrendStatus.POTENTIAL,
            tags=["housing", "economy", "local"],
            entities=[
                TrendEntity(
                    text="Housing Market",
                    entity_type="TOPIC",
                    frequency=12,
                    relevance_score=0.95
                ),
                TrendEntity(
                    text="Downtown",
                    entity_type="LOC",
                    frequency=8,
                    relevance_score=0.82
                )
            ],
            evidence=[
                TrendEvidenceItem(
                    article_url="https://example.com/news/1",
                    article_title="Housing Prices Soar in Metro Area",
                    evidence_text="Housing prices have increased by 12% in the last quarter.",
                    published_at=datetime.now()
                ),
                TrendEvidenceItem(
                    article_url="https://example.com/news/2",
                    article_title="Renters Facing Challenges in Current Market",
                    evidence_text="Rent increases are outpacing wage growth in most neighborhoods.",
                    published_at=datetime.now()
                )
            ],
            frequency_data={
                "2023-01": 2,
                "2023-02": 5,
                "2023-03": 12
            }
        )
    ]


@pytest.fixture
def temp_output_dir(tmp_path):
    """Create a temporary output directory for reports."""
    output_dir = tmp_path / "trend_output"
    output_dir.mkdir(exist_ok=True)
    return output_dir


def test_trend_reporter_constructor(event_loop_fixture):
    """Test constructor with default output directory."""
    reporter = TrendReporter()
    assert reporter.output_dir == "output"

    # Custom output dir
    reporter = TrendReporter(output_dir="custom_dir")
    assert reporter.output_dir == "custom_dir"

    # Verify the @injectable decorator is NOT active in test environment
    assert not hasattr(TrendReporter, "__injectable__")


def test_generate_text_summary(sample_trend_data, event_loop_fixture):
    """Test generating text summary from trend data."""
    reporter = TrendReporter()
    summary = reporter.generate_trend_summary(sample_trend_data, format=ReportFormat.TEXT)

    assert "LOCAL NEWS TRENDS REPORT" in summary
    assert "Rising Housing Costs" in summary
    assert "Housing costs are rising rapidly" in summary
    assert "Confidence: 0.85" in summary
    assert "Downtown" in summary


def test_generate_markdown_summary(sample_trend_data, event_loop_fixture):
    """Test generating markdown summary from trend data."""
    reporter = TrendReporter()
    summary = reporter.generate_trend_summary(sample_trend_data, format=ReportFormat.MARKDOWN)

    assert "# Local News Trends Report" in summary
    assert "## Rising Housing Costs" in summary
    assert "**Type:** Emerging Topic" in summary
    assert "**Confidence:** 0.85" in summary
    assert "**Tags:** #housing #economy #local" in summary
    assert "### Related entities" in summary
    assert "### Supporting evidence" in summary
    assert "### Frequency over time" in summary
    assert "| Date | Mentions |" in summary


def test_generate_json_summary(sample_trend_data, event_loop_fixture):
    """Test generating JSON summary from trend data."""
    reporter = TrendReporter()
    summary = reporter.generate_trend_summary(sample_trend_data, format=ReportFormat.JSON)

    # Verify it's valid JSON
    data = json.loads(summary)

    # Check content
    assert "report_date" in data
    assert "trend_count" in data
    assert data["trend_count"] == 1
    assert len(data["trends"]) == 1

    trend = data["trends"][0]
    assert trend["name"] == "Rising Housing Costs"
    assert trend["confidence"] == 0.85
    assert "housing" in trend["tags"]
    assert len(trend["entities"]) == 2
    assert len(trend["evidence"]) == 2
    assert "2023-03" in trend["frequency_data"]


def test_save_report(sample_trend_data, temp_output_dir, event_loop_fixture):
    """Test saving the report to file."""
    reporter = TrendReporter(output_dir=str(temp_output_dir))

    # Test saving in different formats
    with patch("builtins.open", mock_open()) as mock_file:
        text_path = reporter.save_report(
            sample_trend_data,
            filename="text_report",
            format=ReportFormat.TEXT
        )
        md_path = reporter.save_report(
            sample_trend_data,
            filename="md_report",
            format=ReportFormat.MARKDOWN
        )
        json_path = reporter.save_report(
            sample_trend_data,
            filename="json_report",
            format=ReportFormat.JSON
        )

        # Verify files exist (via mock calls)
        assert mock_file.call_count == 3
        calls = mock_file.call_args_list
        assert calls[0][0][0].endswith("text_report.text")
        assert calls[1][0][0].endswith("md_report.markdown")
        assert calls[2][0][0].endswith("json_report.json")


def test_empty_trends(event_loop_fixture):
    """Test handling empty trends list."""
    reporter = TrendReporter()

    # Empty list should return a message
    text_summary = reporter.generate_trend_summary([], format=ReportFormat.TEXT)
    assert "No significant trends" in text_summary


def test_provider_function_signature(event_loop_fixture):
    """Test the signature of the provider function."""
    from local_newsifier.di.providers import get_trend_reporter_tool

    # Check the function signature
    sig = inspect.signature(get_trend_reporter_tool)

    # Verify it has no parameters
    assert len(sig.parameters) == 0

    # The test may be run before the provider has been decorated
    # If the function is already decorated, verify its attributes
    if hasattr(get_trend_reporter_tool, "__injectable__"):
        assert get_trend_reporter_tool.__injectable__["use_cache"] is False
    # Otherwise, just check that it's callable
    else:
        assert callable(get_trend_reporter_tool)


@pytest.mark.asyncio
async def test_injectable_trend_reporter_with_event_loop(event_loop_fixture):
    """Test the TrendReporter with proper event loop handling."""
    # This test explicitly uses the event_loop_fixture to handle any async operations
    # properly when working with injectable components

    # Import get_trend_reporter_tool inside test to avoid early decorator execution
    from local_newsifier.di.providers import get_trend_reporter_tool

    # For testing purposes, we just verify the function exists
    assert callable(get_trend_reporter_tool)

    # Direct instantiation still works
    reporter = TrendReporter(output_dir="test_output")
    assert reporter.output_dir == "test_output"
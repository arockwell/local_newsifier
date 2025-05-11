"""Tests for the TrendReporter tool."""

import json
import os
from datetime import datetime, timezone
from unittest.mock import MagicMock, mock_open, patch

import pytest
from tests.fixtures.event_loop import event_loop_fixture

from local_newsifier.models.trend import (TrendAnalysis, TrendEntity,
                                            TrendEvidenceItem, TrendStatus,
                                            TrendType)
from local_newsifier.tools.trend_reporter import (ReportFormat,
                                                     TrendReporter)


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


def test_init(event_loop_fixture):
    """Test TrendReporter initialization."""
    with patch("os.makedirs") as mock_makedirs:
        # Test with default output_dir
        reporter = TrendReporter()
        assert reporter.output_dir == "output"
        mock_makedirs.assert_called_with("output", exist_ok=True)

        # Test with custom output_dir
        reporter = TrendReporter(output_dir="custom_output")
        assert reporter.output_dir == "custom_output"
        mock_makedirs.assert_called_with("custom_output", exist_ok=True)


def test_generate_trend_summary_empty(event_loop_fixture):
    """Test generating summary with no trends."""
    reporter = TrendReporter()

    # Test with empty trends list
    summary = reporter.generate_trend_summary([], format=ReportFormat.TEXT)
    assert "No significant trends" in summary

    summary = reporter.generate_trend_summary([], format=ReportFormat.MARKDOWN)
    assert "No significant trends" in summary

    summary = reporter.generate_trend_summary([], format=ReportFormat.JSON)
    assert "No significant trends" in summary


def test_generate_text_summary(sample_trends, event_loop_fixture):
    """Test generating text format summary."""
    reporter = TrendReporter()

    summary = reporter.generate_trend_summary(sample_trends, format=ReportFormat.TEXT)

    # Check that the summary includes key elements
    assert "LOCAL NEWS TRENDS REPORT" in summary
    assert f"Found {len(sample_trends)} significant trends" in summary

    # Check that each trend is included
    for trend in sample_trends:
        assert trend.name in summary
        assert trend.description in summary
        assert f"Type: {trend.trend_type.replace('_', ' ').title()}" in summary

    # Check that related entities are included for the first trend
    assert "Related entities" in summary
    assert "City Council" in summary

    # Check that evidence is included
    assert "Supporting evidence" in summary
    assert "New Downtown Project Announced" in summary


def test_generate_markdown_summary(sample_trends, event_loop_fixture):
    """Test generating markdown format summary."""
    reporter = TrendReporter()

    summary = reporter.generate_trend_summary(sample_trends, format=ReportFormat.MARKDOWN)

    # Check that the summary includes key elements
    assert "# Local News Trends Report" in summary
    assert f"Found **{len(sample_trends)}** significant trends" in summary

    # Check that each trend is included with markdown formatting
    for trend in sample_trends:
        assert f"## {trend.name}" in summary
        assert f"**Type:** {trend.trend_type.replace('_', ' ').title()}" in summary
        assert f"**Confidence:** {trend.confidence_score:.2f}" in summary
        assert f"**Description:** {trend.description}" in summary

    # Check that tags are included
    assert "**Tags:**" in summary
    assert "#development" in summary

    # Check that related entities are included for the first trend
    assert "### Related entities" in summary
    assert "**City Council**" in summary

    # Check that evidence is included
    assert "### Supporting evidence" in summary
    assert "[New Downtown Project Announced]" in summary

    # Check that frequency data is included
    assert "### Frequency over time" in summary
    assert "| Date | Mentions |" in summary
    assert "| 2023-01-15 | 2 |" in summary


def test_generate_json_summary(sample_trends, event_loop_fixture):
    """Test generating JSON format summary."""
    reporter = TrendReporter()

    json_summary = reporter.generate_trend_summary(sample_trends, format=ReportFormat.JSON)

    # Parse the JSON to check its structure
    data = json.loads(json_summary)

    # Check the top-level structure
    assert "report_date" in data
    assert "trend_count" in data
    assert "trends" in data
    assert data["trend_count"] == len(sample_trends)

    # Check that each trend is included with the right structure
    assert len(data["trends"]) == len(sample_trends)

    for i, trend_data in enumerate(data["trends"]):
        trend = sample_trends[i]
        assert trend_data["name"] == trend.name
        assert trend_data["type"] == trend.trend_type
        assert trend_data["description"] == trend.description
        assert trend_data["confidence"] == trend.confidence_score
        assert trend_data["status"] == trend.status
        assert "entities" in trend_data
        assert "evidence" in trend_data

        # Check entity structure
        if trend.entities:
            assert len(trend_data["entities"]) == len(trend.entities)
            assert trend_data["entities"][0]["text"] == trend.entities[0].text

        # Check evidence structure
        if trend.evidence:
            assert len(trend_data["evidence"]) == len(trend.evidence)
            assert trend_data["evidence"][0]["title"] == trend.evidence[0].article_title


@patch("builtins.open", new_callable=mock_open)
def test_save_report(mock_file, sample_trends, event_loop_fixture):
    """Test saving reports to file."""
    # Test only filename functionality and file_writer integration
    with patch("os.makedirs"):
        # Create reporter with no file_writer (uses direct file writes)
        reporter = TrendReporter(output_dir="test_output")
        
        # Test saving with auto-generated filename
        with patch.object(reporter, "generate_trend_summary", return_value="Test report content"), \
             patch("local_newsifier.tools.trend_reporter.datetime") as mock_dt:
            mock_date = MagicMock()
            mock_date.strftime.return_value = "20230115_120000"
            mock_dt.now.return_value = mock_date

            filepath = reporter.save_report(sample_trends, format=ReportFormat.TEXT)

            # Verify the filepath is correct
            assert filepath == os.path.join("test_output", "trend_report_20230115_120000.text")
            # Verify file was opened for writing
            mock_file.assert_called_with(filepath, "w")
            # Verify content was written correctly
            mock_file().write.assert_called_with("Test report content")
        
        # Test saving with provided filename
        with patch.object(reporter, "generate_trend_summary", return_value="Test report content"), \
             patch("os.makedirs"):
            filepath = reporter.save_report(
                sample_trends, filename="custom_report", format=ReportFormat.MARKDOWN
            )

            # Verify the filepath is correct
            assert filepath == os.path.join("test_output", "custom_report.markdown")
            # Verify file was opened for writing
            mock_file.assert_called_with(filepath, "w")
            # Verify content was written correctly
            mock_file().write.assert_called_with("Test report content")

        # Test saving with filename that already has extension
        with patch.object(reporter, "generate_trend_summary", return_value="Test report content"), \
             patch("os.makedirs"):
            filepath = reporter.save_report(
                sample_trends, filename="custom_report.json", format=ReportFormat.JSON
            )

            # Verify the filepath is correct
            assert filepath == os.path.join("test_output", "custom_report.json")
            # Verify file was opened for writing
            mock_file.assert_called_with(filepath, "w")
            # Verify content was written correctly
            mock_file().write.assert_called_with("Test report content")

        # Test reporter with file_writer
        mock_file_writer = MagicMock()
        mock_file_writer.write_file.return_value = "/mock/path/custom_report.json"

        reporter_with_writer = TrendReporter(output_dir="test_output", file_writer=mock_file_writer)

        with patch.object(reporter_with_writer, "generate_trend_summary", return_value="Test report content"), \
             patch("os.makedirs"):
            filepath = reporter_with_writer.save_report(
                sample_trends, filename="custom_report.json", format=ReportFormat.JSON
            )

            # Assert file_writer was used
            mock_file_writer.write_file.assert_called_once()
            assert filepath == "/mock/path/custom_report.json"

            # Verify file_writer was called with correct path and content
            mock_file_writer.write_file.assert_called_with(
                os.path.join("test_output", "custom_report.json"),
                "Test report content"
            )
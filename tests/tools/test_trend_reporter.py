"""Tests for the TrendReporter tool."""

import json
import os
from datetime import datetime, timezone
from unittest.mock import MagicMock, mock_open, patch

import pytest

# Import event loop fixture
pytest.importorskip("tests.fixtures.event_loop")
from tests.fixtures.event_loop import event_loop_fixture  # noqa

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
        assert reporter.file_writer is None
        mock_makedirs.assert_called_with("output", exist_ok=True)

        # Test with custom output_dir
        reporter = TrendReporter(output_dir="custom_output")
        assert reporter.output_dir == "custom_output"
        mock_makedirs.assert_called_with("custom_output", exist_ok=True)

        # Test with file_writer
        mock_writer = MagicMock()
        reporter = TrendReporter(output_dir="custom_output", file_writer=mock_writer)
        assert reporter.file_writer is mock_writer


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


def test_save_report(event_loop_fixture):
    """Test saving reports to file."""
    # Use lower level unittest mocks for this test
    reporter = TrendReporter(output_dir="test_output")

    # Mock generate_trend_summary to return a controlled string
    reporter.generate_trend_summary = MagicMock(return_value="Test report content")

    # Mock the built-in open function
    m = mock_open()
    with patch("builtins.open", m):
        # Test saving with auto-generated filename
        with patch("local_newsifier.tools.trend_reporter.datetime") as mock_dt:
            mock_date = MagicMock()
            mock_date.strftime.return_value = "20230115_120000"
            mock_dt.now.return_value = mock_date

            filepath = reporter.save_report([], format=ReportFormat.TEXT)

            assert filepath == os.path.join("test_output", "trend_report_20230115_120000.text")
            m.assert_called_with(filepath, "w")
            handle = m()
            handle.write.assert_called_with("Test report content")

    # Create additional test with provided filename
    reporter.generate_trend_summary.reset_mock()
    m = mock_open()
    with patch("builtins.open", m):
        filepath = reporter.save_report(
            [], filename="custom_report", format=ReportFormat.MARKDOWN
        )

        assert filepath == os.path.join("test_output", "custom_report.markdown")
        m.assert_called_with(filepath, "w")

    # Test with filename that already has extension
    reporter.generate_trend_summary.reset_mock()
    m = mock_open()
    with patch("builtins.open", m):
        filepath = reporter.save_report(
            [], filename="custom_report.json", format=ReportFormat.JSON
        )

        assert filepath == os.path.join("test_output", "custom_report.json")
        m.assert_called_with(filepath, "w")


@patch("builtins.open", new_callable=mock_open)
def test_save_report_with_file_writer(mock_file, sample_trends, event_loop_fixture):
    """Test saving report when file_writer is injected."""
    # Create mock file writer
    mock_writer = MagicMock()
    mock_writer.write_file.return_value = "/path/to/output/test_report.text"

    # Create reporter with injected file_writer
    reporter = TrendReporter(output_dir="test_output", file_writer=mock_writer)

    # Patch generate_trend_summary to return predictable content
    with patch.object(reporter, "generate_trend_summary", return_value="Test content"):
        # Save report
        filepath = reporter.save_report(
            sample_trends,
            filename="test_report",
            format=ReportFormat.TEXT
        )

        # Verify file_writer was called
        mock_writer.write_file.assert_called_once()

        # The filepath should be what's returned by the mock_file_writer
        assert filepath == "/path/to/output/test_report.text"

        # Verify open() was NOT called - we should be using the file_writer instead
        mock_file.assert_not_called()
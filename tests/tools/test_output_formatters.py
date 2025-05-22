"""Tests for output formatting utilities."""

import json
import os
import inspect
from datetime import datetime, timezone
from unittest.mock import MagicMock, mock_open, patch

import pytest
from tests.fixtures.event_loop import event_loop_fixture

from local_newsifier.models.sentiment import SentimentVisualizationData
from local_newsifier.models.trend import (
    TrendAnalysis,
    TrendEntity,
    TrendEvidenceItem,
    TrendStatus,
    TrendType,
)
from local_newsifier.tools.opinion_visualizer import OpinionVisualizerTool
from local_newsifier.tools.trend_reporter import ReportFormat, TrendReporter


class TestOpinionVisualizerOutputFormatting:
    """Test class for OpinionVisualizer output formatting methods."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock database session."""
        return MagicMock()

    @pytest.fixture
    def visualizer(self, mock_session, event_loop_fixture):
        """Create an opinion visualizer instance."""
        # Create a direct instance bypassing the decorator
        # Import the real class methods
        from local_newsifier.tools.opinion_visualizer import OpinionVisualizerTool

        # Create a mock
        visualizer = MagicMock()
        visualizer.session = mock_session
        visualizer.session_factory = lambda: mock_session

        # Copy the actual methods from the class (excluding __init__)
        for name, method in inspect.getmembers(OpinionVisualizerTool, predicate=inspect.isfunction):
            if name != "__init__":
                # Bind the method to our mock object
                visualizer.__dict__[name] = method.__get__(visualizer, OpinionVisualizerTool)

        return visualizer

    @pytest.fixture
    def sample_data(self):
        """Create sample visualization data."""
        return SentimentVisualizationData(
            topic="climate change",
            time_periods=["2023-05-01", "2023-05-02", "2023-05-03"],
            sentiment_values=[0.2, -0.3, -0.5],
            confidence_intervals=[
                {"lower": 0.1, "upper": 0.3},
                {"lower": -0.4, "upper": -0.2},
                {"lower": -0.6, "upper": -0.4},
            ],
            article_counts=[5, 3, 7],
            viz_metadata={"start_date": "2023-05-01", "end_date": "2023-05-03", "interval": "day"},
        )

    @pytest.fixture
    def comparison_data(self, sample_data):
        """Create sample comparison visualization data."""
        climate_data = sample_data

        energy_data = SentimentVisualizationData(
            topic="renewable energy",
            time_periods=["2023-05-01", "2023-05-02", "2023-05-03"],
            sentiment_values=[0.5, 0.4, 0.6],
            confidence_intervals=[
                {"lower": 0.4, "upper": 0.6},
                {"lower": 0.3, "upper": 0.5},
                {"lower": 0.5, "upper": 0.7},
            ],
            article_counts=[3, 4, 5],
            viz_metadata={"start_date": "2023-05-01", "end_date": "2023-05-03", "interval": "day"},
        )

        return {"climate change": climate_data, "renewable energy": energy_data}

    def test_text_report_structure(self, visualizer, sample_data, event_loop_fixture):
        """Test the structure of text reports."""
        report = visualizer.generate_text_report(sample_data, "timeline")

        # Check report sections
        assert "SENTIMENT ANALYSIS REPORT:" in report
        assert "=" * 50 in report  # Separator line
        assert "Time period:" in report
        assert "Interval:" in report
        assert "SUMMARY STATISTICS" in report
        assert "SENTIMENT TIMELINE" in report

        # Check data formatting
        assert "Average sentiment:" in report
        assert "Minimum sentiment:" in report
        assert "Maximum sentiment:" in report
        assert "Total articles:" in report

        # Check timeline entries
        for period in sample_data.time_periods:
            assert period in report

    def test_markdown_report_structure(self, visualizer, sample_data, event_loop_fixture):
        """Test the structure of markdown reports."""
        report = visualizer.generate_markdown_report(sample_data, "timeline")

        # Check markdown formatting
        assert "# Sentiment Analysis Report:" in report
        assert "**Time period:**" in report
        assert "**Interval:**" in report
        assert "## Summary Statistics" in report
        assert "## Sentiment Timeline" in report

        # Check markdown list formatting
        assert "- **Average sentiment:**" in report
        assert "- **Minimum sentiment:**" in report
        assert "- **Maximum sentiment:**" in report

        # Check table formatting
        assert "| Period | Sentiment | Articles |" in report
        assert "|--------|-----------|----------|" in report

        # Check data rows
        for i, period in enumerate(sample_data.time_periods):
            sentiment = sample_data.sentiment_values[i]
            articles = sample_data.article_counts[i]
            assert f"| {period} | {sentiment:.2f} | {articles} |" in report

    def test_html_report_structure(self, visualizer, sample_data, event_loop_fixture):
        """Test the structure of HTML reports."""
        report = visualizer.generate_html_report(sample_data, "timeline")

        # Check HTML structure
        assert "<html>" in report
        assert "<head>" in report
        assert "<style>" in report
        assert "</style>" in report
        assert "<title>" in report
        assert "</head>" in report
        assert "<body>" in report
        assert "</body>" in report
        assert "</html>" in report

        # Check content structure
        assert "<h1>" in report
        assert "<h2>" in report
        assert "<table>" in report
        assert "<tr>" in report
        assert "<th>" in report
        assert "<td>" in report

        # Check CSS styling
        assert "font-family:" in report
        assert "border-collapse: collapse;" in report
        assert "background-color:" in report

    def test_comparison_text_report_structure(
        self, visualizer, comparison_data, event_loop_fixture
    ):
        """Test the structure of comparison text reports."""
        report = visualizer.generate_text_report(comparison_data, "comparison")

        # Check report sections
        assert "SENTIMENT COMPARISON REPORT" in report
        assert "=" * 50 in report  # Separator line
        assert "Time period:" in report
        assert "Interval:" in report
        assert "SUMMARY STATISTICS" in report
        assert "DETAILED COMPARISON" in report

        # Check that all topics are included
        for topic in comparison_data.keys():
            assert topic in report

        # Check that all time periods are included
        for period in comparison_data["climate change"].time_periods:
            assert period in report

    def test_comparison_markdown_report_structure(
        self, visualizer, comparison_data, event_loop_fixture
    ):
        """Test the structure of comparison markdown reports."""
        report = visualizer.generate_markdown_report(comparison_data, "comparison")

        # Check markdown formatting
        assert "# Sentiment Comparison Report" in report
        assert "**Time period:**" in report
        assert "**Interval:**" in report
        assert "## Summary Statistics" in report
        assert "## Detailed Comparison" in report

        # Check table formatting
        assert "| Topic | Average Sentiment | Total Articles |" in report
        assert "|-------|------------------|----------------|" in report

        # Check that all topics are included in the summary table
        for topic in comparison_data.keys():
            # Find the row for this topic
            assert f"| {topic} |" in report

        # Check that the comparison table includes all topics and periods
        assert "| Period |" in report
        for topic in comparison_data.keys():
            assert f" {topic} |" in report

    def test_comparison_html_report_structure(
        self, visualizer, comparison_data, event_loop_fixture
    ):
        """Test the structure of comparison HTML reports."""
        report = visualizer.generate_html_report(comparison_data, "comparison")

        # Check HTML structure
        assert "<html>" in report
        assert "<head>" in report
        assert "<style>" in report
        assert "</style>" in report
        assert "<title>Sentiment Comparison</title>" in report
        assert "</head>" in report
        assert "<body>" in report
        assert "</body>" in report
        assert "</html>" in report

        # Check content structure
        assert "<h1>Sentiment Comparison Report</h1>" in report
        assert "<h2>Summary Statistics</h2>" in report
        assert "<h2>Detailed Comparison</h2>" in report

        # Check table structure
        assert "<table>" in report
        assert "<tr><th>Topic</th><th>Average Sentiment</th><th>Total Articles</th></tr>" in report

        # Check that all topics are included
        for topic in comparison_data.keys():
            assert f"<td>{topic}</td>" in report

    def test_text_report_calculations(self, visualizer, sample_data, event_loop_fixture):
        """Test that calculations in text reports are correct."""
        report = visualizer.generate_text_report(sample_data, "timeline")

        # Calculate expected values
        avg_sentiment = sum(sample_data.sentiment_values) / len(sample_data.sentiment_values)
        min_sentiment = min(sample_data.sentiment_values)
        max_sentiment = max(sample_data.sentiment_values)
        total_articles = sum(sample_data.article_counts)

        # Check that these values are correctly formatted in the report
        assert f"Average sentiment: {avg_sentiment:.2f}" in report
        assert f"Minimum sentiment: {min_sentiment:.2f}" in report
        assert f"Maximum sentiment: {max_sentiment:.2f}" in report
        assert f"Total articles: {total_articles}" in report

        # Check individual period data
        for i, period in enumerate(sample_data.time_periods):
            sentiment = sample_data.sentiment_values[i]
            articles = sample_data.article_counts[i]
            assert f"{period}: {sentiment:.2f} ({articles} articles)" in report

    def test_markdown_report_calculations(self, visualizer, sample_data, event_loop_fixture):
        """Test that calculations in markdown reports are correct."""
        report = visualizer.generate_markdown_report(sample_data, "timeline")

        # Calculate expected values
        avg_sentiment = sum(sample_data.sentiment_values) / len(sample_data.sentiment_values)
        min_sentiment = min(sample_data.sentiment_values)
        max_sentiment = max(sample_data.sentiment_values)
        total_articles = sum(sample_data.article_counts)

        # Check that these values are correctly formatted in the report
        assert f"**Average sentiment:** {avg_sentiment:.2f}" in report
        assert f"**Minimum sentiment:** {min_sentiment:.2f}" in report
        assert f"**Maximum sentiment:** {max_sentiment:.2f}" in report
        assert f"**Total articles:** {total_articles}" in report

    def test_html_report_calculations(self, visualizer, sample_data, event_loop_fixture):
        """Test that calculations in HTML reports are correct."""
        report = visualizer.generate_html_report(sample_data, "timeline")

        # Calculate expected values
        avg_sentiment = sum(sample_data.sentiment_values) / len(sample_data.sentiment_values)
        min_sentiment = min(sample_data.sentiment_values)
        max_sentiment = max(sample_data.sentiment_values)
        total_articles = sum(sample_data.article_counts)

        # Check that these values are correctly formatted in the report
        assert f"<li><strong>Average sentiment:</strong> {avg_sentiment:.2f}</li>" in report
        assert f"<li><strong>Minimum sentiment:</strong> {min_sentiment:.2f}</li>" in report
        assert f"<li><strong>Maximum sentiment:</strong> {max_sentiment:.2f}</li>" in report
        assert f"<li><strong>Total articles:</strong> {total_articles}</li>" in report

    def test_empty_data_handling(self, visualizer, event_loop_fixture):
        """Test handling of empty data in reports."""
        empty_data = SentimentVisualizationData(
            topic="empty topic",
            time_periods=[],
            sentiment_values=[],
            article_counts=[],
            confidence_intervals=[],
            viz_metadata={"start_date": "2023-05-01", "end_date": "2023-05-03", "interval": "day"},
        )

        # Test text report
        text_report = visualizer.generate_text_report(empty_data, "timeline")
        assert "No sentiment data available" in text_report

        # Test markdown report
        md_report = visualizer.generate_markdown_report(empty_data, "timeline")
        assert "No sentiment data available" in md_report

        # Test HTML report
        html_report = visualizer.generate_html_report(empty_data, "timeline")
        assert "No sentiment data available" in html_report

    def test_empty_comparison_data_handling(self, visualizer, event_loop_fixture):
        """Test handling of empty comparison data in reports."""
        empty_comparison = {}

        # Test text report
        text_report = visualizer.generate_text_report(empty_comparison, "comparison")
        assert "No sentiment data available for comparison" in text_report

        # Test markdown report
        md_report = visualizer.generate_markdown_report(empty_comparison, "comparison")
        assert "No sentiment data available for comparison" in md_report

        # Test HTML report
        html_report = visualizer.generate_html_report(empty_comparison, "comparison")
        assert "No sentiment data available for comparison" in html_report

    def test_invalid_report_type(
        self, visualizer, sample_data, comparison_data, event_loop_fixture
    ):
        """Test error handling for invalid report types."""
        # Test with invalid report type
        with pytest.raises(ValueError) as excinfo:
            visualizer.generate_text_report(sample_data, "invalid_type")
        assert "Invalid report type" in str(excinfo.value)

        # Test with mismatched data type and report type
        with pytest.raises(ValueError) as excinfo:
            visualizer.generate_text_report(sample_data, "comparison")
        assert "data type mismatch" in str(excinfo.value)

        with pytest.raises(ValueError) as excinfo:
            visualizer.generate_text_report(comparison_data, "timeline")
        assert "data type mismatch" in str(excinfo.value)


class TestTrendReporterOutputFormatting:
    """Test class for TrendReporter output formatting methods."""

    @pytest.fixture
    def sample_trends(self):
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

    def test_text_summary_structure(self, sample_trends, event_loop_fixture):
        """Test the structure of text format summaries."""
        reporter = TrendReporter()
        summary = reporter.generate_trend_summary(sample_trends, format=ReportFormat.TEXT)

        # Check report sections
        assert "LOCAL NEWS TRENDS REPORT" in summary
        assert f"Found {len(sample_trends)} significant trends" in summary

        # Check that each trend is included
        for i, trend in enumerate(sample_trends, 1):
            assert f"{i}. {trend.name}" in summary
            assert f"Type: {trend.trend_type.replace('_', ' ').title()}" in summary
            assert trend.description in summary

        # Check that related entities are included
        assert "Related entities:" in summary
        assert "City Council" in summary

        # Check that evidence is included
        assert "Supporting evidence:" in summary
        assert "New Downtown Project Announced" in summary

    def test_markdown_summary_structure(self, sample_trends, event_loop_fixture):
        """Test the structure of markdown format summaries."""
        reporter = TrendReporter()
        summary = reporter.generate_trend_summary(sample_trends, format=ReportFormat.MARKDOWN)

        # Check markdown formatting
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

        # Check that related entities are included
        assert "### Related entities" in summary
        assert "**City Council**" in summary

        # Check that evidence is included
        assert "### Supporting evidence" in summary
        assert "[New Downtown Project Announced]" in summary

        # Check that frequency data is included
        assert "### Frequency over time" in summary
        assert "| Date | Mentions |" in summary
        assert "| 2023-01-15 | 2 |" in summary

    def test_json_summary_structure(self, sample_trends, event_loop_fixture):
        """Test the structure of JSON format summaries."""
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

    def test_empty_trends_handling(self, event_loop_fixture):
        """Test handling of empty trends list."""
        reporter = TrendReporter()

        # Test with empty trends list
        text_summary = reporter.generate_trend_summary([], format=ReportFormat.TEXT)
        assert "No significant trends" in text_summary

        markdown_summary = reporter.generate_trend_summary([], format=ReportFormat.MARKDOWN)
        assert "No significant trends" in markdown_summary

        json_summary = reporter.generate_trend_summary([], format=ReportFormat.JSON)
        assert "No significant trends" in json_summary

    def test_save_report_file_formats(self, sample_trends, tmp_path, event_loop_fixture):
        """Test saving reports in different file formats."""
        reporter = TrendReporter(output_dir=str(tmp_path))

        # Test saving text format
        text_path = reporter.save_report(
            sample_trends, filename="test_report.text", format=ReportFormat.TEXT
        )
        assert os.path.exists(text_path)
        assert text_path.endswith(".text")

        # Test saving markdown format
        md_path = reporter.save_report(
            sample_trends, filename="test_report.markdown", format=ReportFormat.MARKDOWN
        )
        assert os.path.exists(md_path)
        assert md_path.endswith(".markdown")

        # Test saving JSON format
        json_path = reporter.save_report(
            sample_trends, filename="test_report.json", format=ReportFormat.JSON
        )
        assert os.path.exists(json_path)
        assert json_path.endswith(".json")

        # Verify file contents
        with open(text_path, "r") as f:
            text_content = f.read()
            assert "LOCAL NEWS TRENDS REPORT" in text_content

        with open(md_path, "r") as f:
            md_content = f.read()
            assert "# Local News Trends Report" in md_content

        with open(json_path, "r") as f:
            json_content = json.load(f)
            assert "report_date" in json_content
            assert "trends" in json_content

    def test_auto_filename_generation(self, sample_trends, tmp_path, event_loop_fixture):
        """Test automatic filename generation."""
        reporter = TrendReporter(output_dir=str(tmp_path))

        # Mock datetime to get a predictable filename
        with patch("local_newsifier.tools.trend_reporter.datetime") as mock_dt:
            mock_date = MagicMock()
            mock_date.strftime.return_value = "20230115_120000"
            mock_dt.now.return_value = mock_date

            # Test auto-generated filename
            path = reporter.save_report(sample_trends, format=ReportFormat.TEXT)
            expected_path = os.path.join(str(tmp_path), "trend_report_20230115_120000.text")
            assert path == expected_path
            assert os.path.exists(path)

    def test_filename_extension_handling(self, sample_trends, tmp_path, event_loop_fixture):
        """Test handling of filename extensions."""
        reporter = TrendReporter(output_dir=str(tmp_path))

        # Test with filename that doesn't have the correct extension
        path = reporter.save_report(
            sample_trends, filename="report_without_extension", format=ReportFormat.JSON
        )
        assert path.endswith(".json")
        assert os.path.exists(path)

        # Test with filename that already has the correct extension
        path = reporter.save_report(
            sample_trends, filename="report_with_extension.markdown", format=ReportFormat.MARKDOWN
        )
        assert path.endswith(".markdown")
        assert not path.endswith(".markdown.markdown")  # Shouldn't add extension twice
        assert os.path.exists(path)

        # Test with filename that has a different extension
        path = reporter.save_report(
            sample_trends, filename="report_wrong_extension.txt", format=ReportFormat.JSON
        )
        assert path.endswith(".txt.json")  # Should add correct extension
        assert os.path.exists(path)

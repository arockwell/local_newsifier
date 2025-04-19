"""Tests for the HeadlineTrendFlow."""

import unittest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from pytest_mock import MockFixture

from local_newsifier.flows.analysis.headline_trend_flow import HeadlineTrendFlow
from local_newsifier.tools.analysis.headline_analyzer import HeadlineTrendAnalyzer


class TestHeadlineTrendFlow:
    """Tests for the HeadlineTrendFlow class."""

    @pytest.fixture
    def mock_session(self) -> MagicMock:
        """Create a mock database session."""
        return MagicMock()

    @pytest.fixture
    def mock_headline_analyzer(self) -> MagicMock:
        """Create a mock headline analyzer."""
        return MagicMock()

    @pytest.fixture
    def flow(self, mock_session: MagicMock, mock_headline_analyzer: MagicMock) -> HeadlineTrendFlow:
        """Create a flow with mocked components."""
        with patch('local_newsifier.tools.analysis.headline_analyzer.HeadlineTrendAnalyzer', autospec=True) as mock_analyzer_class:
            mock_analyzer_class.return_value = mock_headline_analyzer
            flow = HeadlineTrendFlow(session=mock_session)
            flow.headline_analyzer = mock_headline_analyzer
            return flow

    def test_analyze_recent_trends(
        self, flow: HeadlineTrendFlow, mock_headline_analyzer: MagicMock
    ) -> None:
        """Test analyzing recent trends with default parameters."""
        # Set up mock analyzer response
        mock_results = {
            "trending_terms": [{"term": "test", "growth_rate": 1.5, "total_mentions": 5}],
            "overall_top_terms": [("test", 5)],
            "raw_data": {"2023-05-01": [("test", 2)]},
            "period_counts": {"2023-05-01": 2}
        }
        mock_headline_analyzer.analyze_trends.return_value = mock_results
        
        # Call the method
        result = flow.analyze_recent_trends()
        
        # Verify analyzer was called with correct parameters
        mock_headline_analyzer.analyze_trends.assert_called_once()
        args, kwargs = mock_headline_analyzer.analyze_trends.call_args
        assert kwargs["time_interval"] == "day"
        assert kwargs["top_n"] == 20
        
        # Verify results
        assert result == mock_results
        
    def test_analyze_recent_trends_with_custom_params(
        self, flow: HeadlineTrendFlow, mock_headline_analyzer: MagicMock
    ) -> None:
        """Test analyzing recent trends with custom parameters."""
        # Set up mock analyzer response
        mock_results = {
            "trending_terms": [{"term": "custom", "growth_rate": 2.0, "total_mentions": 10}],
            "overall_top_terms": [("custom", 10)],
            "raw_data": {"2023-03-01": [("custom", 5)]},
            "period_counts": {"2023-03-01": 5}
        }
        mock_headline_analyzer.analyze_trends.return_value = mock_results
        
        # Call the method with custom parameters
        result = flow.analyze_recent_trends(days_back=60, interval="week", top_n=10)
        
        # Verify analyzer was called with correct parameters
        mock_headline_analyzer.analyze_trends.assert_called_once()
        args, kwargs = mock_headline_analyzer.analyze_trends.call_args
        assert kwargs["time_interval"] == "week"
        assert kwargs["top_n"] == 10
        
        # Verify results
        assert result == mock_results
        
    def test_analyze_date_range(
        self, flow: HeadlineTrendFlow, mock_headline_analyzer: MagicMock
    ) -> None:
        """Test analyzing a specific date range."""
        # Set up mock analyzer response
        mock_results = {
            "trending_terms": [{"term": "custom", "growth_rate": 2.0, "total_mentions": 8}],
            "overall_top_terms": [("custom", 8)],
            "raw_data": {"2023-01-01": [("custom", 3)]},
            "period_counts": {"2023-01-01": 3}
        }
        mock_headline_analyzer.analyze_trends.return_value = mock_results
        
        # Call the method with custom date range
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 1, 10)
        result = flow.analyze_date_range(
            start_date=start_date,
            end_date=end_date,
            interval="week",
            top_n=15
        )
        
        # Verify analyzer was called with correct parameters
        # We need to check that all expected params were passed, ignoring the session param
        args, kwargs = mock_headline_analyzer.analyze_trends.call_args
        assert kwargs["start_date"] == start_date
        assert kwargs["end_date"] == end_date
        assert kwargs["time_interval"] == "week"
        assert kwargs["top_n"] == 15
        assert "session" in kwargs
        
        # Verify results
        assert result == mock_results
        
    def test_generate_text_report(
        self, flow: HeadlineTrendFlow
    ) -> None:
        """Test generating a text report."""
        # Sample analysis results
        results = {
            "trending_terms": [
                {"term": "term1", "growth_rate": 1.5, "total_mentions": 10},
                {"term": "term2", "growth_rate": 0.8, "total_mentions": 5}
            ],
            "overall_top_terms": [("term1", 10), ("term3", 7)],
            "period_counts": {"2023-05-01": 5, "2023-05-02": 3}
        }
        
        # Generate report
        report = flow.generate_report(results, format_type="text")
        
        # Verify report contains key sections
        assert "HEADLINE TREND ANALYSIS REPORT" in report
        assert "TOP TRENDING TERMS" in report
        assert "term1" in report
        assert "term2" in report
        assert "OVERALL TOP TERMS" in report
        assert "term3" in report
        assert "ARTICLE COUNTS BY PERIOD" in report
        assert "2023-05-01" in report
        assert "2023-05-02" in report
        
    def test_generate_markdown_report(
        self, flow: HeadlineTrendFlow
    ) -> None:
        """Test generating a markdown report."""
        # Sample analysis results
        results = {
            "trending_terms": [
                {"term": "term1", "growth_rate": 1.5, "total_mentions": 10}
            ],
            "overall_top_terms": [("term1", 10)],
            "period_counts": {"2023-05-01": 5}
        }
        
        # Generate report
        report = flow.generate_report(results, format_type="markdown")
        
        # Verify report contains markdown formatting
        assert "# Headline Trend Analysis Report" in report
        assert "## Top Trending Terms" in report
        assert "**term1**" in report
        assert "| Period | Article Count |" in report
        assert "| 2023-05-01 | 5 |" in report
        
    def test_generate_html_report(
        self, flow: HeadlineTrendFlow
    ) -> None:
        """Test generating an HTML report."""
        # Sample analysis results
        results = {
            "trending_terms": [
                {"term": "term1", "growth_rate": 1.5, "total_mentions": 10}
            ],
            "overall_top_terms": [("term1", 10)],
            "period_counts": {"2023-05-01": 5}
        }
        
        # Generate report
        report = flow.generate_report(results, format_type="html")
        
        # Verify report contains HTML formatting
        assert "<html>" in report
        assert "<h1>Headline Trend Analysis Report</h1>" in report
        assert "<strong>term1</strong>" in report
        assert "<table border='1'>" in report
        assert "<tr><td>2023-05-01</td><td>5</td></tr>" in report
        
    def test_error_in_results(
        self, flow: HeadlineTrendFlow
    ) -> None:
        """Test handling error in results."""
        # Error results
        results = {"error": "No headlines found"}
        
        # Generate report
        report = flow.generate_report(results)
        
        # Verify error is included in report
        assert "Error:" in report
        assert "No headlines found" in report
        
    def test_flow_cleanup(self, mock_session: MagicMock) -> None:
        """Test that resources are properly cleaned up."""
        # Create a flow generator to mock
        session_generator = MagicMock()
        
        # Create a flow using the provided mock session
        flow = HeadlineTrendFlow(session=mock_session)
        flow.session_generator = session_generator
        flow._owns_session = True
        
        # Call the destructor
        flow.__del__()
        
        # Verify next was called on session generator
        session_generator.__next__.assert_called_once()
        
        # Test with a flow that doesn't own its session
        flow = HeadlineTrendFlow(session=mock_session)
        flow._owns_session = False
        
        # Reset the mock
        session_generator.reset_mock()
        
        # Call the destructor
        flow.__del__()
        
        # Verify session generator was not used
        session_generator.__next__.assert_not_called()

    def test_init_without_session(self, monkeypatch):
        """Test initialization without providing a session."""
        # Mock session generator
        mock_session = MagicMock()
        mock_session_generator = MagicMock()
        mock_session_generator.__next__.return_value = mock_session
        
        # Use the correct import path for patching
        with patch('local_newsifier.flows.analysis.headline_trend_flow.get_session', return_value=mock_session_generator):
            
            # Create flow without providing a session
            flow = HeadlineTrendFlow()
            
            # Verify session was created
            assert flow.session is not None
            assert flow.session == mock_session
            assert flow._owns_session is True
            
            # Clean up
            del flow
            mock_session_generator.__next__.assert_called()
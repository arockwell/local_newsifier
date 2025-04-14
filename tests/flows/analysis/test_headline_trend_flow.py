"""Tests for HeadlineTrendFlow."""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from local_newsifier.flows.analysis.headline_trend_flow import HeadlineTrendFlow
from local_newsifier.database.manager import DatabaseManager
from local_newsifier.models.database.article import ArticleDB


@pytest.fixture
def mock_db_manager():
    """Create a mock database manager."""
    mock_manager = MagicMock(spec=DatabaseManager)
    mock_manager.session = MagicMock()
    return mock_manager


@pytest.fixture
def mock_headline_analyzer():
    """Create a mock headline analyzer."""
    return MagicMock()


@pytest.fixture
def flow_with_mocks(mock_db_manager, mock_headline_analyzer):
    """Create a HeadlineTrendFlow with mocked dependencies."""
    with patch("local_newsifier.flows.analysis.headline_trend_flow.HeadlineTrendAnalyzer", return_value=mock_headline_analyzer):
        flow = HeadlineTrendFlow(db_manager=mock_db_manager)
        return flow, mock_db_manager, mock_headline_analyzer


def test_init_with_db_manager(mock_db_manager):
    """Test initialization with provided database manager."""
    flow = HeadlineTrendFlow(db_manager=mock_db_manager)
    assert flow.db_manager == mock_db_manager
    assert not flow._owns_session


def test_init_without_db_manager():
    """Test initialization without database manager."""
    with patch("local_newsifier.flows.analysis.headline_trend_flow.get_database_settings") as mock_get_settings, \
         patch("local_newsifier.flows.analysis.headline_trend_flow.init_db") as mock_init_db, \
         patch("local_newsifier.flows.analysis.headline_trend_flow.get_session") as mock_get_session:
        
        mock_session = MagicMock()
        mock_session_factory = MagicMock(return_value=mock_session)
        mock_get_session.return_value = mock_session_factory
        
        flow = HeadlineTrendFlow()
        assert flow._owns_session
        assert flow.db_manager is not None
        assert flow.db_manager.session == mock_session


def test_analyze_recent_trends(flow_with_mocks):
    """Test analyzing recent trends."""
    flow, _, mock_analyzer = flow_with_mocks
    
    # Mock return value
    expected_results = {
        "trending_terms": [{"term": "test", "growth_rate": 0.5, "total_mentions": 10}],
        "overall_top_terms": [("test", 10)],
        "period_counts": {"2024-03-01": 5}
    }
    mock_analyzer.analyze_trends.return_value = expected_results
    
    # Call the method
    results = flow.analyze_recent_trends(days_back=7, interval="day", top_n=10)
    
    # Verify the results
    assert results == expected_results
    mock_analyzer.analyze_trends.assert_called_once()
    call_args = mock_analyzer.analyze_trends.call_args[1]
    assert call_args["time_interval"] == "day"
    assert call_args["top_n"] == 10
    assert isinstance(call_args["start_date"], datetime)
    assert isinstance(call_args["end_date"], datetime)


def test_analyze_date_range(flow_with_mocks):
    """Test analyzing a specific date range."""
    flow, _, mock_analyzer = flow_with_mocks
    
    # Set up test dates
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 1, 7)
    
    # Mock return value
    expected_results = {
        "trending_terms": [{"term": "test", "growth_rate": 0.5, "total_mentions": 10}],
        "overall_top_terms": [("test", 10)],
        "period_counts": {"2024-01-01": 5}
    }
    mock_analyzer.analyze_trends.return_value = expected_results
    
    # Call the method
    results = flow.analyze_date_range(start_date, end_date, interval="week", top_n=15)
    
    # Verify the results
    assert results == expected_results
    mock_analyzer.analyze_trends.assert_called_once_with(
        start_date=start_date,
        end_date=end_date,
        time_interval="week",
        top_n=15
    )


def test_generate_text_report(flow_with_mocks):
    """Test generating a text report."""
    flow, _, _ = flow_with_mocks
    
    results = {
        "trending_terms": [
            {"term": "test", "growth_rate": 0.5, "total_mentions": 10},
            {"term": "example", "growth_rate": 0.3, "total_mentions": 8}
        ],
        "overall_top_terms": [("test", 10), ("example", 8)],
        "period_counts": {"2024-03-01": 5, "2024-03-02": 7}
    }
    
    report = flow.generate_report(results, format_type="text")
    
    assert "HEADLINE TREND ANALYSIS REPORT" in report
    assert "TOP TRENDING TERMS:" in report
    assert "test (Growth: 50.0%" in report
    assert "example (Growth: 30.0%" in report
    assert "OVERALL TOP TERMS:" in report
    assert "ARTICLE COUNTS BY PERIOD:" in report
    assert "2024-03-01: 5" in report
    assert "2024-03-02: 7" in report


def test_generate_markdown_report(flow_with_mocks):
    """Test generating a markdown report."""
    flow, _, _ = flow_with_mocks
    
    results = {
        "trending_terms": [
            {"term": "test", "growth_rate": 0.5, "total_mentions": 10},
            {"term": "example", "growth_rate": 0.3, "total_mentions": 8}
        ],
        "overall_top_terms": [("test", 10), ("example", 8)],
        "period_counts": {"2024-03-01": 5, "2024-03-02": 7}
    }
    
    report = flow.generate_report(results, format_type="markdown")
    
    assert "# Headline Trend Analysis Report" in report
    assert "## Top Trending Terms" in report
    assert "**test**" in report
    assert "**example**" in report
    assert "| Period | Article Count |" in report


def test_generate_html_report(flow_with_mocks):
    """Test generating an HTML report."""
    flow, _, _ = flow_with_mocks
    
    results = {
        "trending_terms": [
            {"term": "test", "growth_rate": 0.5, "total_mentions": 10},
            {"term": "example", "growth_rate": 0.3, "total_mentions": 8}
        ],
        "overall_top_terms": [("test", 10), ("example", 8)],
        "period_counts": {"2024-03-01": 5, "2024-03-02": 7}
    }
    
    report = flow.generate_report(results, format_type="html")
    
    assert "<html>" in report
    assert "<h1>Headline Trend Analysis Report</h1>" in report
    assert "<strong>test</strong>" in report
    assert "<table border='1'>" in report
    assert "</html>" in report


def test_generate_report_with_error(flow_with_mocks):
    """Test generating a report when there's an error in the results."""
    flow, _, _ = flow_with_mocks
    
    results = {"error": "Something went wrong"}
    report = flow.generate_report(results)
    
    assert "Error: Something went wrong" in report


def test_cleanup_on_delete(mock_db_manager):
    """Test that the session is closed when the flow is deleted."""
    flow = HeadlineTrendFlow(db_manager=mock_db_manager)
    flow.__del__()
    
    # Session should not be closed since we didn't create it
    mock_db_manager.session.close.assert_not_called()
    
    # Test with owned session
    with patch("local_newsifier.flows.analysis.headline_trend_flow.get_database_settings"), \
         patch("local_newsifier.flows.analysis.headline_trend_flow.init_db"), \
         patch("local_newsifier.flows.analysis.headline_trend_flow.get_session") as mock_get_session:
        
        mock_session = MagicMock()
        mock_session_factory = MagicMock(return_value=mock_session)
        mock_get_session.return_value = mock_session_factory
        
        flow = HeadlineTrendFlow()  # No db_manager provided, so it creates its own
        flow.__del__()
        
        # Session should be closed since we created it
        mock_session.close.assert_called_once() 
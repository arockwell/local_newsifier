"""Tests for the TrendAnalysisFlow."""

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest

from local_newsifier.flows.trend_analysis_flow import TrendAnalysisFlow
from local_newsifier.tools.trend_reporter import ReportFormat
from local_newsifier.models.state import AnalysisStatus, TrendAnalysisState
from local_newsifier.models.trend import (
    TimeFrame, TrendAnalysis, TrendAnalysisConfig, TrendStatus, TrendType
)


@pytest.fixture
def mock_tools():
    """Fixture for mocked tools used by the flow."""
    data_aggregator = MagicMock()
    topic_analyzer = MagicMock()
    trend_detector = MagicMock()
    reporter = MagicMock()

    return {
        "data_aggregator": data_aggregator,
        "topic_analyzer": topic_analyzer,
        "trend_detector": trend_detector,
        "reporter": reporter,
    }


@pytest.fixture(autouse=True)
def mock_dependencies():
    """Fixture to mock dependencies."""
    # Only mock AnalysisService since that's what the implementation uses
    with patch("local_newsifier.services.analysis_service.AnalysisService") as mock_service, \
         patch("local_newsifier.tools.trend_reporter.TrendReporter") as mock_reporter:

        mock_service.return_value = MagicMock()
        mock_reporter.return_value = MagicMock()

        # Create mocks for the tool objects that will be returned during imports
        mock_data_aggregator = MagicMock()
        mock_topic_analyzer = MagicMock()
        mock_trend_detector = MagicMock()

        yield {
            "service": mock_service,
            "reporter": mock_reporter,
            "data_aggregator": mock_data_aggregator,
            "topic_analyzer": mock_topic_analyzer,
            "trend_detector": mock_trend_detector
        }


@pytest.fixture
def sample_trends():
    """Fixture providing sample trend data."""
    now = datetime.now(timezone.utc)

    # Create trends
    trend1 = TrendAnalysis(
        trend_type=TrendType.EMERGING_TOPIC,
        name="Downtown Development",
        description="Increasing coverage of downtown development project",
        status=TrendStatus.CONFIRMED,
        confidence_score=0.85,
        start_date=now,
    )

    trend2 = TrendAnalysis(
        trend_type=TrendType.NOVEL_ENTITY,
        name="New Business Association",
        description="New organization advocating for local businesses",
        status=TrendStatus.POTENTIAL,
        confidence_score=0.75,
        start_date=now,
    )

    return [trend1, trend2]


def test_trend_analysis_state_init():
    """Test TrendAnalysisState initialization."""
    # Test with default config
    state = TrendAnalysisState()
    assert state.status == AnalysisStatus.INITIALIZED
    assert state.detected_trends == []
    assert state.logs == []
    assert state.report_path is None
    assert state.error is None
    assert isinstance(state.config, TrendAnalysisConfig)

    # Test with custom config
    config = TrendAnalysisConfig(
        time_frame=TimeFrame.MONTHLY,
        min_articles=5,
    )
    state = TrendAnalysisState(config=config)
    assert state.config.time_frame == TimeFrame.MONTHLY
    assert state.config.min_articles == 5


def test_trend_analysis_state_methods():
    """Test TrendAnalysisState methods."""
    state = TrendAnalysisState()

    # Test add_log method
    state.add_log("Test log message")
    assert len(state.logs) == 1
    assert "Test log message" in state.logs[0]

    # Test set_error method
    state.set_error("Test error message")
    assert state.error == "Test error message"
    assert len(state.logs) == 2
    assert "ERROR: Test error message" in state.logs[1]


def test_trend_analysis_flow_init(mock_dependencies):
    """Test TrendAnalysisFlow initialization."""
    # Test with default parameters
    flow = TrendAnalysisFlow()
    
    # Test with explicit dependencies
    mock_analysis_service = MagicMock()
    mock_trend_detector = MagicMock()
    
    flow = TrendAnalysisFlow(
        analysis_service=mock_analysis_service,
        trend_detector=mock_trend_detector
    )
    
    assert flow.analysis_service is mock_analysis_service
    assert flow.trend_detector is mock_trend_detector


def test_analyze_trends(mock_dependencies, sample_trends):
    """Test trend analysis method."""
    # Setup mock dependencies
    mock_trend_detector = MagicMock()
    mock_trend_detector.detect_entity_trends.return_value = sample_trends
    
    mock_analysis_service = MagicMock()
    
    # Create flow with mocked dependencies
    flow = TrendAnalysisFlow(
        analysis_service=mock_analysis_service,
        trend_detector=mock_trend_detector
    )
    
    # Test the analyze_trends method
    result = flow.analyze_trends(
        time_frame="daily",
        trend_types=["ENTITY", "TOPIC"],
        limit=10,
        min_articles=3
    )
    
    # Verify the trend detector was called
    mock_trend_detector.detect_entity_trends.assert_called_once()
    
    # The result should contain the detected trends
    assert "trends" in result
    
    # Test with output format
    mock_trend_reporter = MagicMock()
    mock_trend_reporter.generate_report.return_value = "/path/to/report.md"
    
    flow = TrendAnalysisFlow(
        analysis_service=mock_analysis_service,
        trend_detector=mock_trend_detector,
        trend_reporter=mock_trend_reporter
    )
    
    result = flow.analyze_trends(
        time_frame="daily",
        output_format="markdown",
        output_path="/path/to/output"
    )
    
    # Verify the reporter was called
    mock_trend_reporter.generate_report.assert_called_once()
    assert "report_path" in result


def test_detect_trends(mock_dependencies, sample_trends):
    """Test the _detect_trends internal method."""
    # Setup mocks
    mock_trend_detector = MagicMock()
    mock_trend_detector.detect_entity_trends.return_value = sample_trends
    mock_trend_detector.detect_topic_trends.return_value = []
    mock_trend_detector.detect_sentiment_trends.return_value = []
    mock_trend_detector.detect_keyword_trends.return_value = []
    
    # Create flow with mocked trend detector
    flow = TrendAnalysisFlow(trend_detector=mock_trend_detector)
    
    # Create analysis configuration
    config = TrendAnalysisConfig(
        time_frame=TimeFrame.DAILY,
        trend_types=[TrendType.ENTITY, TrendType.TOPIC],
        limit=10,
        min_articles=3
    )
    
    # Create analysis object
    analysis = TrendAnalysis(
        id="test-analysis",
        config=config,
        status=TrendStatus.PENDING,
        created_at=datetime.now(timezone.utc)
    )
    
    # Call the method
    result = flow._detect_trends(analysis)
    
    # Verify correct methods were called on the trend detector
    mock_trend_detector.detect_entity_trends.assert_called_once()
    mock_trend_detector.detect_topic_trends.assert_called_once()
    
    # The result should contain the detected entity trends
    assert "entity_trends" in result
    assert result["entity_trends"] == sample_trends

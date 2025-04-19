"""Tests for the NewsTrendAnalysisFlow."""

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest

from local_newsifier.flows.trend_analysis_flow import (NewsTrendAnalysisFlow,
                                                         ReportFormat,
                                                         TrendAnalysisState)
from local_newsifier.models.state import AnalysisStatus
from local_newsifier.models.trend import (TimeFrame, TrendAnalysis,
                                            TrendAnalysisConfig, TrendStatus,
                                            TrendType)


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
    with patch("local_newsifier.flows.trend_analysis_flow.HistoricalDataAggregator") as mock_agg, \
         patch("local_newsifier.flows.trend_analysis_flow.TopicFrequencyAnalyzer") as mock_analyzer, \
         patch("local_newsifier.flows.trend_analysis_flow.TrendDetector") as mock_detector, \
         patch("local_newsifier.flows.trend_analysis_flow.TrendReporter") as mock_reporter:
        mock_agg.return_value = MagicMock()
        mock_analyzer.return_value = MagicMock()
        mock_detector.return_value = MagicMock()
        mock_reporter.return_value = MagicMock()
        yield mock_agg, mock_analyzer, mock_detector, mock_reporter


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
        time_frame=TimeFrame.MONTH,
        min_articles=5,
    )
    state = TrendAnalysisState(config=config)
    assert state.config.time_frame == TimeFrame.MONTH
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


def test_news_trend_analysis_flow_init(mock_tools):
    """Test NewsTrendAnalysisFlow initialization."""
    with patch("local_newsifier.flows.trend_analysis_flow.HistoricalDataAggregator") as mock_agg_cls, \
         patch("local_newsifier.flows.trend_analysis_flow.TopicFrequencyAnalyzer") as mock_analyzer_cls, \
         patch("local_newsifier.flows.trend_analysis_flow.TrendDetector") as mock_detector_cls, \
         patch("local_newsifier.flows.trend_analysis_flow.TrendReporter") as mock_reporter_cls:
        
        mock_agg_cls.return_value = mock_tools["data_aggregator"]
        mock_analyzer_cls.return_value = mock_tools["topic_analyzer"]
        mock_detector_cls.return_value = mock_tools["trend_detector"]
        mock_reporter_cls.return_value = mock_tools["reporter"]
        
        # Test with default parameters
        flow = NewsTrendAnalysisFlow()
        assert isinstance(flow.config, TrendAnalysisConfig)
        assert flow.data_aggregator == mock_tools["data_aggregator"]
        assert flow.topic_analyzer == mock_tools["topic_analyzer"]
        assert flow.trend_detector == mock_tools["trend_detector"]
        assert flow.reporter == mock_tools["reporter"]
        
        # Test with custom parameters
        custom_config = TrendAnalysisConfig(
            time_frame=TimeFrame.MONTH,
            min_articles=5,
        )
        flow = NewsTrendAnalysisFlow(config=custom_config, output_dir="custom_output")
        assert flow.config == custom_config
        mock_reporter_cls.assert_called_with(output_dir="custom_output")


def test_aggregate_historical_data(mock_tools):
    """Test historical data aggregation in the flow."""
    with patch("local_newsifier.flows.trend_analysis_flow.HistoricalDataAggregator") as mock_agg_cls, \
         patch("local_newsifier.flows.trend_analysis_flow.TopicFrequencyAnalyzer") as mock_analyzer_cls, \
         patch("local_newsifier.flows.trend_analysis_flow.TrendDetector") as mock_detector_cls, \
         patch("local_newsifier.flows.trend_analysis_flow.TrendReporter") as mock_reporter_cls:
        
        mock_agg_cls.return_value = mock_tools["data_aggregator"]
        mock_analyzer_cls.return_value = mock_tools["topic_analyzer"]
        mock_detector_cls.return_value = mock_tools["trend_detector"]
        mock_reporter_cls.return_value = mock_tools["reporter"]
        
        # Setup data_aggregator mock behavior
        start_date = datetime.now(timezone.utc) - timedelta(days=7)
        end_date = datetime.now(timezone.utc)
        mock_tools["data_aggregator"].calculate_date_range.return_value = (start_date, end_date)
        mock_tools["data_aggregator"].get_articles_in_timeframe.return_value = [MagicMock(), MagicMock()]
        
        flow = NewsTrendAnalysisFlow()
        state = TrendAnalysisState()
        
        # Test successful data aggregation
        result = flow.aggregate_historical_data(state)
        
        assert result.status == AnalysisStatus.SCRAPE_SUCCEEDED
        assert len(result.logs) > 0
        mock_tools["data_aggregator"].calculate_date_range.assert_called_once()
        mock_tools["data_aggregator"].get_articles_in_timeframe.assert_called_once()
        mock_tools["data_aggregator"].get_entity_frequencies.assert_called_once()
        
        # Test failure case
        mock_tools["data_aggregator"].get_articles_in_timeframe.side_effect = Exception("Test error")
        result = flow.aggregate_historical_data(state)
        
        assert result.status == AnalysisStatus.SCRAPE_FAILED_NETWORK
        assert result.error is not None
        assert "Test error" in result.error


def test_detect_trends(mock_tools, sample_trends):
    """Test trend detection in the flow."""
    with patch("local_newsifier.flows.trend_analysis_flow.HistoricalDataAggregator") as mock_agg_cls, \
         patch("local_newsifier.flows.trend_analysis_flow.TopicFrequencyAnalyzer") as mock_analyzer_cls, \
         patch("local_newsifier.flows.trend_analysis_flow.TrendDetector") as mock_detector_cls, \
         patch("local_newsifier.flows.trend_analysis_flow.TrendReporter") as mock_reporter_cls:
        
        mock_agg_cls.return_value = mock_tools["data_aggregator"]
        mock_analyzer_cls.return_value = mock_tools["topic_analyzer"]
        mock_detector_cls.return_value = mock_tools["trend_detector"]
        mock_reporter_cls.return_value = mock_tools["reporter"]
        
        # Setup trend_detector mock behavior
        mock_tools["trend_detector"].detect_entity_trends.return_value = sample_trends
        mock_tools["trend_detector"].detect_anomalous_patterns.return_value = []
        
        flow = NewsTrendAnalysisFlow()
        state = TrendAnalysisState()
        
        # Test successful trend detection
        result = flow.detect_trends(state)
        
        assert result.status == AnalysisStatus.ANALYSIS_SUCCEEDED
        assert len(result.logs) > 0
        assert result.detected_trends == sample_trends
        mock_tools["trend_detector"].detect_entity_trends.assert_called_once()
        mock_tools["trend_detector"].detect_anomalous_patterns.assert_called_once()
        
        # Test failure case
        mock_tools["trend_detector"].detect_entity_trends.side_effect = Exception("Test error")
        result = flow.detect_trends(state)
        
        assert result.status == AnalysisStatus.ANALYSIS_FAILED
        assert result.error is not None
        assert "Test error" in result.error


def test_generate_report(mock_tools, sample_trends):
    """Test report generation in the flow."""
    with patch("local_newsifier.flows.trend_analysis_flow.HistoricalDataAggregator") as mock_agg_cls, \
         patch("local_newsifier.flows.trend_analysis_flow.TopicFrequencyAnalyzer") as mock_analyzer_cls, \
         patch("local_newsifier.flows.trend_analysis_flow.TrendDetector") as mock_detector_cls, \
         patch("local_newsifier.flows.trend_analysis_flow.TrendReporter") as mock_reporter_cls:
        
        mock_agg_cls.return_value = mock_tools["data_aggregator"]
        mock_analyzer_cls.return_value = mock_tools["topic_analyzer"]
        mock_detector_cls.return_value = mock_tools["trend_detector"]
        mock_reporter_cls.return_value = mock_tools["reporter"]
        
        # Setup reporter mock behavior
        mock_tools["reporter"].save_report.return_value = "/path/to/report.md"
        
        flow = NewsTrendAnalysisFlow()
        
        # Test with trends
        state = TrendAnalysisState()
        state.detected_trends = sample_trends
        
        result = flow.generate_report(state, format=ReportFormat.MARKDOWN)
        
        assert result.status == AnalysisStatus.SAVE_SUCCEEDED
        assert result.report_path == "/path/to/report.md"
        mock_tools["reporter"].save_report.assert_called_once()
        
        # Test with no trends
        state = TrendAnalysisState()
        state.detected_trends = []
        
        result = flow.generate_report(state)
        
        assert result.status == AnalysisStatus.SAVE_SUCCEEDED
        assert result.report_path is None
        
        # Test failure case
        state.detected_trends = sample_trends
        mock_tools["reporter"].save_report.side_effect = Exception("Test error")
        result = flow.generate_report(state)
        
        assert result.status == AnalysisStatus.SAVE_FAILED
        assert result.error is not None
        assert "Test error" in result.error


def test_run_analysis(mock_tools, sample_trends):
    """Test running the complete analysis flow."""
    with patch("local_newsifier.flows.trend_analysis_flow.HistoricalDataAggregator") as mock_agg_cls, \
         patch("local_newsifier.flows.trend_analysis_flow.TopicFrequencyAnalyzer") as mock_analyzer_cls, \
         patch("local_newsifier.flows.trend_analysis_flow.TrendDetector") as mock_detector_cls, \
         patch("local_newsifier.flows.trend_analysis_flow.TrendReporter") as mock_reporter_cls, \
         patch("local_newsifier.flows.trend_analysis_flow.NewsTrendAnalysisFlow.aggregate_historical_data") as mock_aggregate, \
         patch("local_newsifier.flows.trend_analysis_flow.NewsTrendAnalysisFlow.detect_trends") as mock_detect, \
         patch("local_newsifier.flows.trend_analysis_flow.NewsTrendAnalysisFlow.generate_report") as mock_generate:
        
        mock_agg_cls.return_value = mock_tools["data_aggregator"]
        mock_analyzer_cls.return_value = mock_tools["topic_analyzer"]
        mock_detector_cls.return_value = mock_tools["trend_detector"]
        mock_reporter_cls.return_value = mock_tools["reporter"]
        
        # Setup method mock behaviors for success case
        def aggregate_success(state):
            state.status = AnalysisStatus.SCRAPE_SUCCEEDED
            return state
            
        def detect_success(state):
            state.status = AnalysisStatus.ANALYSIS_SUCCEEDED
            state.detected_trends = sample_trends
            return state
            
        def generate_success(state, format=None):
            state.status = AnalysisStatus.SAVE_SUCCEEDED
            state.report_path = "/path/to/report.md"
            return state
            
        mock_aggregate.side_effect = aggregate_success
        mock_detect.side_effect = detect_success
        mock_generate.side_effect = generate_success
        
        flow = NewsTrendAnalysisFlow()
        
        # Test successful complete flow
        result = flow.run_analysis()
        
        assert result.status == AnalysisStatus.COMPLETED_SUCCESS
        assert len(result.logs) > 0
        assert result.detected_trends == sample_trends
        assert result.report_path == "/path/to/report.md"
        mock_aggregate.assert_called_once()
        mock_detect.assert_called_once()
        mock_generate.assert_called_once()
        
        # Test flow with aggregation failure
        def aggregate_failure(state):
            state.status = AnalysisStatus.SCRAPE_FAILED_NETWORK
            state.set_error("Aggregation error")
            return state
            
        mock_aggregate.side_effect = aggregate_failure
        result = flow.run_analysis()
        
        assert result.status == AnalysisStatus.SCRAPE_FAILED_NETWORK
        assert "Aggregation error" in result.error
        assert "Aborting flow due to data aggregation failure" in result.logs[-1]
        
        # Test flow with detection failure
        mock_aggregate.side_effect = aggregate_success
        
        def detect_failure(state):
            state.status = AnalysisStatus.ANALYSIS_FAILED
            state.set_error("Detection error")
            return state
            
        mock_detect.side_effect = detect_failure
        result = flow.run_analysis()
        
        assert result.status == AnalysisStatus.ANALYSIS_FAILED
        assert "Detection error" in result.error
        assert "Aborting flow due to trend detection failure" in result.logs[-1]
        
        # Test flow with report generation failure
        mock_detect.side_effect = detect_success
        
        def generate_failure(state, format=None):
            state.status = AnalysisStatus.SAVE_FAILED
            state.set_error("Report generation error")
            return state
            
        mock_generate.side_effect = generate_failure
        result = flow.run_analysis()
        
        assert result.status == AnalysisStatus.COMPLETED_WITH_ERRORS
        assert "Report generation error" in result.error
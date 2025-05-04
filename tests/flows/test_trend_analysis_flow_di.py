"""Tests for the NewsTrendAnalysisFlow with dependency injection."""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi_injectable import injectable
from sqlmodel import Session

from local_newsifier.flows.trend_analysis_flow import (NewsTrendAnalysisFlowBase as NewsTrendAnalysisFlow,
                                                    TrendAnalysisState,
                                                    ReportFormat)
from local_newsifier.models.state import AnalysisStatus
from local_newsifier.models.trend import (TrendAnalysis, TrendType,
                                        TrendAnalysisConfig, TrendStatus)


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


class MockAnalysisService:
    """Mock AnalysisService for testing."""
    
    def __init__(self, *args, **kwargs):
        """Initialize with mocked methods."""
        self.detect_entity_trends = MagicMock()
        self._get_session = MagicMock(return_value=Session())


class MockTrendReporter:
    """Mock TrendReporter for testing."""
    
    def __init__(self, *args, **kwargs):
        """Initialize with mocked methods."""
        self.generate_trend_summary = MagicMock(return_value="Trend summary content")
        self.save_report = MagicMock(return_value="/path/to/mock_report.md")


class MockTrendAnalyzer:
    """Mock TrendAnalyzer for testing."""
    
    def __init__(self, *args, **kwargs):
        """Initialize with mocked methods."""
        self.detect_entity_trends = MagicMock()
        self.detect_anomalous_patterns = MagicMock()
        self.extract_keywords = MagicMock()


@pytest.fixture
def mock_di_providers():
    """Mock the DI providers for testing."""
    with patch("local_newsifier.di.providers.get_analysis_service") as mock_get_analysis_service, \
         patch("local_newsifier.di.providers.get_trend_reporter_tool") as mock_get_trend_reporter, \
         patch("local_newsifier.di.providers.get_trend_analyzer_tool") as mock_get_trend_analyzer:
        
        # Create instances of our mock classes
        mock_analysis_service = MockAnalysisService()
        mock_trend_reporter = MockTrendReporter()
        mock_trend_analyzer = MockTrendAnalyzer()
        
        # Configure the provider mock return values
        mock_get_analysis_service.return_value = mock_analysis_service
        mock_get_trend_reporter.return_value = mock_trend_reporter
        mock_get_trend_analyzer.return_value = mock_trend_analyzer
        
        yield {
            "analysis_service": mock_analysis_service,
            "trend_reporter": mock_trend_reporter,
            "trend_analyzer": mock_trend_analyzer
        }


def test_flow_di_initialization(mock_di_providers):
    """Test that the flow can be initialized with dependency injection."""
    # Since our class uses @injectable, we'll create a direct instance
    # This test verifies the mocks are working, not testing the injector directly
    flow = NewsTrendAnalysisFlow(
        analysis_service=mock_di_providers["analysis_service"],
        trend_reporter=mock_di_providers["trend_reporter"],
        trend_analyzer=mock_di_providers["trend_analyzer"]
    )
    
    # Check that dependencies were properly injected
    assert flow.analysis_service is mock_di_providers["analysis_service"]
    assert flow.reporter is mock_di_providers["trend_reporter"]
    assert flow.trend_detector is mock_di_providers["trend_analyzer"]
    
    # Check that other properties are initialized correctly
    assert isinstance(flow.config, TrendAnalysisConfig)


def test_flow_di_detect_trends(mock_di_providers, sample_trends):
    """Test trend detection with DI-based flow."""
    # Setup the mock trend analyzer to return sample trends
    mock_di_providers["trend_analyzer"].detect_entity_trends.return_value = sample_trends
    mock_di_providers["trend_analyzer"].detect_anomalous_patterns.return_value = []
    
    # Create a flow instance directly with mocked dependencies
    flow = NewsTrendAnalysisFlow(
        analysis_service=mock_di_providers["analysis_service"],
        trend_reporter=mock_di_providers["trend_reporter"],
        trend_analyzer=mock_di_providers["trend_analyzer"]
    )
    
    # Create a state and run trend detection
    state = TrendAnalysisState()
    result = flow.detect_trends(state)
    
    # Verify the result
    assert result.status == AnalysisStatus.ANALYSIS_SUCCEEDED
    assert result.detected_trends == sample_trends
    assert len(result.logs) > 0
    
    # Verify that the trend analyzer was called with expected arguments
    mock_di_providers["trend_analyzer"].detect_entity_trends.assert_called_once()
    call_args = mock_di_providers["trend_analyzer"].detect_entity_trends.call_args[1]
    assert "entity_types" in call_args
    assert "min_significance" in call_args
    assert "min_mentions" in call_args
    assert "max_trends" in call_args


def test_flow_di_generate_report(mock_di_providers, sample_trends):
    """Test report generation with DI-based flow."""
    # Setup the mock trend reporter
    mock_di_providers["trend_reporter"].save_report.return_value = "/path/to/di_report.md"
    
    # Create a flow instance directly with mocked dependencies
    flow = NewsTrendAnalysisFlow(
        analysis_service=mock_di_providers["analysis_service"],
        trend_reporter=mock_di_providers["trend_reporter"],
        trend_analyzer=mock_di_providers["trend_analyzer"]
    )
    
    # Create a state with detected trends and generate report
    state = TrendAnalysisState()
    state.detected_trends = sample_trends
    result = flow.generate_report(state)
    
    # Verify the result
    assert result.status == AnalysisStatus.SAVE_SUCCEEDED
    assert result.report_path == "/path/to/di_report.md"
    assert len(result.logs) > 0
    
    # Verify that the trend reporter was called with expected arguments
    mock_di_providers["trend_reporter"].save_report.assert_called_once_with(
        sample_trends, format=ReportFormat.MARKDOWN
    )


def test_flow_di_run_analysis(mock_di_providers, sample_trends):
    """Test running the complete analysis flow with DI."""
    # Setup mocks
    mock_di_providers["trend_analyzer"].detect_entity_trends.return_value = sample_trends
    mock_di_providers["trend_reporter"].save_report.return_value = "/path/to/full_report.md"
    
    # Create a flow instance directly with mocked dependencies
    flow = NewsTrendAnalysisFlow(
        analysis_service=mock_di_providers["analysis_service"],
        trend_reporter=mock_di_providers["trend_reporter"],
        trend_analyzer=mock_di_providers["trend_analyzer"]
    )
    
    # Setup method patches to test the full flow
    with patch.object(flow, 'aggregate_historical_data') as mock_aggregate, \
         patch.object(flow, 'detect_trends') as mock_detect, \
         patch.object(flow, 'generate_report') as mock_generate:
        
        # Define success behaviors for patched methods
        def aggregate_success(state):
            state.status = AnalysisStatus.SCRAPE_SUCCEEDED
            return state
            
        def detect_success(state):
            state.status = AnalysisStatus.ANALYSIS_SUCCEEDED
            state.detected_trends = sample_trends
            return state
            
        def generate_success(state, format=None):
            state.status = AnalysisStatus.SAVE_SUCCEEDED
            state.report_path = "/path/to/full_report.md"
            return state
            
        mock_aggregate.side_effect = aggregate_success
        mock_detect.side_effect = detect_success
        mock_generate.side_effect = generate_success
        
        # Run the flow
        result = flow.run_analysis()
        
        # Verify full flow execution
        assert result.status == AnalysisStatus.COMPLETED_SUCCESS
        assert result.detected_trends == sample_trends
        assert result.report_path == "/path/to/full_report.md"
        mock_aggregate.assert_called_once()
        mock_detect.assert_called_once()
        mock_generate.assert_called_once()


def test_flow_di_fallbacks(mock_di_providers, sample_trends):
    """Test that DI flow uses fallbacks appropriately when needed."""
    # Setup special case where trend_detector doesn't have required methods
    # This tests the fallback to analysis_service
    mock_trend_analyzer = mock_di_providers["trend_analyzer"]
    
    # Need to update how we simulate missing methods - retain the instance but make detect_entity_trends check work
    # Instead of removing the method entirely, create a new instance that behaves differently
    class ModifiedMockAnalyzer:
        def __init__(self):
            pass
            
    # Use this mock which has no detect_entity_trends method
    modified_analyzer = ModifiedMockAnalyzer()
    
    mock_di_providers["analysis_service"].detect_entity_trends.return_value = sample_trends
    
    # Create a flow instance directly with mocked dependencies
    flow = NewsTrendAnalysisFlow(
        analysis_service=mock_di_providers["analysis_service"],
        trend_reporter=mock_di_providers["trend_reporter"],
        trend_analyzer=modified_analyzer
    )
    
    # Create a state and run trend detection
    state = TrendAnalysisState()
    result = flow.detect_trends(state)
    
    # Verify the result uses fallback to analysis_service
    assert result.status == AnalysisStatus.ANALYSIS_SUCCEEDED
    assert result.detected_trends == sample_trends
    
    # Verify that analysis_service was called with expected arguments
    mock_di_providers["analysis_service"].detect_entity_trends.assert_called_once()
    call_args = mock_di_providers["analysis_service"].detect_entity_trends.call_args[1]
    assert "entity_types" in call_args
    assert "time_frame" in call_args
    assert "min_significance" in call_args
    assert "min_mentions" in call_args
    assert "max_trends" in call_args
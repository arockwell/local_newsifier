"""Flow for analyzing and detecting trends in local news articles."""

from datetime import datetime, timezone, timedelta
import logging
from enum import Enum
from typing import Any, Dict, List, Optional, Union, Annotated
from unittest.mock import MagicMock
from uuid import UUID, uuid4

from crewai import Flow
from fastapi import Depends
from fastapi_injectable import injectable

from local_newsifier.models.state import AnalysisStatus
from local_newsifier.models.trend import (
    TimeFrame,
    TrendAnalysis,
    TrendAnalysisConfig,
    TrendStatus,
    TrendType,
)
from local_newsifier.services.analysis_service import AnalysisService
from local_newsifier.tools.trend_reporter import ReportFormat, TrendReporter
from local_newsifier.di.providers import (
    get_analysis_service, get_trend_reporter_tool, get_trend_analyzer_tool
)

# Global logger
logger = logging.getLogger(__name__)


class TrendAnalysisState:
    """State for tracking the trend analysis flow."""

    def __init__(
        self,
        config: Optional[TrendAnalysisConfig] = None,
        run_id: Optional[UUID] = None,
    ):
        """
        Initialize the trend analysis state.

        Args:
            config: Configuration for trend analysis
            run_id: Optional run ID
        """
        self.run_id = run_id or uuid4()
        self.config = config or TrendAnalysisConfig()
        self.start_time = datetime.now(timezone.utc)
        self.status = AnalysisStatus.INITIALIZED
        self.detected_trends: List[TrendAnalysis] = []
        self.logs: List[str] = []
        self.report_path: Optional[str] = None
        self.error: Optional[str] = None

    def add_log(self, message: str) -> None:
        """
        Add a log message with timestamp.

        Args:
            message: Log message
        """
        timestamp = datetime.now(timezone.utc).isoformat()
        self.logs.append(f"[{timestamp}] {message}")

    def set_error(self, error_message: str) -> None:
        """
        Set error message.

        Args:
            error_message: Error message
        """
        self.error = error_message
        self.add_log(f"ERROR: {error_message}")


# Base class without DI for testing
class NewsTrendAnalysisFlowBase(Flow):
    """Base flow for detecting and analyzing trends in local news coverage.
    
    This non-injectable version is used for testing.
    """
    
    def __init__(
        self,
        analysis_service: AnalysisService,
        trend_reporter: TrendReporter,
        trend_analyzer: Any,
        data_aggregator: Optional[Any] = None,
        topic_analyzer: Optional[Any] = None,
        config: Optional[TrendAnalysisConfig] = None,
    ):
        """
        Initialize the trend analysis flow.

        Args:
            analysis_service: Service for analysis operations (injected)
            trend_reporter: Tool for generating trend reports (injected)
            trend_analyzer: Tool for analyzing trends (injected)
            data_aggregator: Tool for aggregating data (for backwards compatibility)
            topic_analyzer: Tool for analyzing topics (for backwards compatibility)
            config: Configuration for trend analysis
        """
        super().__init__()
        self.config = config or TrendAnalysisConfig()
        
        # Use injected services and tools
        self.reporter = trend_reporter
        self.analysis_service = analysis_service
        
        # Initialize trend analyzer via DI 
        self.trend_detector = trend_analyzer
        
        # For backwards compatibility with tests
        self.data_aggregator = data_aggregator or MagicMock()
        self.topic_analyzer = topic_analyzer or MagicMock()
        
    def aggregate_historical_data(
        self, state: TrendAnalysisState
    ) -> TrendAnalysisState:
        """
        Retrieve articles for trend analysis.

        Args:
            state: Current flow state

        Returns:
            Updated state
        """
        try:
            state.status = AnalysisStatus.SCRAPING
            state.add_log("Starting article retrieval for trend analysis")

            # Calculate date range based on configuration
            if state.config.time_frame == TimeFrame.DAY:
                days_back = state.config.lookback_periods
            elif state.config.time_frame == TimeFrame.WEEK:
                days_back = state.config.lookback_periods * 7
            elif state.config.time_frame == TimeFrame.MONTH:
                days_back = state.config.lookback_periods * 30
            else:
                days_back = 90  # Default to 90 days

            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(days=days_back)

            # Add a log of the date range
            state.add_log(
                f"Analyzing trends from {start_date.isoformat()} to {end_date.isoformat()}"
            )
            
            state.start_date = start_date
            state.end_date = end_date
            state.status = AnalysisStatus.SCRAPE_SUCCEEDED
            state.add_log("Successfully completed article retrieval")

        except Exception as e:
            state.status = AnalysisStatus.SCRAPE_FAILED_NETWORK
            state.set_error(f"Error during article retrieval: {str(e)}")

        return state

    def detect_trends(self, state: TrendAnalysisState) -> TrendAnalysisState:
        """
        Detect trends in the historical data.

        Args:
            state: Current flow state

        Returns:
            Updated state
        """
        try:
            state.status = AnalysisStatus.ANALYZING
            state.add_log("Starting trend detection")

            # Calculate date range based on configuration
            end_date = datetime.now(timezone.utc)
            if state.config.time_frame == TimeFrame.DAY:
                start_date = end_date - timedelta(days=1)
            elif state.config.time_frame == TimeFrame.WEEK:
                start_date = end_date - timedelta(days=7)
            elif state.config.time_frame == TimeFrame.MONTH:
                start_date = end_date - timedelta(days=30)
            else:
                start_date = end_date - timedelta(days=90)
                
            state.add_log(f"Analyzing trends from {start_date.isoformat()} to {end_date.isoformat()}")
            
            # Detect entity-based trends using TrendAnalyzer via DI
            # If this is a proper TrendAnalyzer instance
            if hasattr(self.trend_detector, 'detect_entity_trends'):
                entity_trends = self.trend_detector.detect_entity_trends(
                    entity_types=state.config.entity_types,
                    min_significance=state.config.significance_threshold,
                    min_mentions=state.config.min_articles,
                    max_trends=state.config.topic_limit
                )
                
                # Try to detect anomalous patterns
                if hasattr(self.trend_detector, 'detect_anomalous_patterns'):
                    anomaly_trends = self.trend_detector.detect_anomalous_patterns()
            else:
                # Fallback to using analysis_service directly
                entity_trends = self.analysis_service.detect_entity_trends(
                    entity_types=state.config.entity_types,
                    time_frame=state.config.time_frame,
                    min_significance=state.config.significance_threshold,
                    min_mentions=state.config.min_articles,
                    max_trends=state.config.topic_limit
                )

            # Store the trends
            state.detected_trends = entity_trends

            state.add_log(f"Detected {len(state.detected_trends)} trends")
            state.status = AnalysisStatus.ANALYSIS_SUCCEEDED

        except Exception as e:
            state.status = AnalysisStatus.ANALYSIS_FAILED
            state.set_error(f"Error during trend detection: {str(e)}")
            logger.exception("Error during trend detection")

        return state

    def generate_report(
        self, state: TrendAnalysisState, format: ReportFormat = ReportFormat.MARKDOWN
    ) -> TrendAnalysisState:
        """
        Generate a report of detected trends.

        Args:
            state: Current flow state
            format: Report format

        Returns:
            Updated state
        """
        try:
            state.status = AnalysisStatus.SAVING
            state.add_log(f"Generating {format.value} trend report")

            if not state.detected_trends:
                state.add_log("No trends to report")
                state.report_path = None
                state.status = AnalysisStatus.SAVE_SUCCEEDED
                return state

            # Generate and save report
            state.report_path = self.reporter.save_report(
                state.detected_trends, format=format
            )

            state.add_log(f"Saved trend report to {state.report_path}")
            state.status = AnalysisStatus.SAVE_SUCCEEDED

        except Exception as e:
            state.status = AnalysisStatus.SAVE_FAILED
            state.set_error(f"Error generating trend report: {str(e)}")

        return state

    def run_analysis(
        self,
        config: Optional[TrendAnalysisConfig] = None,
        report_format: ReportFormat = ReportFormat.MARKDOWN,
    ) -> TrendAnalysisState:
        """
        Run the full trend analysis flow.

        Args:
            config: Optional custom configuration
            report_format: Format for the final report

        Returns:
            Flow state with results
        """
        # Initialize state
        state = TrendAnalysisState(config or self.config)
        state.add_log("Starting trend analysis flow")

        # Execute pipeline
        state = self.aggregate_historical_data(state)
        if state.status != AnalysisStatus.SCRAPE_SUCCEEDED:
            state.add_log("Aborting flow due to article retrieval failure")
            return state

        state = self.detect_trends(state)
        if state.status != AnalysisStatus.ANALYSIS_SUCCEEDED:
            state.add_log("Aborting flow due to trend detection failure")
            return state

        state = self.generate_report(state, format=report_format)

        if state.status == AnalysisStatus.SAVE_SUCCEEDED:
            state.status = AnalysisStatus.COMPLETED_SUCCESS
            state.add_log("Successfully completed trend analysis flow")
        else:
            state.status = AnalysisStatus.COMPLETED_WITH_ERRORS
            state.add_log("Completed trend analysis flow with errors")

        return state

@injectable(use_cache=False)
class NewsTrendAnalysisFlow(NewsTrendAnalysisFlowBase):
    """Flow for detecting and analyzing trends in local news coverage.
    
    This version uses dependency injection.
    """
    
    def __init__(
        self,
        analysis_service: Annotated[AnalysisService, Depends(get_analysis_service)],
        trend_reporter: Annotated[TrendReporter, Depends(get_trend_reporter_tool)],
        trend_analyzer: Annotated[Any, Depends(get_trend_analyzer_tool)],
        data_aggregator: Optional[Any] = None,
        topic_analyzer: Optional[Any] = None,
        config: Optional[TrendAnalysisConfig] = None,
    ):
        """
        Initialize the trend analysis flow.

        Args:
            analysis_service: Service for analysis operations (injected)
            trend_reporter: Tool for generating trend reports (injected)
            trend_analyzer: Tool for analyzing trends (injected)
            data_aggregator: Tool for aggregating data (for backwards compatibility)
            topic_analyzer: Tool for analyzing topics (for backwards compatibility)
            config: Configuration for trend analysis
        """
        super().__init__(
            analysis_service=analysis_service,
            trend_reporter=trend_reporter,
            trend_analyzer=trend_analyzer,
            data_aggregator=data_aggregator,
            topic_analyzer=topic_analyzer,
            config=config
        )

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
from sqlmodel import Session

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


@injectable(use_cache=False)
class NewsTrendAnalysisFlow(Flow):
    """Flow for detecting and analyzing trends in local news coverage."""

    def __init__(
        self,
        analysis_service: Optional[AnalysisService] = None,
        trend_reporter: Optional[TrendReporter] = None,
        data_aggregator: Optional[Any] = None,
        topic_analyzer: Optional[Any] = None,
        trend_detector: Optional[Any] = None,
        session: Optional[Session] = None,
        config: Optional[TrendAnalysisConfig] = None,
        output_dir: str = "trend_output"
    ):
        """
        Initialize the trend analysis flow.

        Args:
            analysis_service: Service for analysis operations
            trend_reporter: Tool for generating trend reports
            data_aggregator: Tool for aggregating data (for backwards compatibility)
            topic_analyzer: Tool for analyzing topics (for backwards compatibility)
            trend_detector: Tool for detecting trends (for backwards compatibility)
            session: Database session
            config: Configuration for trend analysis
            output_dir: Directory for report output
        """
        super().__init__()
        self.config = config or TrendAnalysisConfig()
        self.session = session
        
        # Initialize reporter
        self.reporter = trend_reporter or TrendReporter(output_dir=output_dir)
        
        # Use analysis service for all trend analysis operations 
        self.analysis_service = analysis_service or AnalysisService()
        
        # For backwards compatibility with tests
        self.data_aggregator = data_aggregator or MagicMock()
        self.topic_analyzer = topic_analyzer or MagicMock()
        self.trend_detector = trend_detector or MagicMock()
        
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

            # Detect entity-based trends using TrendDetector
            entity_trends = self.trend_detector.detect_entity_trends(
                entity_types=state.config.entity_types,
                min_significance=state.config.significance_threshold,
                min_mentions=state.config.min_articles,
                max_trends=state.config.topic_limit,
                session=self.analysis_service._get_session()
            )
            
            # Detect anomalous patterns
            anomaly_trends = self.trend_detector.detect_anomalous_patterns()

            # Store the trends
            state.detected_trends = entity_trends

            state.add_log(f"Detected {len(state.detected_trends)} trends")
            state.status = AnalysisStatus.ANALYSIS_SUCCEEDED

        except Exception as e:
            state.status = AnalysisStatus.ANALYSIS_FAILED
            state.set_error(f"Error during trend detection: {str(e)}")

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

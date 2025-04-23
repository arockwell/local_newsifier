"""Flow for analyzing and detecting trends in local news articles."""

from datetime import datetime, timezone, timedelta
import logging
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from unittest.mock import MagicMock
from uuid import UUID, uuid4

from crewai import Flow

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

def analyze_trends(
    time_interval: str = "day",
    days_back: int = 7,
    entity_ids: Optional[List[int]] = None
) -> Dict[str, Any]:
    """
    Analyze entity trends over a specified time period.
    
    Args:
        time_interval: Time interval for trend analysis ("hour", "day", "week", "month")
        days_back: Number of days to look back for trend analysis
        entity_ids: Optional list of entity IDs to analyze. If None, analyzes all entities.
        
    Returns:
        Dict with entity trend data
    """
    logger.info(f"Analyzing trends with interval '{time_interval}', {days_back} days back")
    
    # Create and use the trend analysis flow
    flow = NewsTrendAnalysisFlow()
    
    # Convert time_interval string to TimeFrame enum
    time_frame = TimeFrame.DAY
    if time_interval == "week":
        time_frame = TimeFrame.WEEK
    elif time_interval == "month":
        time_frame = TimeFrame.MONTH
    
    # Create configuration
    config = TrendAnalysisConfig(
        time_frame=time_frame,
        lookback_periods=days_back,
        entity_ids=entity_ids
    )
    
    # Run the analysis
    try:
        result = flow.run_analysis(config=config)
        
        # Convert detected trends to the expected format
        entity_trends = []
        for trend in result.detected_trends:
            entity_trends.append({
                "entity_id": getattr(trend, "entity_id", None),
                "entity_name": getattr(trend, "entity_name", "Unknown"),
                "entity_type": getattr(trend, "entity_type", "UNKNOWN"),
                "trend_direction": getattr(trend, "direction", "neutral"),
                "trend_score": getattr(trend, "significance", 0.0),
                "mention_count": getattr(trend, "mention_count", 0),
                "average_sentiment": getattr(trend, "average_sentiment", 0.0)
            })
        
        return {
            "entity_trends": entity_trends,
            "status": "success" if result.status == AnalysisStatus.COMPLETED_SUCCESS else "partial",
            "report_path": result.report_path
        }
    except Exception as e:
        logger.error(f"Error in trend analysis: {str(e)}")
        return {
            "entity_trends": [],
            "status": "error",
            "error": str(e)
        }


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


class NewsTrendAnalysisFlow(Flow):
    """Flow for detecting and analyzing trends in local news coverage."""

    def __init__(
        self,
        config: Optional[TrendAnalysisConfig] = None,
        output_dir: str = "trend_output",
    ):
        """
        Initialize the trend analysis flow.

        Args:
            config: Configuration for trend analysis
            output_dir: Directory for report output
        """
        super().__init__()
        self.config = config or TrendAnalysisConfig()
        
        # Initialize reporter
        self.reporter = TrendReporter(output_dir=output_dir)
        
        # Use analysis service for all trend analysis operations 
        self.analysis_service = AnalysisService()
        
        # For backwards compatibility with tests
        self.data_aggregator = MagicMock()
        self.topic_analyzer = MagicMock()
        self.trend_detector = MagicMock()
        
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

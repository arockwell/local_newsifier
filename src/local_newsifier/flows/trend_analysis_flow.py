"""Flow for analyzing and detecting trends in local news articles."""

from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Union
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
from local_newsifier.tools.historical_aggregator import HistoricalDataAggregator
from local_newsifier.tools.topic_analyzer import TopicFrequencyAnalyzer
from local_newsifier.tools.trend_detector import TrendDetector
from local_newsifier.tools.trend_reporter import ReportFormat, TrendReporter


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
        self.data_aggregator = HistoricalDataAggregator()
        self.topic_analyzer = TopicFrequencyAnalyzer(self.data_aggregator)
        self.trend_detector = TrendDetector(self.topic_analyzer, self.data_aggregator)
        self.reporter = TrendReporter(output_dir=output_dir)

    def aggregate_historical_data(
        self, state: TrendAnalysisState
    ) -> TrendAnalysisState:
        """
        Aggregate historical data for trend analysis.

        Args:
            state: Current flow state

        Returns:
            Updated state
        """
        try:
            state.status = AnalysisStatus.SCRAPING
            state.add_log("Starting historical data aggregation")

            start_date, end_date = self.data_aggregator.calculate_date_range(
                state.config.time_frame, state.config.lookback_periods
            )

            # Pre-cache the articles for the analysis
            articles = self.data_aggregator.get_articles_in_timeframe(
                start_date, end_date
            )

            state.add_log(
                f"Retrieved {len(articles)} articles from "
                f"{start_date.isoformat()} to {end_date.isoformat()}"
            )

            # Warm up the frequency cache
            self.data_aggregator.get_entity_frequencies(
                state.config.entity_types, start_date, end_date
            )

            state.status = AnalysisStatus.SCRAPE_SUCCEEDED
            state.add_log("Successfully completed historical data aggregation")

        except Exception as e:
            state.status = AnalysisStatus.SCRAPE_FAILED_NETWORK
            state.set_error(f"Error during historical data aggregation: {str(e)}")

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

            # Detect entity-based trends
            entity_trends = self.trend_detector.detect_entity_trends(
                entity_types=state.config.entity_types,
                min_significance=state.config.significance_threshold,
                min_mentions=state.config.min_articles,
                max_trends=state.config.topic_limit,
            )

            # Detect anomalous patterns
            anomaly_trends = self.trend_detector.detect_anomalous_patterns()

            # Combine all trends
            state.detected_trends = entity_trends + anomaly_trends

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
            state.add_log("Aborting flow due to data aggregation failure")
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

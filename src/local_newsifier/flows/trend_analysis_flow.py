"""Flow for analyzing and detecting trends in local news articles."""

from datetime import datetime, timezone, timedelta
import logging
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import UUID, uuid4

from sqlmodel import Session

from local_newsifier.flows.flow_base import FlowBase
from local_newsifier.di.descriptors import Dependency
from local_newsifier.models.state import AnalysisStatus
from local_newsifier.models.trend import (
    TimeFrame,
    TrendAnalysis,
    TrendAnalysisConfig,
    TrendStatus,
    TrendType,
)
from local_newsifier.database.engine import SessionManager
from local_newsifier.tools.trend_reporter import ReportFormat

# Global logger
logger = logging.getLogger(__name__)


class TrendAnalysisFlow(FlowBase):
    """Flow for analyzing trends in news articles.
    
    This implementation uses the simplified DI pattern with descriptors
    for cleaner dependency declaration and resolution.
    """
    
    # Define dependencies using descriptors - these will be lazy-loaded when needed
    analysis_service = Dependency()
    trend_detector = Dependency()
    trend_reporter = Dependency()
    entity_service = Dependency()
    sentiment_analyzer = Dependency()
    session_factory = Dependency(fallback=SessionManager)
    
    def __init__(
        self,
        container=None,
        session: Optional[Session] = None,
        **explicit_deps
    ):
        """Initialize the trend analysis flow.
        
        Args:
            container: Optional DI container for resolving dependencies
            session: Optional database session (for direct use)
            **explicit_deps: Explicit dependencies (overrides container)
        """
        # Initialize the FlowBase
        super().__init__(container, **explicit_deps)
            
        self.session = session
    
    def ensure_dependencies(self) -> None:
        """Ensure all required dependencies are available."""
        # Access dependencies to trigger lazy loading
        assert self.analysis_service is not None, "AnalysisService is required"
        assert self.trend_detector is not None, "TrendDetector is required"
        # Other dependencies will be loaded when needed
    
    def analyze_trends(
        self,
        time_frame: Union[TimeFrame, str] = TimeFrame.DAILY,
        trend_types: Optional[List[Union[TrendType, str]]] = None,
        limit: int = 10,
        min_articles: int = 3,
        output_format: Optional[Union[ReportFormat, str]] = None,
        output_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """Analyze trends across news articles.
        
        Args:
            time_frame: Time frame for trend analysis
            trend_types: Types of trends to analyze (defaults to all)
            limit: Maximum number of trends to return
            min_articles: Minimum number of articles for trend detection
            output_format: Optional format for output report
            output_path: Optional path for output report
            
        Returns:
            Dictionary with trend analysis results
        """
        # Convert string time frame to enum if needed
        if isinstance(time_frame, str):
            time_frame = TimeFrame(time_frame)
        
        # Convert string trend types to enum if needed
        if trend_types:
            enum_trend_types = []
            for trend_type in trend_types:
                if isinstance(trend_type, str):
                    enum_trend_types.append(TrendType(trend_type))
                else:
                    enum_trend_types.append(trend_type)
            trend_types = enum_trend_types
        else:
            # Default to all trend types
            trend_types = list(TrendType)
        
        # Create analysis config
        config = TrendAnalysisConfig(
            time_frame=time_frame,
            trend_types=trend_types,
            limit=limit,
            min_articles=min_articles
        )
        
        # Create analysis ID
        analysis_id = str(uuid4())
        
        # Create analysis object
        analysis = TrendAnalysis(
            id=analysis_id,
            config=config,
            status=TrendStatus.PENDING,
            created_at=datetime.now(timezone.utc)
        )
        
        try:
            # Detect trends
            logger.info(f"Starting trend analysis: {analysis_id}")
            results = self._detect_trends(analysis)
            
            # Generate report if requested
            report_path = None
            if output_format and self.trend_reporter:
                if isinstance(output_format, str):
                    output_format = ReportFormat(output_format)
                
                report_path = self.trend_reporter.generate_report(
                    results,
                    format=output_format,
                    output_path=output_path
                )
            
            # Update analysis status
            analysis.status = TrendStatus.COMPLETED
            analysis.completed_at = datetime.now(timezone.utc)
            
            return {
                "analysis_id": analysis_id,
                "status": analysis.status.value,
                "trends": results,
                "report_path": report_path
            }
        except Exception as e:
            # Handle errors
            logger.error(f"Error in trend analysis {analysis_id}: {str(e)}")
            analysis.status = TrendStatus.FAILED
            analysis.error = str(e)
            
            return {
                "analysis_id": analysis_id,
                "status": analysis.status.value,
                "error": str(e)
            }
    
    def _detect_trends(self, analysis: TrendAnalysis) -> Dict[str, Any]:
        """Internal method to detect trends.
        
        Args:
            analysis: TrendAnalysis configuration object
            
        Returns:
            Dictionary with detected trends by category
        """
        config = analysis.config
        results = {}
        
        # Determine date range based on time frame
        end_date = datetime.now(timezone.utc)
        if config.time_frame == TimeFrame.DAILY:
            start_date = end_date - timedelta(days=1)
        elif config.time_frame == TimeFrame.WEEKLY:
            start_date = end_date - timedelta(days=7)
        elif config.time_frame == TimeFrame.MONTHLY:
            start_date = end_date - timedelta(days=30)
        elif config.time_frame == TimeFrame.QUARTERLY:
            start_date = end_date - timedelta(days=90)
        else:
            start_date = end_date - timedelta(days=1)  # Default to daily
        
        # Check for entity trends
        if TrendType.ENTITY in config.trend_types:
            entity_trends = self.trend_detector.detect_entity_trends(
                start_date=start_date,
                end_date=end_date,
                limit=config.limit,
                min_articles=config.min_articles
            )
            results["entity_trends"] = entity_trends
        
        # Check for topic trends
        if TrendType.TOPIC in config.trend_types:
            topic_trends = self.trend_detector.detect_topic_trends(
                start_date=start_date,
                end_date=end_date,
                limit=config.limit,
                min_articles=config.min_articles
            )
            results["topic_trends"] = topic_trends
        
        # Check for sentiment trends
        if TrendType.SENTIMENT in config.trend_types:
            sentiment_trends = self.trend_detector.detect_sentiment_trends(
                start_date=start_date,
                end_date=end_date,
                limit=config.limit,
                min_articles=config.min_articles
            )
            results["sentiment_trends"] = sentiment_trends
        
        # Check for keyword trends
        if TrendType.KEYWORD in config.trend_types:
            keyword_trends = self.trend_detector.detect_keyword_trends(
                start_date=start_date,
                end_date=end_date,
                limit=config.limit,
                min_articles=config.min_articles
            )
            results["keyword_trends"] = keyword_trends
        
        return results

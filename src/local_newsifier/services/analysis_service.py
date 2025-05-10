"""Service layer for analysis operations."""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Callable

from sqlmodel import Session
from fastapi_injectable import injectable
from typing import Annotated
from fastapi import Depends

from local_newsifier.crud.analysis_result import analysis_result
from local_newsifier.crud.article import article
from local_newsifier.crud.entity import entity
from local_newsifier.database.engine import SessionManager, get_session
from local_newsifier.errors import handle_database
from local_newsifier.models.analysis_result import AnalysisResult
from local_newsifier.models.trend import TrendAnalysis, TimeFrame


@injectable(use_cache=False)
class AnalysisService:
    """Service for analysis operations."""

    def __init__(
        self,
        analysis_result_crud,
        article_crud,
        entity_crud,
        trend_analyzer,
        session_factory: Callable,
    ):
        """Initialize the analysis service.

        Args:
            analysis_result_crud: CRUD component for analysis results
            article_crud: CRUD component for articles
            entity_crud: CRUD component for entities
            trend_analyzer: Tool for trend analysis
            session_factory: Factory function for creating database sessions
        """
        self.analysis_result_crud = analysis_result_crud
        self.article_crud = article_crud
        self.entity_crud = entity_crud
        self.trend_analyzer = trend_analyzer
        self.session_factory = session_factory

    @handle_database
    def analyze_headline_trends(
        self,
        start_date: datetime,
        end_date: datetime,
        time_interval: str = "day",
        top_n: int = 20
    ) -> Dict[str, Any]:
        """Analyze headline trends over the specified time period.

        Args:
            start_date: Start date for analysis
            end_date: End date for analysis
            time_interval: Time interval for grouping ('day', 'week', 'month')
            top_n: Number of top keywords to analyze per period

        Returns:
            Dictionary containing trend analysis results
        """
        with self.session_factory() as session:
            # Use the injected trend analyzer
            trend_analyzer = self.trend_analyzer

            # Get headlines grouped by time interval
            grouped_headlines = self._get_headlines_by_period(
                session, start_date, end_date, time_interval
            )

            if not grouped_headlines:
                return {"error": "No headlines found in the specified period"}

            # Extract keywords for each time interval
            trend_data = {}
            for interval, headlines in grouped_headlines.items():
                trend_data[interval] = trend_analyzer.extract_keywords(headlines, top_n=top_n)

            # Identify trending terms
            trending_terms = trend_analyzer.detect_keyword_trends(trend_data)

            # Calculate overall top terms
            all_headlines = []
            for headlines in grouped_headlines.values():
                all_headlines.extend(headlines)

            overall_top_terms = trend_analyzer.extract_keywords(all_headlines, top_n=top_n)

            result = {
                "trending_terms": trending_terms,
                "overall_top_terms": overall_top_terms,
                "raw_data": trend_data,
                "period_counts": {period: len(headlines) for period, headlines in grouped_headlines.items()}
            }

            return result

    def _get_headlines_by_period(
        self,
        session: Session,
        start_date: datetime,
        end_date: datetime,
        interval: str = "day"
    ) -> Dict[str, List[str]]:
        """Retrieve headlines grouped by time period.

        Args:
            session: Database session
            start_date: Start date for analysis
            end_date: End date for analysis
            interval: Time interval for grouping ('day', 'week', 'month')

        Returns:
            Dictionary mapping time periods to lists of headlines
        """
        # Get all articles in the date range
        articles = self.article_crud.get_by_date_range(
            session, start_date=start_date, end_date=end_date
        )

        # Group by time interval
        grouped_headlines = {}
        for article_obj in articles:
            if not article_obj.title:
                continue

            interval_key = self.trend_analyzer.get_interval_key(article_obj.published_at, interval)

            if interval_key not in grouped_headlines:
                grouped_headlines[interval_key] = []

            grouped_headlines[interval_key].append(article_obj.title)

        return grouped_headlines
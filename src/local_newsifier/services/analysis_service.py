"""Service layer for analysis operations."""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Callable

from sqlmodel import Session
from fastapi_injectable import injectable
from typing import Annotated
from fastapi import Depends

from local_newsifier.models.analysis_result import AnalysisResult
from local_newsifier.models.trend import TrendAnalysis, TimeFrame


@injectable(use_cache=False)
class AnalysisService:
    """Service for analyzing news data and managing analysis results."""

    def __init__(
        self,
        analysis_result_crud,
        article_crud,
        entity_crud,
        trend_analyzer,
        session_factory: Callable
    ):
        """Initialize the analysis service.

        Args:
            analysis_result_crud: CRUD component for analysis results
            article_crud: CRUD component for articles
            entity_crud: CRUD component for entities
            trend_analyzer: Tool for analyzing trends
            session_factory: Factory function for creating database sessions
        """
        self.analysis_result_crud = analysis_result_crud
        self.article_crud = article_crud
        self.entity_crud = entity_crud
        self.trend_analyzer = trend_analyzer
        self.session_factory = session_factory

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
            
            # Save analysis result if needed
            # self._save_analysis_result(session, result)
            
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

    def detect_entity_trends(
        self,
        entity_types: List[str] = None,
        time_frame: TimeFrame = TimeFrame.WEEK,
        min_significance: float = 1.5,
        min_mentions: int = 2,
        max_trends: int = 20
    ) -> List[TrendAnalysis]:
        """Detect trends based on entity frequency analysis.

        Args:
            entity_types: List of entity types to analyze (default: ["PERSON", "ORG", "GPE"])
            time_frame: Time frame for analysis
            min_significance: Minimum significance score for trends
            min_mentions: Minimum number of mentions required
            max_trends: Maximum number of trends to return

        Returns:
            List of detected trends
        """
        if not entity_types:
            entity_types = ["PERSON", "ORG", "GPE"]
            
        with self.session_factory() as session:
            # Use the injected trend analyzer
            trend_analyzer = self.trend_analyzer
            
            # Get start and end dates based on time frame
            end_date = datetime.now()
            if time_frame == TimeFrame.DAY:
                start_date = end_date - timedelta(days=1)
            elif time_frame == TimeFrame.WEEK:
                start_date = end_date - timedelta(weeks=1)
            elif time_frame == TimeFrame.MONTH:
                start_date = end_date - timedelta(days=30)
            else:
                start_date = end_date - timedelta(days=90)
            
            # Get entities in the time range
            entities = self.entity_crud.get_by_date_range_and_types(
                session, 
                start_date=start_date, 
                end_date=end_date,
                entity_types=entity_types
            )
            
            # Get articles in the time range
            articles = self.article_crud.get_by_date_range(
                session, start_date=start_date, end_date=end_date
            )
            
            # Detect trends using the consolidated trend analyzer
            trends = trend_analyzer.detect_entity_trends(
                entities=entities,
                articles=articles,
                entity_types=entity_types,
                min_significance=min_significance,
                min_mentions=min_mentions,
                max_trends=max_trends
            )
            
            # Save analysis results if needed
            # self._save_trend_analysis(session, trends)
            
            return trends

    def _save_analysis_result(
        self, 
        session: Session, 
        article_id: int, 
        analysis_type: str, 
        results: Dict[str, Any]
    ) -> AnalysisResult:
        """Save an analysis result to the database.

        Args:
            session: Database session
            article_id: ID of the article
            analysis_type: Type of analysis
            results: Analysis results

        Returns:
            Saved AnalysisResult object
        """
        # Check if an analysis result already exists
        existing = self.analysis_result_crud.get_by_article_and_type(
            session, 
            article_id=article_id, 
            analysis_type=analysis_type
        )
        
        if existing:
            # Update existing result
            for key, value in results.items():
                existing.results[key] = value
            session.add(existing)
            session.commit()
            session.refresh(existing)
            return existing
        else:
            # Create new result
            new_result = AnalysisResult(
                article_id=article_id,
                analysis_type=analysis_type,
                results=results
            )
            session.add(new_result)
            session.commit()
            session.refresh(new_result)
            return new_result

    def get_analysis_result(
        self, 
        article_id: int, 
        analysis_type: str
    ) -> Optional[Dict[str, Any]]:
        """Get an analysis result from the database.

        Args:
            article_id: ID of the article
            analysis_type: Type of analysis

        Returns:
            Analysis results if found, None otherwise
        """
        with self.session_factory() as session:
            result = self.analysis_result_crud.get_by_article_and_type(
                session, 
                article_id=article_id, 
                analysis_type=analysis_type
            )
            
            if result:
                return result.results
            return None

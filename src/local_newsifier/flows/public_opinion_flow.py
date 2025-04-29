"""
Flow for analyzing public opinion and sentiment in news articles.

This module provides functionality for orchestrating sentiment analysis, including:

1. Analyzing sentiment in article content
2. Tracking sentiment changes over time for specific topics
3. Detecting significant shifts in public sentiment
4. Generating visualizations and reports of sentiment analysis
5. Correlating sentiment across different topics and entities

The PublicOpinionFlow handles database session management, tool initialization,
and report generation in various formats (text, markdown, HTML).
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any, Tuple, Union

from sqlmodel import Session

from local_newsifier.flows.flow_base import FlowBase
from local_newsifier.di.descriptors import Dependency
from local_newsifier.database.engine import SessionManager

# Global logger
logger = logging.getLogger(__name__)


class PublicOpinionFlow(FlowBase):
    """Flow for analyzing public opinion and sentiment in news articles.
    
    This implementation uses the simplified DI pattern with descriptors
    for cleaner dependency declaration and resolution.
    """
    
    # Define dependencies using descriptors - these will be lazy-loaded when needed
    sentiment_analyzer = Dependency()
    sentiment_tracker = Dependency()
    opinion_visualizer = Dependency()
    entity_service = Dependency()
    article_service = Dependency()
    file_writer = Dependency()
    session_factory = Dependency(fallback=SessionManager)
    
    def __init__(
        self,
        container=None,
        session: Optional[Session] = None,
        **explicit_deps
    ):
        """Initialize the public opinion flow.
        
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
        assert self.sentiment_analyzer is not None, "SentimentAnalyzer is required"
        assert self.sentiment_tracker is not None, "SentimentTracker is required"
        # Other dependencies will be loaded when needed
    
    def analyze_entity_sentiment(
        self,
        entity_id: int,
        days: int = 30,
        include_related: bool = True,
        output_format: Optional[str] = None,
        output_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """Analyze sentiment for a specific entity.
        
        Args:
            entity_id: ID of the entity to analyze
            days: Number of days to include in analysis
            include_related: Whether to include sentiment for related entities
            output_format: Optional format for output report
            output_path: Optional path for output report
            
        Returns:
            Dictionary with sentiment analysis results
        """
        with self.session_factory() as session:
            # Get entity
            entity = self.entity_service.get_canonical_entity(session, entity_id)
            
            if not entity:
                raise ValueError(f"Entity with ID {entity_id} not found")
            
            # Calculate date range
            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(days=days)
            
            # Analyze sentiment for entity
            sentiment_data = self.sentiment_tracker.analyze_entity_sentiment(
                session,
                entity_id=entity_id,
                start_date=start_date,
                end_date=end_date
            )
            
            # Include related entities if requested
            related_sentiment = {}
            if include_related:
                # Get related entities
                related_entities = self.entity_service.get_related_entities(
                    session,
                    entity_id=entity_id,
                    limit=5
                )
                
                # Analyze sentiment for each related entity
                for related in related_entities:
                    try:
                        related_sentiment[related.name] = self.sentiment_tracker.analyze_entity_sentiment(
                            session,
                            entity_id=related.id,
                            start_date=start_date,
                            end_date=end_date
                        )
                    except Exception as e:
                        logger.error(f"Error analyzing sentiment for related entity {related.name}: {str(e)}")
            
            # Generate visualization if requested
            visualization_path = None
            if output_format and self.opinion_visualizer:
                try:
                    visualization_path = self.opinion_visualizer.visualize_entity_sentiment(
                        entity_name=entity.name,
                        sentiment_data=sentiment_data,
                        related_sentiment=related_sentiment,
                        format=output_format,
                        output_path=output_path
                    )
                except Exception as e:
                    logger.error(f"Error generating visualization: {str(e)}")
            
            # Return results
            return {
                "entity_id": entity_id,
                "entity_name": entity.name,
                "sentiment_data": sentiment_data,
                "related_sentiment": related_sentiment,
                "visualization_path": visualization_path
            }
    
    def analyze_topic_sentiment(
        self,
        topic: str,
        days: int = 30,
        related_topics: Optional[List[str]] = None,
        output_format: Optional[str] = None,
        output_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """Analyze sentiment for a specific topic.
        
        Args:
            topic: Topic to analyze
            days: Number of days to include in analysis
            related_topics: Optional list of related topics to include
            output_format: Optional format for output report
            output_path: Optional path for output report
            
        Returns:
            Dictionary with sentiment analysis results
        """
        with self.session_factory() as session:
            # Calculate date range
            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(days=days)
            
            # Analyze sentiment for topic
            sentiment_data = self.sentiment_tracker.analyze_topic_sentiment(
                session,
                topic=topic,
                start_date=start_date,
                end_date=end_date
            )
            
            # Include related topics if requested
            related_sentiment = {}
            if related_topics:
                for related in related_topics:
                    try:
                        related_sentiment[related] = self.sentiment_tracker.analyze_topic_sentiment(
                            session,
                            topic=related,
                            start_date=start_date,
                            end_date=end_date
                        )
                    except Exception as e:
                        logger.error(f"Error analyzing sentiment for related topic {related}: {str(e)}")
            
            # Generate visualization if requested
            visualization_path = None
            if output_format and self.opinion_visualizer:
                try:
                    visualization_path = self.opinion_visualizer.visualize_topic_sentiment(
                        topic=topic,
                        sentiment_data=sentiment_data,
                        related_sentiment=related_sentiment,
                        format=output_format,
                        output_path=output_path
                    )
                except Exception as e:
                    logger.error(f"Error generating visualization: {str(e)}")
            
            # Return results
            return {
                "topic": topic,
                "sentiment_data": sentiment_data,
                "related_sentiment": related_sentiment,
                "visualization_path": visualization_path
            }
    
    def detect_sentiment_shifts(
        self,
        days: int = 30,
        threshold: float = 0.3,
        min_articles: int = 5,
        output_format: Optional[str] = None,
        output_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """Detect significant shifts in sentiment for entities and topics.
        
        Args:
            days: Number of days to include in analysis
            threshold: Minimum sentiment shift to consider significant
            min_articles: Minimum number of articles for entity/topic to be included
            output_format: Optional format for output report
            output_path: Optional path for output report
            
        Returns:
            Dictionary with detected sentiment shifts
        """
        with self.session_factory() as session:
            # Calculate date range
            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(days=days)
            
            # Detect entity sentiment shifts
            entity_shifts = self.sentiment_tracker.detect_entity_sentiment_shifts(
                session,
                start_date=start_date,
                end_date=end_date,
                threshold=threshold,
                min_articles=min_articles
            )
            
            # Detect topic sentiment shifts
            topic_shifts = self.sentiment_tracker.detect_topic_sentiment_shifts(
                session,
                start_date=start_date,
                end_date=end_date,
                threshold=threshold,
                min_articles=min_articles
            )
            
            # Generate visualization if requested
            visualization_path = None
            if output_format and self.opinion_visualizer:
                try:
                    visualization_path = self.opinion_visualizer.visualize_sentiment_shifts(
                        entity_shifts=entity_shifts,
                        topic_shifts=topic_shifts,
                        format=output_format,
                        output_path=output_path
                    )
                except Exception as e:
                    logger.error(f"Error generating visualization: {str(e)}")
            
            # Return results
            return {
                "entity_shifts": entity_shifts,
                "topic_shifts": topic_shifts,
                "visualization_path": visualization_path
            }
    
    def generate_sentiment_report(
        self,
        period: Union[str, int] = "day",
        output_format: str = "html",
        output_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate a comprehensive sentiment analysis report.
        
        Args:
            period: Time period for report (day, week, month, or number of days)
            output_format: Format for output report (text, markdown, html)
            output_path: Optional path for output report
            
        Returns:
            Dictionary with report information
        """
        # Convert period to days
        days = 1
        if isinstance(period, str):
            if period.lower() == "day":
                days = 1
            elif period.lower() == "week":
                days = 7
            elif period.lower() == "month":
                days = 30
            else:
                try:
                    days = int(period)
                except ValueError:
                    raise ValueError(f"Invalid period: {period}")
        else:
            days = period
        
        # Calculate date range
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)
        
        # Generate report
        with self.session_factory() as session:
            # Get top entities
            top_entities = self.entity_service.get_trending_entities(
                session,
                start_date=start_date,
                end_date=end_date,
                limit=10
            )
            
            # Analyze sentiment for each entity
            entity_sentiment = {}
            for entity in top_entities:
                try:
                    entity_sentiment[entity.name] = self.sentiment_tracker.analyze_entity_sentiment(
                        session,
                        entity_id=entity.id,
                        start_date=start_date,
                        end_date=end_date
                    )
                except Exception as e:
                    logger.error(f"Error analyzing sentiment for entity {entity.name}: {str(e)}")
            
            # Get top topics
            top_topics = self.article_service.get_trending_topics(
                session,
                start_date=start_date,
                end_date=end_date,
                limit=10
            )
            
            # Analyze sentiment for each topic
            topic_sentiment = {}
            for topic in top_topics:
                try:
                    topic_sentiment[topic] = self.sentiment_tracker.analyze_topic_sentiment(
                        session,
                        topic=topic,
                        start_date=start_date,
                        end_date=end_date
                    )
                except Exception as e:
                    logger.error(f"Error analyzing sentiment for topic {topic}: {str(e)}")
            
            # Detect sentiment shifts
            sentiment_shifts = self.detect_sentiment_shifts(
                days=days,
                threshold=0.2,
                min_articles=3
            )
            
            # Generate visualization
            report_path = None
            if self.opinion_visualizer:
                try:
                    report_path = self.opinion_visualizer.generate_sentiment_report(
                        period_days=days,
                        entity_sentiment=entity_sentiment,
                        topic_sentiment=topic_sentiment,
                        sentiment_shifts=sentiment_shifts,
                        format=output_format,
                        output_path=output_path
                    )
                except Exception as e:
                    logger.error(f"Error generating report: {str(e)}")
            
            # Return results
            return {
                "period": period,
                "start_date": start_date,
                "end_date": end_date,
                "entity_sentiment": entity_sentiment,
                "topic_sentiment": topic_sentiment,
                "sentiment_shifts": sentiment_shifts,
                "report_path": report_path
            }

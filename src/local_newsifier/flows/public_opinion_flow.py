"""
Flow for analyzing public opinion and sentiment in news articles.

This module provides a crew.ai Flow for orchestrating sentiment analysis, including:

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
from typing import Dict, List, Optional, Any, Tuple

from crewai import Flow

from ..config.database import get_database_settings
from ..database.manager import DatabaseManager
from ..models.database import init_db, get_session
from ..models.sentiment import SentimentVisualizationData
from ..tools.sentiment_analyzer import SentimentAnalysisTool
from ..tools.sentiment_tracker import SentimentTracker
from ..tools.opinion_visualizer import OpinionVisualizerTool

logger = logging.getLogger(__name__)


class PublicOpinionFlow(Flow):
    """Flow for analyzing public opinion and sentiment in news articles."""

    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        """
        Initialize the public opinion analysis flow.
        
        Args:
            db_manager: Optional database manager to use
        """
        super().__init__()
        
        # Set up database connection if not provided
        if db_manager is None:
            db_settings = get_database_settings()
            engine = init_db(str(db_settings.DATABASE_URL))  # Convert PostgresDsn to string
            session_factory = get_session(engine)
            session = session_factory()
            self.db_manager = DatabaseManager(session)
            self._owns_session = True
        else:
            self.db_manager = db_manager
            self._owns_session = False
            
        # Initialize tools
        self.sentiment_analyzer = SentimentAnalysisTool()
        self.sentiment_tracker = SentimentTracker(self.db_manager)
        self.opinion_visualizer = OpinionVisualizerTool(self.db_manager)
        
    def __del__(self):
        """Clean up resources when the flow is deleted."""
        if hasattr(self, '_owns_session') and self._owns_session:
            if hasattr(self, 'db_manager') and self.db_manager is not None:
                self.db_manager.session.close()
    
    def analyze_articles(self, article_ids: Optional[List[int]] = None) -> Dict[int, Dict]:
        """
        Analyze sentiment for specific articles or all unanalyzed articles.
        
        Args:
            article_ids: Optional list of article IDs to analyze
            
        Returns:
            Dictionary mapping article IDs to sentiment results
        """
        # If no article IDs provided, get all articles that need sentiment analysis
        if not article_ids:
            articles = self.db_manager.get_articles_by_status("analyzed")
            article_ids = [article.id for article in articles]
        
        # Analyze each article
        results = {}
        for article_id in article_ids:
            try:
                sentiment_results = self.sentiment_analyzer.analyze_article(
                    self.db_manager, article_id
                )
                results[article_id] = sentiment_results
                
                # Update article status to indicate sentiment analysis is complete
                self.db_manager.update_article_status(article_id, "sentiment_analyzed")
                
            except Exception as e:
                logger.error(f"Error analyzing article {article_id}: {str(e)}")
                results[article_id] = {"error": str(e)}
        
        return results
    
    def analyze_topic_sentiment(
        self, 
        topics: List[str],
        days_back: int = 30, 
        interval: str = "day"
    ) -> Dict[str, Dict]:
        """
        Analyze sentiment trends for specific topics.
        
        Args:
            topics: List of topics to analyze
            days_back: Number of days to look back
            interval: Time interval for grouping ('day', 'week', 'month')
            
        Returns:
            Dictionary containing topic sentiment analysis results
        """
        # Calculate date range
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days_back)
        
        logger.info(f"Analyzing sentiment for topics {topics} from {start_date} to {end_date}")
        
        # Get sentiment data by topic and period
        sentiment_by_period = self.sentiment_tracker.get_sentiment_by_period(
            start_date=start_date,
            end_date=end_date,
            time_interval=interval,
            topics=topics
        )
        
        # Detect sentiment shifts
        shifts = self.sentiment_tracker.detect_sentiment_shifts(
            topics=topics,
            start_date=start_date,
            end_date=end_date,
            time_interval=interval
        )
        
        # Prepare results
        results = {
            "date_range": {
                "start": start_date,
                "end": end_date,
                "days": days_back
            },
            "interval": interval,
            "topics": topics,
            "sentiment_by_period": sentiment_by_period,
            "sentiment_shifts": shifts
        }
        
        return results
    
    def analyze_entity_sentiment(
        self, 
        entity_names: List[str],
        days_back: int = 30, 
        interval: str = "day"
    ) -> Dict[str, Dict]:
        """
        Analyze sentiment trends for specific entities.
        
        Args:
            entity_names: List of entity names to analyze
            days_back: Number of days to look back
            interval: Time interval for grouping ('day', 'week', 'month')
            
        Returns:
            Dictionary containing entity sentiment analysis results
        """
        # Calculate date range
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days_back)
        
        logger.info(f"Analyzing sentiment for entities {entity_names} from {start_date} to {end_date}")
        
        # Get sentiment data by entity and period
        entity_sentiments = {}
        for entity_name in entity_names:
            entity_sentiment = self.sentiment_tracker.get_entity_sentiment_trends(
                entity_name=entity_name,
                start_date=start_date,
                end_date=end_date,
                time_interval=interval
            )
            entity_sentiments[entity_name] = entity_sentiment
        
        # Prepare results
        results = {
            "date_range": {
                "start": start_date,
                "end": end_date,
                "days": days_back
            },
            "interval": interval,
            "entities": entity_names,
            "entity_sentiments": entity_sentiments
        }
        
        return results
    
    def detect_opinion_shifts(
        self,
        topics: List[str],
        days_back: int = 30,
        interval: str = "day",
        shift_threshold: float = 0.3
    ) -> Dict[str, List]:
        """
        Detect significant shifts in public opinion.
        
        Args:
            topics: List of topics to analyze
            days_back: Number of days to look back
            interval: Time interval for grouping ('day', 'week', 'month')
            shift_threshold: Threshold for significant shifts
            
        Returns:
            Dictionary of detected opinion shifts by topic
        """
        # Calculate date range
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days_back)
        
        logger.info(f"Detecting opinion shifts for topics {topics} from {start_date} to {end_date}")
        
        # Detect shifts
        shifts = self.sentiment_tracker.detect_sentiment_shifts(
            topics=topics,
            start_date=start_date,
            end_date=end_date,
            time_interval=interval,
            shift_threshold=shift_threshold
        )
        
        # Group shifts by topic
        shifts_by_topic = {}
        for topic in topics:
            topic_shifts = [s for s in shifts if s["topic"] == topic]
            shifts_by_topic[topic] = topic_shifts
        
        return shifts_by_topic
    
    def correlate_topics(
        self,
        topic_pairs: List[Tuple[str, str]],
        days_back: int = 30,
        interval: str = "day"
    ) -> List[Dict]:
        """
        Analyze correlation between sentiment of topic pairs.
        
        Args:
            topic_pairs: List of topic name pairs to correlate
            days_back: Number of days to look back
            interval: Time interval for grouping ('day', 'week', 'month')
            
        Returns:
            List of topic correlation results
        """
        # Calculate date range
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days_back)
        
        logger.info(f"Analyzing topic correlations from {start_date} to {end_date}")
        
        # Calculate correlations
        correlations = []
        for topic1, topic2 in topic_pairs:
            correlation = self.sentiment_tracker.calculate_topic_correlation(
                topic1=topic1,
                topic2=topic2,
                start_date=start_date,
                end_date=end_date,
                time_interval=interval
            )
            correlations.append(correlation)
        
        return correlations
    
    def generate_topic_report(
        self, 
        topic: str,
        days_back: int = 30,
        interval: str = "day",
        format_type: str = "markdown"
    ) -> str:
        """
        Generate a report for a specific topic's sentiment analysis.
        
        Args:
            topic: Topic to analyze
            days_back: Number of days to look back
            interval: Time interval for grouping ('day', 'week', 'month')
            format_type: Report format type ('text', 'markdown', 'html')
            
        Returns:
            Formatted report string
        """
        # Calculate date range
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days_back)
        
        logger.info(f"Generating {format_type} report for topic {topic} from {start_date} to {end_date}")
        
        # Prepare visualization data
        try:
            viz_data = self.opinion_visualizer.prepare_timeline_data(
                topic=topic,
                start_date=start_date,
                end_date=end_date,
                interval=interval
            )
            
            # Generate report based on format
            if format_type == "markdown":
                return self.opinion_visualizer.generate_markdown_report(
                    viz_data, report_type="timeline"
                )
            elif format_type == "html":
                return self.opinion_visualizer.generate_html_report(
                    viz_data, report_type="timeline"
                )
            else:  # Default to text
                return self.opinion_visualizer.generate_text_report(
                    viz_data, report_type="timeline"
                )
                
        except Exception as e:
            logger.error(f"Error generating report: {str(e)}")
            return f"Error generating report: {str(e)}"
    
    def generate_comparison_report(
        self, 
        topics: List[str],
        days_back: int = 30,
        interval: str = "day",
        format_type: str = "markdown"
    ) -> str:
        """
        Generate a comparison report for multiple topics.
        
        Args:
            topics: List of topics to compare
            days_back: Number of days to look back
            interval: Time interval for grouping ('day', 'week', 'month')
            format_type: Report format type ('text', 'markdown', 'html')
            
        Returns:
            Formatted comparison report string
        """
        # Calculate date range
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days_back)
        
        logger.info(f"Generating {format_type} comparison report for topics {topics}")
        
        # Prepare visualization data for all topics
        try:
            comparison_data = {}
            for topic in topics:
                try:
                    topic_data = self.opinion_visualizer.prepare_timeline_data(
                        topic=topic,
                        start_date=start_date,
                        end_date=end_date,
                        interval=interval
                    )
                    comparison_data[topic] = topic_data
                except Exception as topic_error:
                    logger.warning(f"Error preparing data for topic {topic}: {str(topic_error)}")
            
            # Generate report based on format
            if format_type == "markdown":
                return self.opinion_visualizer.generate_markdown_report(
                    comparison_data, report_type="comparison"
                )
            elif format_type == "html":
                return self.opinion_visualizer.generate_html_report(
                    comparison_data, report_type="comparison"
                )
            else:  # Default to text
                return self.opinion_visualizer.generate_text_report(
                    comparison_data, report_type="comparison"
                )
                
        except Exception as e:
            logger.error(f"Error generating comparison report: {str(e)}")
            return f"Error generating comparison report: {str(e)}"
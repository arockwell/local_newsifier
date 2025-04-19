"""Tool for detecting trends in news articles."""

from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Set, Tuple

from sqlmodel import Session, select
from local_newsifier.models.database.article import Article 
from local_newsifier.models.database.entity import Entity
from local_newsifier.models.trend import TrendAnalysis, TrendEntity, TrendEvidenceItem, TrendStatus, TrendType
from local_newsifier.tools.historical_aggregator import HistoricalDataAggregator
from local_newsifier.tools.topic_analyzer import TopicFrequencyAnalyzer
from local_newsifier.database.engine import with_session


class TrendDetector:
    """Tool for detecting trends in news article data."""

    def __init__(
        self, 
        topic_analyzer: Optional[TopicFrequencyAnalyzer] = None,
        data_aggregator: Optional[HistoricalDataAggregator] = None,
    ):
        """
        Initialize the trend detector.

        Args:
            topic_analyzer: Optional TopicFrequencyAnalyzer instance.
                           If not provided, a new one will be created.
            data_aggregator: Optional HistoricalDataAggregator instance.
                            If not provided, a new one will be created.
        """
        self.data_aggregator = data_aggregator or HistoricalDataAggregator()
        self.topic_analyzer = topic_analyzer or TopicFrequencyAnalyzer(self.data_aggregator)
        
    @with_session
    def _get_articles_for_entity(
        self, 
        entity_text: str, 
        entity_type: str, 
        start_date: datetime, 
        end_date: datetime,
        *,
        session: Optional[Session] = None
    ) -> List[Article]:
        """
        Get articles that mention a specific entity.

        Args:
            entity_text: Text of the entity
            entity_type: Type of the entity
            start_date: Start date for search
            end_date: End date for search
            session: Optional SQLAlchemy session

        Returns:
            List of articles mentioning the entity
        """
        # Get articles in time range
        articles = self.data_aggregator.get_articles_in_timeframe(
            start_date, end_date, session=session
        )
        article_ids = [article.id for article in articles]
        
        if not article_ids:
            return []
            
        # Create article lookup
        article_lookup = {article.id: article for article in articles}
        
        # Get entities matching our criteria using SQLModel
        matched_articles = []
        statement = select(Entity).where(
            Entity.article_id.in_(article_ids),
            Entity.entity_type == entity_type,
            Entity.text == entity_text
        )
        results = session.execute(statement)
        entities = results.all()
        
        # Get unique articles
        for entity in entities:
            article = article_lookup.get(entity.article_id)
            if article and article not in matched_articles:
                matched_articles.append(article)
        
        return matched_articles

    def _create_trend_from_topic(
        self,
        topic: str,
        entity_type: str,
        significance_data: Dict,
        pattern_data: Optional[Dict] = None,
        related_topics: Optional[List[Dict]] = None,
    ) -> TrendAnalysis:
        """
        Create a trend analysis object from topic data.

        Args:
            topic: Topic text
            entity_type: Entity type
            significance_data: Data about statistical significance
            pattern_data: Optional pattern analysis data
            related_topics: Optional list of related topics

        Returns:
            TrendAnalysis object
        """
        # Determine trend type based on data
        trend_type = TrendType.FREQUENCY_SPIKE
        if significance_data.get("is_new", False):
            trend_type = TrendType.NOVEL_ENTITY
        elif pattern_data and pattern_data.get("is_rising", False):
            trend_type = TrendType.EMERGING_TOPIC
        elif pattern_data and pattern_data.get("is_consistent", False):
            trend_type = TrendType.SUSTAINED_COVERAGE
        
        # Calculate confidence score
        z_score = significance_data.get("z_score", 0)
        confidence_score = min(0.99, max(0.6, min(z_score / 3.0, 1.0)))
        
        # Create basic trend
        trend = TrendAnalysis(
            trend_type=trend_type,
            name=f"{topic} ({entity_type})",
            description=self._generate_trend_description(
                topic, entity_type, trend_type, significance_data
            ),
            status=TrendStatus.CONFIRMED if confidence_score > 0.8 else TrendStatus.POTENTIAL,
            confidence_score=confidence_score,
            start_date=datetime.now(timezone.utc) - significance_data.get("lookback_days", 7),
            statistical_significance=z_score,
            tags=[entity_type.lower(), trend_type.lower().replace("_", "-")],
        )
        
        # Add main entity
        trend.add_entity(
            TrendEntity(
                text=topic,
                entity_type=entity_type,
                frequency=significance_data.get("current_frequency", 1),
                relevance_score=1.0,
            )
        )
        
        # Add related entities if available
        if related_topics:
            for related in related_topics[:5]:  # Add top 5 related topics
                trend.add_entity(
                    TrendEntity(
                        text=related["topic"],
                        entity_type=related["entity_type"],
                        frequency=related.get("co_occurrence_count", 1),
                        relevance_score=related.get("co_occurrence_rate", 0.5),
                    )
                )
        
        return trend

    def _generate_trend_description(
        self, topic: str, entity_type: str, trend_type: TrendType, data: Dict
    ) -> str:
        """
        Generate a human-readable description of the trend.

        Args:
            topic: Topic text
            entity_type: Entity type
            trend_type: Type of trend
            data: Trend data dictionary

        Returns:
            Description string
        """
        if trend_type == TrendType.NOVEL_ENTITY:
            return f"New {entity_type.lower()} '{topic}' appearing in local news coverage"
            
        if trend_type == TrendType.FREQUENCY_SPIKE:
            change_percent = data.get("change_percent", 0)
            return f"Significant increase ({change_percent:.1f}%) in mentions of {entity_type.lower()} '{topic}'"
            
        if trend_type == TrendType.EMERGING_TOPIC:
            return f"Steadily increasing coverage of {entity_type.lower()} '{topic}' in local news"
            
        if trend_type == TrendType.SUSTAINED_COVERAGE:
            return f"Consistent ongoing coverage of {entity_type.lower()} '{topic}' in local news"
            
        return f"Unusual pattern in mentions of {entity_type.lower()} '{topic}' in local news"

    def _add_evidence_to_trend(
        self, trend: TrendAnalysis, articles: List[Article]
    ) -> TrendAnalysis:
        """
        Add evidence from articles to a trend.

        Args:
            trend: TrendAnalysis object to update
            articles: List of articles providing evidence

        Returns:
            Updated trend
        """
        # Sort articles by publication date, newest first
        sorted_articles = sorted(
            articles, key=lambda a: a.published_at or datetime.now(), reverse=True
        )
        
        # Create a new trend object to avoid appending to existing evidence
        # This ensures we only ever have at most 10 evidence items
        result = TrendAnalysis(
            trend_id=trend.trend_id,
            trend_type=trend.trend_type,
            name=trend.name,
            description=trend.description,
            status=trend.status,
            confidence_score=trend.confidence_score,
            start_date=trend.start_date,
            end_date=trend.end_date,
            statistical_significance=trend.statistical_significance,
            tags=trend.tags.copy() if trend.tags else [],
        )
        
        # Copy existing entities
        for entity in trend.entities:
            result.add_entity(entity)
            
        # Add evidence from each article (limit to 10)
        for article in sorted_articles[:10]:
            if not article.published_at:
                continue
                
            result.add_evidence(
                TrendEvidenceItem(
                    article_id=article.id,
                    article_url=article.url,
                    article_title=article.title,
                    published_at=article.published_at,
                    evidence_text=article.title or "Article mentions this entity",
                    relevance_score=1.0,
                )
            )
            
        return result

    @with_session
    def detect_entity_trends(
        self,
        entity_types: List[str] = None,
        min_significance: float = 1.5,
        min_mentions: int = 2,
        max_trends: int = 20,
        *,
        session: Optional[Session] = None
    ) -> List[TrendAnalysis]:
        """
        Detect trends based on entity frequency analysis.

        Args:
            entity_types: List of entity types to analyze
            min_significance: Minimum significance score for trends
            min_mentions: Minimum number of mentions required
            max_trends: Maximum number of trends to return
            session: Optional SQLAlchemy session

        Returns:
            List of detected trends
        """
        if not entity_types:
            entity_types = ["PERSON", "ORG", "GPE"]
            
        # Get significant frequency changes
        significant_changes = self.topic_analyzer.identify_significant_changes(
            entity_types=entity_types,
            time_frame="WEEK",
            significance_threshold=min_significance,
            min_mentions=min_mentions,
            session=session
        )
        
        # Get current frequency data for pattern analysis
        current_frequencies, _ = self.data_aggregator.get_baseline_frequencies(
            entity_types, "WEEK", current_period=1, session=session
        )
        
        # Analyze patterns in the frequencies
        patterns = self.topic_analyzer.analyze_frequency_patterns(current_frequencies)
        
        # Create trend objects for significant changes
        trends = []
        for key, data in significant_changes.items():
            topic, entity_type = key.split(":")
            
            # Find patterns for this topic
            pattern_data = patterns.get(key)
            
            # Find related topics
            related_topics = self.topic_analyzer.find_related_topics(
                topic, entity_type, current_frequencies
            )
            
            # Create the trend object
            trend = self._create_trend_from_topic(
                topic, entity_type, data, pattern_data, related_topics
            )
            
            # Get articles as evidence
            start_date, end_date = self.data_aggregator.calculate_date_range("WEEK", 2)
            articles = self._get_articles_for_entity(
                topic, entity_type, start_date, end_date, session=session
            )
            
            # Add evidence to trend
            if articles:
                trend = self._add_evidence_to_trend(trend, articles)
                trends.append(trend)
        
        # Sort by confidence and limit
        trends.sort(key=lambda t: t.confidence_score, reverse=True)
        return trends[:max_trends]

    def detect_anomalous_patterns(self) -> List[TrendAnalysis]:
        """
        Detect anomalous patterns that don't fit standard trend categories.

        Returns:
            List of anomalous pattern trends
        """
        # This is a placeholder for more sophisticated anomaly detection
        # that would require more complex statistical analysis
        return []
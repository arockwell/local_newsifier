"""Consolidated trend analysis tool for news articles."""

import logging
import math
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from typing import Annotated, Any, Dict, List, Optional, Set, Tuple, Union

import numpy as np
import spacy
from fastapi import Depends
from fastapi_injectable import injectable
from sqlmodel import Session, select

from local_newsifier.models.article import Article
from local_newsifier.models.entity import Entity
from local_newsifier.models.trend import (TimeFrame, TopicFrequency, TrendAnalysis, TrendEntity,
                                          TrendEvidenceItem, TrendStatus, TrendType)

logger = logging.getLogger(__name__)


@injectable(use_cache=False)
class TrendAnalyzer:
    """Consolidated tool for analyzing trends in news articles.

    This tool combines functionality from:
    - HeadlineTrendAnalyzer
    - TrendDetector
    - TopicFrequencyAnalyzer
    - HistoricalDataAggregator

    It provides a unified interface for trend analysis operations.
    """

    def __init__(
        self,
        session: Optional[Session] = None,
        nlp_model: Optional[Any] = None,
        model_name: str = "en_core_web_lg"
    ):
        """Initialize the trend analyzer.

        Args:
            session: Optional SQLAlchemy session for database access
            nlp_model: Pre-loaded spaCy NLP model (injected)
            model_name: Name of the spaCy model to use as fallback
        """
        self.session = session
        self._cache: Dict[str, Any] = {}
        self.nlp = nlp_model

        # Fallback to loading model if not injected (for backward compatibility)
        if self.nlp is None:
            try:
                self.nlp = spacy.load(model_name)
                logger.info(f"Loaded spaCy model '{model_name}'")
            except OSError:
                logger.warning(f"spaCy model '{model_name}' not found. Some NLP features will be disabled.")
                self.nlp = None

    def extract_keywords(self, headlines: List[str], top_n: int = 50) -> List[Tuple[str, int]]:
        """Extract significant keywords from a collection of headlines.
        
        Args:
            headlines: List of headlines to analyze
            top_n: Number of top keywords to return
            
        Returns:
            List of (keyword, count) tuples sorted by frequency
        """
        if not headlines:
            return []
            
        if not self.nlp:
            # Fallback simple keyword extraction if NLP is unavailable
            words = []
            for headline in headlines:
                words.extend(headline.split())
            
            # Filter common words and count
            stopwords = {"the", "a", "an", "and", "in", "on", "at", "to", "for", "of", "with", "by"}
            filtered_words = [w.lower() for w in words if w.lower() not in stopwords and len(w) > 2]
            return Counter(filtered_words).most_common(top_n)
        
        # NLP-based keyword extraction
        combined_text = " ".join(headlines)
        doc = self.nlp(combined_text)
        
        # Extract significant noun phrases and named entities
        keywords = []
        for chunk in doc.noun_chunks:
            if not any(token.is_stop for token in chunk):
                keywords.append(chunk.text.lower())
                
        for ent in doc.ents:
            if ent.label_ in ["PERSON", "ORG", "GPE", "EVENT"]:
                keywords.append(ent.text.lower())
                
        # Count frequencies and return top N
        return Counter(keywords).most_common(top_n)

    def detect_keyword_trends(self, trend_data: Dict[str, List[Tuple[str, int]]]) -> List[Dict[str, Any]]:
        """Detect trending terms by analyzing frequency changes over time.
        
        Args:
            trend_data: Dictionary mapping time periods to keyword frequency lists
            
        Returns:
            List of trending terms with growth metrics
        """
        if not trend_data or len(trend_data) < 2:
            return []
            
        # Convert to sorted time periods
        periods = sorted(trend_data.keys())
        
        # Track term frequencies across periods
        term_frequencies = defaultdict(lambda: {period: 0 for period in periods})
        for period in periods:
            for term, count in trend_data[period]:
                term_frequencies[term][period] = count
        
        # Calculate growth for each term
        term_growth = []
        for term, period_counts in term_frequencies.items():
            if sum(period_counts.values()) < 3:  # Filter noise
                continue
                
            # Calculate growth rate
            first_period = periods[0]
            last_period = periods[-1]
            
            # Check if term appeared in both first and last period
            if period_counts[first_period] > 0 and period_counts[last_period] > 0:
                growth_rate = (period_counts[last_period] - period_counts[first_period]) / max(1, period_counts[first_period])
                
                # Only consider significant growth
                if growth_rate > 0.5 or period_counts[last_period] >= 3:
                    term_growth.append({
                        "term": term,
                        "growth_rate": growth_rate,
                        "first_count": period_counts[first_period],
                        "last_count": period_counts[last_period],
                        "total_mentions": sum(period_counts.values())
                    })
        
        # Sort by growth rate descending
        return sorted(term_growth, key=lambda x: (x["growth_rate"], x["total_mentions"]), reverse=True)

    @staticmethod
    def get_interval_key(date: datetime, interval: str) -> str:
        """Convert date to appropriate interval key (day, week, month).
        
        Args:
            date: Date to convert
            interval: Time interval type
            
        Returns:
            String key representing the time interval
        """
        if not date:
            date = datetime.now()
            
        if interval == "day":
            return date.strftime("%Y-%m-%d")
        elif interval == "week":
            return f"{date.year}-W{date.isocalendar()[1]}"
        elif interval == "month":
            return date.strftime("%Y-%m")
        return date.strftime("%Y")

    def calculate_date_range(self, time_frame: TimeFrame, periods: int = 1) -> Tuple[datetime, datetime]:
        """Calculate start and end dates based on time frame.

        Args:
            time_frame: The time frame unit (DAY, WEEK, MONTH, etc.)
            periods: Number of periods to look back

        Returns:
            Tuple of (start_date, end_date)
        """
        end_date = datetime.now(timezone.utc)

        if time_frame == TimeFrame.DAY:
            start_date = end_date - timedelta(days=periods)
        elif time_frame == TimeFrame.WEEK:
            start_date = end_date - timedelta(weeks=periods)
        elif time_frame == TimeFrame.MONTH:
            # Approximate a month as 30 days
            start_date = end_date - timedelta(days=30 * periods)
        elif time_frame == TimeFrame.QUARTER:
            # Approximate a quarter as 90 days
            start_date = end_date - timedelta(days=90 * periods)
        elif time_frame == TimeFrame.YEAR:
            # Approximate a year as 365 days
            start_date = end_date - timedelta(days=365 * periods)
        else:
            raise ValueError(f"Unsupported time frame: {time_frame}")

        return start_date, end_date

    def calculate_statistical_significance(
        self,
        current_mentions: int,
        baseline_mentions: int,
        threshold: float = 1.5,
    ) -> Tuple[float, bool]:
        """Calculate the statistical significance of frequency changes.

        Args:
            current_mentions: Current period mention count
            baseline_mentions: Baseline period mention count
            threshold: Z-score threshold for significance

        Returns:
            Tuple of (z_score, is_significant)
        """
        # If no baseline, treat as significant new topic
        if baseline_mentions == 0:
            # New topics get a default z-score of 2.0 if they have enough mentions
            return 2.0, current_mentions >= 2

        # Calculate growth rate
        growth_rate = current_mentions / baseline_mentions

        # Simple statistical test
        if current_mentions >= 3 and growth_rate >= 1.5:
            z_score = 2.0
        elif current_mentions >= 2 and growth_rate >= 2.0:
            z_score = 1.8
        else:
            # Not significant
            z_score = 0.0

        return z_score, z_score >= threshold

    def analyze_frequency_patterns(
        self,
        entity_frequencies: Dict[str, int],
        min_data_points: int = 3,
    ) -> Dict[str, Dict]:
        """Analyze patterns in topic frequencies over time.

        Args:
            entity_frequencies: Dictionary of entity frequencies
            min_data_points: Minimum data points required for pattern analysis

        Returns:
            Dictionary of patterns detected for each entity
        """
        if len(entity_frequencies) < min_data_points:
            return {}

        # Simple analysis for now - can be expanded in the future
        mean = np.mean(list(entity_frequencies.values()))
        std = np.std(list(entity_frequencies.values()))
        coefficient_of_variation = std / max(1, mean)

        pattern_info = {
            "mean": mean,
            "std": std,
            "coefficient_of_variation": coefficient_of_variation,
            "is_spiky": coefficient_of_variation > 1.0,
            "is_consistent": coefficient_of_variation < 0.5,
        }

        return pattern_info

    def find_related_entities(
        self, 
        target_entity: Entity, 
        all_entities: List[Entity],
        threshold: float = 0.3
    ) -> List[Dict]:
        """Find entities that frequently appear with the target entity.

        Args:
            target_entity: The main entity
            all_entities: List of all entities to check
            threshold: Minimum co-occurrence threshold

        Returns:
            List of related entities with correlation scores
        """
        if not all_entities or not target_entity:
            return []

        # Group entities by article
        articles_with_target = set()
        entities_by_article = defaultdict(list)
        
        for entity in all_entities:
            if entity.article_id:
                entities_by_article[entity.article_id].append(entity)
                if entity.id == target_entity.id or (entity.text == target_entity.text and entity.entity_type == target_entity.entity_type):
                    articles_with_target.add(entity.article_id)
        
        if not articles_with_target:
            return []
            
        # Find co-occurring entities
        co_occurrence_counts = Counter()
        for article_id in articles_with_target:
            for entity in entities_by_article[article_id]:
                if entity.id != target_entity.id and (entity.text != target_entity.text or entity.entity_type != target_entity.entity_type):
                    key = f"{entity.text}|{entity.entity_type}"
                    co_occurrence_counts[key] += 1
        
        # Calculate co-occurrence rate
        related = []
        for key, count in co_occurrence_counts.most_common(10):
            text, entity_type = key.split("|")
            co_occurrence_rate = count / len(articles_with_target)
            
            if co_occurrence_rate >= threshold:
                related.append({
                    "text": text,
                    "entity_type": entity_type,
                    "co_occurrence_rate": co_occurrence_rate,
                    "co_occurrence_count": count,
                })
        
        return related

    def detect_entity_trends(
        self,
        entities: List[Entity],
        articles: List[Article],
        entity_types: List[str],
        min_significance: float = 1.5,
        min_mentions: int = 2,
        max_trends: int = 20
    ) -> List[TrendAnalysis]:
        """Detect trends based on entity frequency analysis.

        Args:
            entities: List of entities to analyze
            articles: List of articles containing the entities
            entity_types: List of entity types to consider
            min_significance: Minimum significance score for trends
            min_mentions: Minimum number of mentions required
            max_trends: Maximum number of trends to return

        Returns:
            List of detected trends
        """
        if not entities or not articles:
            return []
            
        # Group entities by type and text
        entity_counts = Counter()
        entity_objects = defaultdict(list)
        
        for entity in entities:
            if entity.entity_type in entity_types:
                key = f"{entity.text}|{entity.entity_type}"
                entity_counts[key] += 1
                entity_objects[key].append(entity)
        
        # Build article lookup
        article_lookup = {article.id: article for article in articles}
        
        # Find significant entities
        significant_entities = []
        for key, count in entity_counts.items():
            if count < min_mentions:
                continue
                
            text, entity_type = key.split("|")
            
            # Simple significance test for now
            # In a real implementation, we would compare against historical data
            z_score, is_significant = self.calculate_statistical_significance(
                count, count // 2, min_significance
            )
            
            if is_significant:
                entity_data = {
                    "text": text,
                    "entity_type": entity_type,
                    "mention_count": count,
                    "significance": z_score,
                    "entities": entity_objects[key]
                }
                significant_entities.append(entity_data)
        
        # Create trend objects
        trends = []
        for data in significant_entities:
            # Determine trend type
            if data["mention_count"] <= 3:
                trend_type = TrendType.NOVEL_ENTITY
            elif data["significance"] > 2.0:
                trend_type = TrendType.FREQUENCY_SPIKE
            else:
                trend_type = TrendType.EMERGING_TOPIC
            
            # Calculate confidence score based on significance
            confidence_score = min(0.99, max(0.6, min(data["significance"] / 3.0, 1.0)))
            
            # Create trend
            trend = TrendAnalysis(
                trend_type=trend_type,
                name=f"{data['text']} ({data['entity_type']})",
                description=self._generate_trend_description(
                    data["text"], data["entity_type"], trend_type, data
                ),
                status=TrendStatus.CONFIRMED if confidence_score > 0.8 else TrendStatus.POTENTIAL,
                confidence_score=confidence_score,
                start_date=datetime.now(timezone.utc) - timedelta(days=7),
                statistical_significance=data["significance"],
                tags=[data["entity_type"].lower(), trend_type.name.lower().replace("_", "-")],
            )
            
            # Add main entity
            trend.add_entity(
                TrendEntity(
                    text=data["text"],
                    entity_type=data["entity_type"],
                    frequency=data["mention_count"],
                    relevance_score=1.0,
                )
            )
            
            # Find related entities
            if len(data["entities"]) > 0:
                related_entities = self.find_related_entities(
                    data["entities"][0], entities
                )
                
                # Add related entities to trend
                for related in related_entities[:5]:
                    trend.add_entity(
                        TrendEntity(
                            text=related["text"],
                            entity_type=related["entity_type"],
                            frequency=related["co_occurrence_count"],
                            relevance_score=related["co_occurrence_rate"],
                        )
                    )
            
            # Add evidence from articles
            entity_article_ids = {entity.article_id for entity in data["entities"] if entity.article_id}
            for article_id in entity_article_ids:
                article = article_lookup.get(article_id)
                if article and article.published_at:
                    trend.add_evidence(
                        TrendEvidenceItem(
                            article_id=article.id,
                            article_url=article.url,
                            article_title=article.title,
                            published_at=article.published_at,
                            evidence_text=article.title or f"Article mentions {data['text']}",
                            relevance_score=1.0,
                        )
                    )
            
            trends.append(trend)
        
        # Sort by confidence and limit
        trends.sort(key=lambda t: t.confidence_score, reverse=True)
        return trends[:max_trends]

    def _generate_trend_description(
        self, topic: str, entity_type: str, trend_type: TrendType, data: Dict
    ) -> str:
        """Generate a human-readable description of the trend.

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
            return f"Significant increase in mentions of {entity_type.lower()} '{topic}'"
            
        if trend_type == TrendType.EMERGING_TOPIC:
            return f"Steadily increasing coverage of {entity_type.lower()} '{topic}' in local news"
            
        if trend_type == TrendType.SUSTAINED_COVERAGE:
            return f"Consistent ongoing coverage of {entity_type.lower()} '{topic}' in local news"
            
        return f"Unusual pattern in mentions of {entity_type.lower()} '{topic}' in local news"

    def clear_cache(self) -> None:
        """Clear the internal cache to free memory."""
        self._cache.clear()

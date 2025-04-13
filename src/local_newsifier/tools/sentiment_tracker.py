"""Tool for tracking sentiment trends over time across articles."""

import logging
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Tuple, Optional, Any

from ..database.manager import DatabaseManager
from ..models.sentiment import OpinionTrendCreate, SentimentShiftCreate
from ..models.database import ArticleDB, AnalysisResultDB

logger = logging.getLogger(__name__)


class SentimentTracker:
    """Tool for tracking and analyzing sentiment trends over time."""

    def __init__(self, db_manager: DatabaseManager):
        """
        Initialize the sentiment tracker.

        Args:
            db_manager: Database manager instance
        """
        self.db_manager = db_manager

    def get_sentiment_by_period(
        self,
        start_date: datetime,
        end_date: datetime,
        time_interval: str = "day",
        topics: Optional[List[str]] = None
    ) -> Dict[str, Dict]:
        """
        Get sentiment data grouped by time periods.

        Args:
            start_date: Start date for analysis
            end_date: End date for analysis
            time_interval: Time interval for grouping ('day', 'week', 'month')
            topics: Optional list of topics to filter by

        Returns:
            Dictionary mapping periods to sentiment data
        """
        # Get all articles in date range
        articles = self._get_articles_in_range(start_date, end_date)
        
        # Group by period
        period_groups = self._group_articles_by_period(articles, time_interval)
        
        # Compute sentiment for each period and topic
        results = {}
        
        for period, period_articles in period_groups.items():
            period_results = {}
            
            # Get sentiment analyses for these articles
            article_ids = [article.id for article in period_articles]
            sentiment_data = self._get_sentiment_data_for_articles(article_ids)
            
            # Calculate overall sentiment for period
            if sentiment_data:
                overall_sentiment = {
                    "avg_sentiment": sum(data["document_sentiment"] for data in sentiment_data) / len(sentiment_data),
                    "article_count": len(sentiment_data),
                    "sentiment_distribution": self._calculate_sentiment_distribution(sentiment_data)
                }
                period_results["overall"] = overall_sentiment
            
            # Calculate topic-specific sentiment if topics provided
            if topics:
                for topic in topics:
                    topic_sentiment = self._calculate_topic_sentiment(sentiment_data, topic)
                    if topic_sentiment:
                        period_results[topic] = topic_sentiment
            
            results[period] = period_results
            
        return results
    
    def get_entity_sentiment_trends(
        self,
        entity_name: str,
        start_date: datetime,
        end_date: datetime,
        time_interval: str = "day"
    ) -> Dict[str, Dict]:
        """
        Get sentiment trends for a specific entity over time.

        Args:
            entity_name: Name of the entity to analyze
            start_date: Start date for analysis
            end_date: End date for analysis
            time_interval: Time interval for grouping ('day', 'week', 'month')

        Returns:
            Dictionary mapping periods to entity sentiment data
        """
        # Get all articles in date range
        articles = self._get_articles_in_range(start_date, end_date)
        
        # Group by period
        period_groups = self._group_articles_by_period(articles, time_interval)
        
        # Compute entity sentiment for each period
        results = {}
        
        for period, period_articles in period_groups.items():
            # Get sentiment analyses for these articles
            article_ids = [article.id for article in period_articles]
            sentiment_data = self._get_sentiment_data_for_articles(article_ids)
            
            # Extract entity sentiment
            entity_sentiment = self._calculate_entity_sentiment(sentiment_data, entity_name)
            
            if entity_sentiment:
                results[period] = entity_sentiment
            
        return results
    
    def detect_sentiment_shifts(
        self,
        topics: List[str],
        start_date: datetime,
        end_date: datetime,
        time_interval: str = "day",
        shift_threshold: float = 0.3
    ) -> List[Dict]:
        """
        Detect significant shifts in sentiment.

        Args:
            topics: List of topics to analyze
            start_date: Start date for analysis
            end_date: End date for analysis
            time_interval: Time interval for grouping ('day', 'week', 'month')
            shift_threshold: Threshold for considering a shift significant

        Returns:
            List of detected sentiment shifts
        """
        # Get sentiment by period for all specified topics
        sentiment_by_period = self.get_sentiment_by_period(
            start_date, end_date, time_interval, topics
        )
        
        # Detect shifts for each topic
        shifts = []
        
        for topic in topics:
            topic_shifts = self._detect_topic_shifts(
                topic, sentiment_by_period, shift_threshold
            )
            shifts.extend(topic_shifts)
        
        return shifts
    
    def calculate_topic_correlation(
        self,
        topic1: str,
        topic2: str,
        start_date: datetime,
        end_date: datetime,
        time_interval: str = "day"
    ) -> Dict:
        """
        Calculate correlation between sentiment trends of two topics.

        Args:
            topic1: First topic
            topic2: Second topic
            start_date: Start date for analysis
            end_date: End date for analysis
            time_interval: Time interval for grouping ('day', 'week', 'month')

        Returns:
            Dictionary with correlation statistics
        """
        # Get sentiment by period for both topics
        sentiment_by_period = self.get_sentiment_by_period(
            start_date, end_date, time_interval, [topic1, topic2]
        )
        
        # Extract sentiment values for each topic
        topic1_values = []
        topic2_values = []
        periods = []
        
        for period, data in sorted(sentiment_by_period.items()):
            if topic1 in data and topic2 in data:
                topic1_values.append(data[topic1]["avg_sentiment"])
                topic2_values.append(data[topic2]["avg_sentiment"])
                periods.append(period)
        
        # Calculate correlation if we have enough data points
        if len(topic1_values) >= 3:
            correlation = self._calculate_correlation(topic1_values, topic2_values)
        else:
            correlation = 0.0
        
        return {
            "topic1": topic1,
            "topic2": topic2,
            "correlation": correlation,
            "period_count": len(periods),
            "periods": periods
        }
    
    def _calculate_correlation(self, values1: List[float], values2: List[float]) -> float:
        """Calculate Pearson correlation coefficient between two lists of values."""
        if len(values1) != len(values2) or len(values1) < 2:
            return 0.0
            
        n = len(values1)
        
        # Calculate means
        mean1 = sum(values1) / n
        mean2 = sum(values2) / n
        
        # Calculate variances and covariance
        var1 = sum((x - mean1) ** 2 for x in values1) / n
        var2 = sum((x - mean2) ** 2 for x in values2) / n
        cov = sum((values1[i] - mean1) * (values2[i] - mean2) for i in range(n)) / n
        
        # Calculate correlation
        if var1 > 0 and var2 > 0:
            correlation = cov / (var1 ** 0.5 * var2 ** 0.5)
        else:
            correlation = 0.0
            
        return correlation
    
    def _get_articles_in_range(self, start_date: datetime, end_date: datetime) -> List:
        """Get all articles published within the date range."""
        # This is a simplified implementation - in a real system you would filter
        # in the database query to avoid loading all articles
        articles = []
        session = self.db_manager.session
        
        query = (
            session.query(ArticleDB)
            .filter(
                ArticleDB.published_at >= start_date,
                ArticleDB.published_at <= end_date,
                ArticleDB.status.in_(["analyzed", "entity_tracked"])
            )
            .order_by(ArticleDB.published_at)
        )
        
        articles = query.all()
        return articles
    
    def _group_articles_by_period(
        self, articles: List, time_interval: str
    ) -> Dict[str, List]:
        """Group articles by time period."""
        period_groups = defaultdict(list)
        
        for article in articles:
            published_at = article.published_at
            if not published_at:
                continue
                
            period_key = self._get_period_key(published_at, time_interval)
            period_groups[period_key].append(article)
            
        return period_groups
    
    def _get_period_key(self, date: datetime, time_interval: str) -> str:
        """Get key for a time period."""
        if time_interval == "day":
            return date.strftime("%Y-%m-%d")
        elif time_interval == "week":
            return f"{date.year}-W{date.isocalendar()[1]}"
        elif time_interval == "month":
            return date.strftime("%Y-%m")
        elif time_interval == "year":
            return date.strftime("%Y")
        else:
            return date.strftime("%Y-%m-%d")  # Default to day
    
    def _get_sentiment_data_for_articles(self, article_ids: List[int]) -> List[Dict]:
        """Get sentiment analysis results for articles."""
        session = self.db_manager.session
        
        # Get analysis results for articles
        results = (
            session.query(AnalysisResultDB)
            .filter(
                AnalysisResultDB.article_id.in_(article_ids),
                AnalysisResultDB.analysis_type == "sentiment"
            )
            .all()
        )
        
        # Convert to list of dictionaries
        sentiment_data = []
        for result in results:
            data = {
                "article_id": result.article_id,
                "document_sentiment": result.results.get("document_sentiment", 0.0),
                "document_magnitude": result.results.get("document_magnitude", 0.0),
                "topic_sentiments": result.results.get("topic_sentiments", {}),
                "entity_sentiments": result.results.get("entity_sentiments", {})
            }
            sentiment_data.append(data)
            
        return sentiment_data
    
    def _calculate_sentiment_distribution(self, sentiment_data: List[Dict]) -> Dict[str, int]:
        """Calculate distribution of sentiment across articles."""
        distribution = {
            "positive": 0,
            "neutral": 0,
            "negative": 0
        }
        
        for data in sentiment_data:
            sentiment = data["document_sentiment"]
            if sentiment > 0.1:
                distribution["positive"] += 1
            elif sentiment < -0.1:
                distribution["negative"] += 1
            else:
                distribution["neutral"] += 1
                
        return distribution
    
    def _calculate_topic_sentiment(
        self, sentiment_data: List[Dict], topic: str
    ) -> Dict:
        """Calculate sentiment for a specific topic."""
        topic_lower = topic.lower()
        relevant_data = []
        
        for data in sentiment_data:
            # Check if this topic appears in the topic sentiments
            topic_sentiments = data.get("topic_sentiments", {})
            
            # Look for exact match or substring match
            matched_topics = [
                t for t in topic_sentiments.keys() 
                if topic_lower == t.lower() or topic_lower in t.lower()
            ]
            
            if matched_topics:
                # Average sentiment for all matched topics
                topic_sentiment = sum(topic_sentiments[t] for t in matched_topics) / len(matched_topics)
                
                relevant_data.append({
                    "article_id": data.get("article_id"),
                    "sentiment": topic_sentiment
                })
        
        if not relevant_data:
            return {}
            
        # Calculate average sentiment
        total_sentiment = sum(d["sentiment"] for d in relevant_data)
        avg_sentiment = total_sentiment / len(relevant_data)
        
        # Calculate sentiment distribution
        sentiment_distribution = {
            "positive": 0,
            "neutral": 0,
            "negative": 0
        }
        
        for data in relevant_data:
            sentiment = data["sentiment"]
            if sentiment > 0.1:
                sentiment_distribution["positive"] += 1
            elif sentiment < -0.1:
                sentiment_distribution["negative"] += 1
            else:
                sentiment_distribution["neutral"] += 1
        
        return {
            "avg_sentiment": avg_sentiment,
            "article_count": len(relevant_data),
            "sentiment_distribution": sentiment_distribution,
            "article_ids": [d["article_id"] for d in relevant_data]
        }
    
    def _calculate_entity_sentiment(
        self, sentiment_data: List[Dict], entity_name: str
    ) -> Dict:
        """Calculate sentiment for a specific entity."""
        entity_lower = entity_name.lower()
        relevant_data = []
        
        for data in sentiment_data:
            # Check if this entity appears in the entity sentiments
            entity_sentiments = data.get("entity_sentiments", {})
            
            # Look for exact match or substring match
            matched_entities = [
                e for e in entity_sentiments.keys() 
                if entity_lower == e.lower() or entity_lower in e.lower()
            ]
            
            if matched_entities:
                # Average sentiment for all matched entities
                entity_sentiment = sum(entity_sentiments[e] for e in matched_entities) / len(matched_entities)
                
                relevant_data.append({
                    "article_id": data.get("article_id"),
                    "sentiment": entity_sentiment
                })
        
        if not relevant_data:
            return {}
            
        # Calculate average sentiment
        total_sentiment = sum(d["sentiment"] for d in relevant_data)
        avg_sentiment = total_sentiment / len(relevant_data)
        
        return {
            "avg_sentiment": avg_sentiment,
            "article_count": len(relevant_data),
            "article_ids": [d["article_id"] for d in relevant_data]
        }
    
    def _detect_topic_shifts(
        self, topic: str, sentiment_by_period: Dict, threshold: float
    ) -> List[Dict]:
        """Detect significant sentiment shifts for a topic."""
        shifts = []
        periods = sorted(sentiment_by_period.keys())
        
        if len(periods) < 2:
            return shifts
            
        # Collect sentiment data for this topic across periods
        topic_data = []
        
        for period in periods:
            period_data = sentiment_by_period[period]
            if topic in period_data and period_data[topic].get("article_count", 0) > 0:
                topic_data.append({
                    "period": period,
                    "sentiment": period_data[topic]["avg_sentiment"],
                    "article_count": period_data[topic]["article_count"],
                    "article_ids": period_data[topic].get("article_ids", [])
                })
        
        # Need at least two periods with data
        if len(topic_data) < 2:
            return shifts
            
        # Look for shifts between consecutive periods
        for i in range(len(topic_data) - 1):
            start_data = topic_data[i]
            end_data = topic_data[i + 1]
            
            start_sentiment = start_data["sentiment"]
            end_sentiment = end_data["sentiment"]
            
            # Calculate absolute and relative shifts
            shift_magnitude = end_sentiment - start_sentiment
            
            # Avoid division by zero
            if abs(start_sentiment) > 0.001:
                shift_percentage = shift_magnitude / abs(start_sentiment)
            else:
                shift_percentage = 0.0 if abs(shift_magnitude) < 0.001 else float('inf')
            
            # Check if shift exceeds threshold
            if abs(shift_magnitude) >= threshold:
                shifts.append({
                    "topic": topic,
                    "start_period": start_data["period"],
                    "end_period": end_data["period"],
                    "start_sentiment": start_sentiment,
                    "end_sentiment": end_sentiment,
                    "shift_magnitude": shift_magnitude,
                    "shift_percentage": shift_percentage,
                    "supporting_article_ids": start_data["article_ids"] + end_data["article_ids"]
                })
        
        return shifts
    
    def update_opinion_trends(
        self,
        start_date: datetime,
        end_date: datetime,
        topics: List[str],
        time_interval: str = "day",
    ) -> List[Dict]:
        """
        Update opinion trends in the database.

        Args:
            start_date: Start date for analysis
            end_date: End date for analysis
            topics: List of topics to track
            time_interval: Time interval for grouping

        Returns:
            List of created or updated trends
        """
        # Get sentiment data by period
        sentiment_by_period = self.get_sentiment_by_period(
            start_date, end_date, time_interval, topics
        )
        
        # Create or update trend records
        created_trends = []
        
        for period, period_data in sentiment_by_period.items():
            for topic in topics:
                if topic in period_data and period_data[topic].get("article_count", 0) > 0:
                    topic_data = period_data[topic]
                    
                    # Create trend record
                    trend_data = OpinionTrendCreate(
                        topic=topic,
                        period=period,
                        period_type=time_interval,
                        avg_sentiment=topic_data["avg_sentiment"],
                        sentiment_count=topic_data["article_count"],
                        sentiment_distribution=topic_data.get("sentiment_distribution"),
                        sources={}  # Would need to fetch sources in a real implementation
                    )
                    
                    # Store in database
                    # This is a stub - would need actual DB integration
                    created_trends.append(trend_data.model_dump())
        
        return created_trends
    
    def track_sentiment_shifts(
        self,
        start_date: datetime,
        end_date: datetime,
        topics: List[str],
        time_interval: str = "day",
        shift_threshold: float = 0.3
    ) -> List[Dict]:
        """
        Track sentiment shifts in the database.

        Args:
            start_date: Start date for analysis
            end_date: End date for analysis
            topics: List of topics to track
            time_interval: Time interval for grouping
            shift_threshold: Threshold for significant shifts

        Returns:
            List of detected shifts
        """
        # Detect shifts
        shifts = self.detect_sentiment_shifts(
            topics, start_date, end_date, time_interval, shift_threshold
        )
        
        # Create shift records
        created_shifts = []
        
        for shift in shifts:
            # Create shift record
            shift_data = SentimentShiftCreate(
                topic=shift["topic"],
                start_period=shift["start_period"],
                end_period=shift["end_period"],
                period_type=time_interval,
                start_sentiment=shift["start_sentiment"],
                end_sentiment=shift["end_sentiment"],
                shift_magnitude=shift["shift_magnitude"],
                shift_percentage=shift["shift_percentage"],
                supporting_article_ids=shift["supporting_article_ids"]
            )
            
            # Store in database
            # This is a stub - would need actual DB integration
            created_shifts.append(shift_data.model_dump())
        
        return created_shifts
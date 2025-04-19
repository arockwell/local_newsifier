"""Refactored flow for sentiment analysis of news articles."""

from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any

from crewai import Flow

from local_newsifier.core.factory import ToolFactory, ServiceFactory
from local_newsifier.database.session_manager import get_session_manager
from local_newsifier.crud.article import article as article_crud
from local_newsifier.crud.analysis_result import analysis_result as analysis_result_crud
from local_newsifier.models.database.article import Article
from local_newsifier.models.database.analysis_result import AnalysisResult
from local_newsifier.models.state import AnalysisStatus, NewsAnalysisState


class SentimentAnalysisFlow(Flow):
    """Flow for sentiment analysis of news articles."""

    def __init__(self, session_manager=None, sentiment_analyzer=None):
        """Initialize the sentiment analysis flow with dependencies.
        
        Args:
            session_manager: Session manager for database access (optional)
            sentiment_analyzer: SentimentAnalyzer instance (optional)
        """
        super().__init__()
        self.session_manager = session_manager or get_session_manager()
        self.sentiment_analyzer = sentiment_analyzer or ToolFactory.create_sentiment_analyzer(
            session_manager=self.session_manager
        )

    def analyze_new_articles(self) -> List[Dict]:
        """Analyze all new articles for sentiment.

        Returns:
            List of processed articles with sentiment results
        """
        with self.session_manager.session() as session:
            # Get articles that haven't been processed for sentiment yet
            articles = article_crud.get_by_status(session, status="scraped")

            results = []
            for article in articles:
                # Analyze article sentiment
                result = self.analyze_article(article.id)

                # Update article status to indicate sentiment analysis is complete
                article_crud.update_status(session, article_id=article.id, status="analyzed")

                # Add to results
                results.append(
                    {
                        "article_id": article.id,
                        "title": article.title,
                        "url": article.url,
                        "sentiment": result
                    }
                )

            return results

    def analyze_article(self, article_id: int) -> Dict[str, Any]:
        """Analyze sentiment for a single article.

        Args:
            article_id: ID of the article to analyze

        Returns:
            Sentiment analysis results
        """
        # Use the sentiment analyzer to process the article
        sentiment_results = self.sentiment_analyzer.analyze_article(article_id)
        
        # Store results in database
        self.sentiment_analyzer.analyze_article_sentiment(article_id)
        
        return sentiment_results

    def get_sentiment_trends(self, days: int = 30) -> Dict[str, Any]:
        """Generate sentiment trends over time.

        Args:
            days: Number of days to include in the trends

        Returns:
            Sentiment trend data
        """
        # Calculate date range
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)

        # Get sentiment trends using the service
        trend_data = self.sentiment_analyzer.sentiment_service.get_sentiment_trends(
            start_date=start_date,
            end_date=end_date
        )

        # Add date range information
        trend_data["date_range"] = {
            "start": start_date,
            "end": end_date,
            "days": days
        }

        return trend_data

    def get_entity_sentiment_dashboard(self, entity_name: str, days: int = 30) -> Dict[str, Any]:
        """Generate sentiment dashboard for a specific entity.

        Args:
            entity_name: Name of the entity to analyze
            days: Number of days to include in the dashboard

        Returns:
            Entity sentiment dashboard data
        """
        # Calculate date range
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)

        with self.session_manager.session() as session:
            # Get sentiment analysis results with this entity
            sentiment_data = analysis_result_crud.get_by_date_range(
                session,
                analysis_type="sentiment",
                start_date=start_date,
                end_date=end_date
            )

            # Filter and process entity sentiment
            entity_sentiments = []
            for result in sentiment_data:
                # Skip if no entity sentiments
                if not result.results or "entity_sentiments" not in result.results:
                    continue

                # Get sentiment for this entity if it exists
                entity_sentiment = result.results["entity_sentiments"].get(entity_name)
                if entity_sentiment is not None:
                    # Get article for context
                    article = article_crud.get(session, id=result.article_id)
                    if article:
                        entity_sentiments.append({
                            "date": article.published_at or result.created_at,
                            "sentiment_score": entity_sentiment,
                            "article_id": article.id,
                            "article_title": article.title,
                            "article_url": article.url
                        })

            # Sort by date
            entity_sentiments.sort(key=lambda x: x["date"], reverse=True)

            # Calculate summary statistics
            avg_sentiment = sum(item["sentiment_score"] for item in entity_sentiments) / len(entity_sentiments) if entity_sentiments else 0
            positive_count = sum(1 for item in entity_sentiments if item["sentiment_score"] > 0)
            negative_count = sum(1 for item in entity_sentiments if item["sentiment_score"] < 0)
            neutral_count = sum(1 for item in entity_sentiments if item["sentiment_score"] == 0)

            return {
                "entity_name": entity_name,
                "date_range": {"start": start_date, "end": end_date, "days": days},
                "mention_count": len(entity_sentiments),
                "average_sentiment": avg_sentiment,
                "sentiment_breakdown": {
                    "positive": positive_count,
                    "negative": negative_count,
                    "neutral": neutral_count
                },
                "recent_mentions": entity_sentiments[:10]  # Include only top 10 most recent
            }

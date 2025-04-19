"""Service for sentiment analysis business logic."""

from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

from sqlmodel import Session

from local_newsifier.database.session_manager import get_session_manager
from local_newsifier.crud.article import article as article_crud
from local_newsifier.crud.analysis_result import analysis_result as analysis_result_crud
from local_newsifier.models.database.analysis_result import AnalysisResult
from local_newsifier.models.sentiment import SentimentAnalysis
from local_newsifier.models.state import AnalysisStatus, NewsAnalysisState


class SentimentService:
    """Service for sentiment analysis business logic."""

    def __init__(self, session_manager=None):
        """Initialize the sentiment service with dependencies.

        Args:
            session_manager: Session manager for database access (optional)
        """
        self.session_manager = session_manager or get_session_manager()

    def store_sentiment_analysis(
        self, 
        article_id: int, 
        sentiment_results: Dict[str, Any]
    ) -> AnalysisResult:
        """Store sentiment analysis results for an article.

        Args:
            article_id: ID of the article
            sentiment_results: Sentiment analysis results

        Returns:
            Created analysis result
        """
        with self.session_manager.session() as session:
            # Verify article exists
            article = article_crud.get(session, id=article_id)
            if not article:
                raise ValueError(f"Article with ID {article_id} not found")
                
            # Create analysis result
            analysis_result = AnalysisResult(
                article_id=article_id,
                analysis_type="sentiment",
                results=sentiment_results
            )
            
            return analysis_result_crud.create(session, obj_in=analysis_result)

    def get_article_sentiment(self, article_id: int) -> Optional[Dict[str, Any]]:
        """Get sentiment analysis for a specific article.

        Args:
            article_id: ID of the article

        Returns:
            Sentiment analysis results if available, None otherwise
        """
        with self.session_manager.session() as session:
            # Get latest sentiment analysis result
            analysis_result = analysis_result_crud.get_latest_by_type(
                session, article_id=article_id, analysis_type="sentiment"
            )
            
            if not analysis_result:
                return None
                
            return analysis_result.results

    def get_sentiment_trends(
        self, 
        start_date: datetime, 
        end_date: datetime
    ) -> Dict[str, Any]:
        """Get sentiment trends across articles over time.

        Args:
            start_date: Start date for trends
            end_date: End date for trends

        Returns:
            Sentiment trend data
        """
        with self.session_manager.session() as session:
            # Get sentiment analysis results for articles in date range
            sentiment_data = analysis_result_crud.get_by_date_range(
                session, 
                analysis_type="sentiment",
                start_date=start_date,
                end_date=end_date
            )
            
            # Process results into trend data
            trend_data = self._process_sentiment_trends(sentiment_data)
            
            return trend_data

    def _process_sentiment_trends(
        self, 
        sentiment_data: List[AnalysisResult]
    ) -> Dict[str, Any]:
        """Process sentiment analysis results into trend data.

        Args:
            sentiment_data: List of sentiment analysis results

        Returns:
            Processed trend data
        """
        # Initialize trend data
        trend_data = {
            "daily_averages": {},
            "entity_sentiment": {},
            "topic_sentiment": {}
        }
        
        # Process each sentiment analysis result
        for result in sentiment_data:
            # Skip if missing required data
            if not result.results or not result.created_at:
                continue
                
            # Get date key
            date_key = result.created_at.strftime("%Y-%m-%d")
            
            # Process document sentiment
            document_sentiment = result.results.get("document_sentiment")
            if document_sentiment is not None:
                # Add to daily averages
                if date_key in trend_data["daily_averages"]:
                    # Update average
                    current = trend_data["daily_averages"][date_key]["average"]
                    count = trend_data["daily_averages"][date_key]["count"]
                    new_average = (current * count + document_sentiment) / (count + 1)
                    trend_data["daily_averages"][date_key]["average"] = new_average
                    trend_data["daily_averages"][date_key]["count"] += 1
                else:
                    # Initialize for this date
                    trend_data["daily_averages"][date_key] = {
                        "average": document_sentiment,
                        "count": 1
                    }
            
            # Process entity sentiments
            entity_sentiments = result.results.get("entity_sentiments", {})
            for entity, sentiment in entity_sentiments.items():
                if entity not in trend_data["entity_sentiment"]:
                    trend_data["entity_sentiment"][entity] = []
                    
                trend_data["entity_sentiment"][entity].append({
                    "date": date_key,
                    "sentiment": sentiment,
                    "article_id": result.article_id
                })
            
            # Process topic sentiments
            topic_sentiments = result.results.get("topic_sentiments", {})
            for topic, sentiment in topic_sentiments.items():
                if topic not in trend_data["topic_sentiment"]:
                    trend_data["topic_sentiment"][topic] = []
                    
                trend_data["topic_sentiment"][topic].append({
                    "date": date_key,
                    "sentiment": sentiment,
                    "article_id": result.article_id
                })
        
        return trend_data

    def analyze_article_with_state(self, state: NewsAnalysisState, sentiment_data: Dict[str, Any]) -> NewsAnalysisState:
        """Update NewsAnalysisState with sentiment analysis results.

        Args:
            state: Current analysis state
            sentiment_data: Sentiment analysis results

        Returns:
            Updated analysis state
        """
        # Initialize sentiment results if not present
        if not state.analysis_results:
            state.analysis_results = {}
        if "sentiment" not in state.analysis_results:
            state.analysis_results["sentiment"] = {}
            
        # Update state with sentiment data
        state.analysis_results["sentiment"].update(sentiment_data)
        
        # Update state metadata
        state.analyzed_at = datetime.now(timezone.utc)
        state.status = AnalysisStatus.ANALYSIS_SUCCEEDED
        state.add_log("Successfully completed sentiment analysis")
        
        return state

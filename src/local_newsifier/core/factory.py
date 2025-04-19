"""Factories for creating application components."""

from local_newsifier.database.session_manager import get_session_manager
from local_newsifier.services.entity_service import EntityService
from local_newsifier.services.sentiment_service import SentimentService
from local_newsifier.tools.sentiment_analyzer_v2 import SentimentAnalyzer


class ToolFactory:
    """Factory for creating tool instances with their dependencies."""
        
    @staticmethod
    def create_sentiment_analyzer(
        session_manager=None,
        sentiment_service=None,
        model_name="en_core_web_sm"
    ):
        """Create a SentimentAnalyzer instance with dependencies.
        
        Args:
            session_manager: Session manager (optional)
            sentiment_service: Sentiment service (optional)
            model_name: Name of the spaCy model
            
        Returns:
            Configured SentimentAnalyzer instance
        """
        # Use provided dependencies or create defaults
        session_mgr = session_manager or get_session_manager()
        sentiment_svc = sentiment_service or ServiceFactory.create_sentiment_service(
            session_manager=session_mgr
        )
        
        return SentimentAnalyzer(
            sentiment_service=sentiment_svc,
            session_manager=session_mgr,
            model_name=model_name
        )


class ServiceFactory:
    """Factory for creating service instances."""

    @staticmethod
    def create_entity_service(session_manager=None, model_name="en_core_web_lg"):
        """Create an EntityService instance.

        Args:
            session_manager: Session manager (optional)
            model_name: Name of the spaCy model (optional)

        Returns:
            Configured EntityService instance
        """
        return EntityService(
            session_manager=session_manager or get_session_manager(),
            model_name=model_name
        )
        
    @staticmethod
    def create_sentiment_service(session_manager=None):
        """Create a SentimentService instance.
        
        Args:
            session_manager: Session manager (optional)
            
        Returns:
            Configured SentimentService instance
        """
        return SentimentService(session_manager=session_manager or get_session_manager())

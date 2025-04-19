"""Unit tests for the SentimentService."""

import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from local_newsifier.database.session_manager import SessionManager
from local_newsifier.services.sentiment_service import SentimentService
from local_newsifier.models.state import NewsAnalysisState, AnalysisStatus


class TestSentimentService:
    """Test cases for the SentimentService."""
    
    def test_init(self):
        """Test SentimentService initialization."""
        # Test with a provided session manager
        session_manager = SessionManager()
        service = SentimentService(session_manager=session_manager)
        assert service.session_manager == session_manager
        
        # Test with default session manager
        with patch('local_newsifier.services.sentiment_service.get_session_manager') as mock_get_sm:
            mock_session_manager = MagicMock()
            mock_get_sm.return_value = mock_session_manager
            service = SentimentService()
            assert service.session_manager == mock_session_manager
    
    def test_store_sentiment_analysis(self):
        """Test storing sentiment analysis results."""
        # Arrange
        mock_session = MagicMock()
        mock_session_manager = MagicMock()
        mock_session_manager.session.return_value.__enter__.return_value = mock_session
        
        # Mock article_crud
        mock_article_crud = MagicMock()
        mock_article = MagicMock()
        mock_article_crud.get.return_value = mock_article
        
        # Mock analysis_result_crud
        mock_analysis_result_crud = MagicMock()
        mock_analysis_result = MagicMock()
        mock_analysis_result_crud.create.return_value = mock_analysis_result
        
        # Act
        with patch('local_newsifier.services.sentiment_service.article_crud', mock_article_crud):
            with patch('local_newsifier.services.sentiment_service.analysis_result_crud', 
                      mock_analysis_result_crud):
                service = SentimentService(session_manager=mock_session_manager)
                result = service.store_sentiment_analysis(
                    article_id=1,
                    sentiment_results={"document_sentiment": 0.5}
                )
        
        # Assert
        mock_article_crud.get.assert_called_once_with(mock_session, id=1)
        mock_analysis_result_crud.create.assert_called_once()
        assert result == mock_analysis_result
    
    def test_get_article_sentiment(self):
        """Test getting sentiment for an article."""
        # Arrange
        mock_session = MagicMock()
        mock_session_manager = MagicMock()
        mock_session_manager.session.return_value.__enter__.return_value = mock_session
        
        mock_analysis_result_crud = MagicMock()
        mock_analysis_result = MagicMock()
        mock_analysis_result.results = {"document_sentiment": 0.5}
        mock_analysis_result_crud.get_latest_by_type.return_value = mock_analysis_result
        
        # Act
        with patch('local_newsifier.services.sentiment_service.analysis_result_crud', 
                  mock_analysis_result_crud):
            service = SentimentService(session_manager=mock_session_manager)
            result = service.get_article_sentiment(article_id=1)
        
        # Assert
        mock_analysis_result_crud.get_latest_by_type.assert_called_once_with(
            mock_session, article_id=1, analysis_type="sentiment"
        )
        assert result == {"document_sentiment": 0.5}
    
    def test_get_article_sentiment_none(self):
        """Test getting sentiment when none exists."""
        # Arrange
        mock_session = MagicMock()
        mock_session_manager = MagicMock()
        mock_session_manager.session.return_value.__enter__.return_value = mock_session
        
        mock_analysis_result_crud = MagicMock()
        mock_analysis_result_crud.get_latest_by_type.return_value = None
        
        # Act
        with patch('local_newsifier.services.sentiment_service.analysis_result_crud', 
                  mock_analysis_result_crud):
            service = SentimentService(session_manager=mock_session_manager)
            result = service.get_article_sentiment(article_id=1)
        
        # Assert
        assert result is None
    
    def test_get_sentiment_trends(self):
        """Test getting sentiment trends."""
        # Arrange
        mock_session = MagicMock()
        mock_session_manager = MagicMock()
        mock_session_manager.session.return_value.__enter__.return_value = mock_session
        
        mock_analysis_result_crud = MagicMock()
        mock_results = [
            MagicMock(
                article_id=1, 
                created_at=datetime(2025, 4, 15, tzinfo=timezone.utc),
                results={"document_sentiment": 0.5}
            ),
            MagicMock(
                article_id=2, 
                created_at=datetime(2025, 4, 16, tzinfo=timezone.utc),
                results={"document_sentiment": -0.2}
            )
        ]
        mock_analysis_result_crud.get_by_date_range.return_value = mock_results
        
        # Act
        with patch('local_newsifier.services.sentiment_service.analysis_result_crud', 
                  mock_analysis_result_crud):
            service = SentimentService(session_manager=mock_session_manager)
            start_date = datetime(2025, 4, 10, tzinfo=timezone.utc)
            end_date = datetime(2025, 4, 20, tzinfo=timezone.utc)
            result = service.get_sentiment_trends(
                start_date=start_date,
                end_date=end_date
            )
        
        # Assert
        mock_analysis_result_crud.get_by_date_range.assert_called_once_with(
            mock_session,
            analysis_type="sentiment",
            start_date=start_date,
            end_date=end_date
        )
        assert "daily_averages" in result
        assert "entity_sentiment" in result
        assert "topic_sentiment" in result
    
    def test_analyze_article_with_state(self):
        """Test updating NewsAnalysisState with sentiment data."""
        # Arrange
        service = SentimentService()
        state = NewsAnalysisState(
            target_url="https://example.com",
            scraped_text="Some article text",
            status=AnalysisStatus.INITIALIZED
        )
        sentiment_data = {
            "document_sentiment": 0.5,
            "entity_sentiments": {"Joe Biden": 0.2}
        }
        
        # Act
        result = service.analyze_article_with_state(state, sentiment_data)
        
        # Assert
        assert result.status == AnalysisStatus.ANALYSIS_SUCCEEDED
        assert result.analysis_results["sentiment"]["document_sentiment"] == 0.5
        assert result.analysis_results["sentiment"]["entity_sentiments"]["Joe Biden"] == 0.2

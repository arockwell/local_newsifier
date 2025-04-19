"""Unit tests for the refactored SentimentAnalyzer."""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone

from local_newsifier.tools.sentiment_analyzer_v2 import SentimentAnalyzer, SentimentScore
from local_newsifier.models.state import NewsAnalysisState, AnalysisStatus


class TestSentimentAnalyzer:
    """Test cases for the SentimentAnalyzer."""
    
    def test_init_with_dependencies(self):
        """Test initialization with provided dependencies."""
        # Arrange
        mock_session_manager = MagicMock()
        mock_sentiment_service = MagicMock()
        
        # Act
        analyzer = SentimentAnalyzer(
            sentiment_service=mock_sentiment_service,
            session_manager=mock_session_manager,
            model_name="en_core_web_sm"
        )
        
        # Assert
        assert analyzer.sentiment_service == mock_sentiment_service
        assert analyzer.session_manager == mock_session_manager
    
    def test_init_default_dependencies(self):
        """Test initialization with default dependencies."""
        # Arrange
        mock_session_manager = MagicMock()
        mock_sentiment_service = MagicMock()
        
        # Act
        with patch('local_newsifier.tools.sentiment_analyzer_v2.get_session_manager', 
                  return_value=mock_session_manager):
            with patch('local_newsifier.tools.sentiment_analyzer_v2.SentimentService', 
                      return_value=mock_sentiment_service):
                with patch('local_newsifier.tools.sentiment_analyzer_v2.spacy.load'):
                    analyzer = SentimentAnalyzer()
        
        # Assert
        assert analyzer.sentiment_service == mock_sentiment_service
        assert analyzer.session_manager == mock_session_manager
    
    def test_analyze_text_sentiment(self):
        """Test analyzing text sentiment."""
        # Arrange
        with patch('local_newsifier.tools.sentiment_analyzer_v2.spacy.load', MagicMock()):
            analyzer = SentimentAnalyzer()
        
        # Mock TextBlob sentiment
        with patch('local_newsifier.tools.sentiment_analyzer_v2.TextBlob') as mock_textblob:
            mock_blob = MagicMock()
            mock_blob.sentiment.polarity = 0.5
            mock_blob.sentiment.subjectivity = 0.7
            mock_textblob.return_value = mock_blob
            
            # Act
            result = analyzer._analyze_text_sentiment("This is a test text")
        
        # Assert
        assert isinstance(result, SentimentScore)
        assert result["polarity"] == 0.5
        assert result["subjectivity"] == 0.7
    
    def test_analyze_sentiment(self):
        """Test analyzing sentiment for an article state."""
        # Arrange
        mock_sentiment_service = MagicMock()
        mock_sentiment_service.analyze_article_with_state.return_value = MagicMock(
            analysis_results={"sentiment": {"document_sentiment": 0.5}},
            status=AnalysisStatus.ANALYSIS_SUCCEEDED
        )
        
        # Create analyzer with mocked dependencies
        with patch('local_newsifier.tools.sentiment_analyzer_v2.spacy.load', MagicMock()):
            analyzer = SentimentAnalyzer(sentiment_service=mock_sentiment_service)
            
            # Mock internal methods
            analyzer._analyze_text_sentiment = MagicMock(return_value={"polarity": 0.5, "subjectivity": 0.7})
            analyzer._extract_entity_sentiments = MagicMock(return_value={})
            analyzer._extract_topic_sentiments = MagicMock(return_value={})
            
            # Create state
            state = NewsAnalysisState(
                target_url="https://example.com",
                scraped_text="This is a test article",
                status=AnalysisStatus.INITIALIZED
            )
            
            # Act
            result = analyzer.analyze_sentiment(state)
        
        # Assert
        analyzer._analyze_text_sentiment.assert_called_once_with("This is a test article")
        mock_sentiment_service.analyze_article_with_state.assert_called_once()
        assert result.status == AnalysisStatus.ANALYSIS_SUCCEEDED
    
    def test_analyze_article(self):
        """Test analyzing an article by ID."""
        # Arrange
        mock_session = MagicMock()
        mock_session_manager = MagicMock()
        mock_session_manager.session.return_value.__enter__.return_value = mock_session
        
        mock_article = MagicMock(
            id=1,
            url="https://example.com",
            content="This is a test article"
        )
        
        # Create analyzer with mocked dependencies
        with patch('local_newsifier.tools.sentiment_analyzer_v2.spacy.load', MagicMock()):
            analyzer = SentimentAnalyzer(session_manager=mock_session_manager)
            
            # Mock analyze_sentiment method
            mock_state = MagicMock()
            mock_state.analysis_results = {"sentiment": {"document_sentiment": 0.5}}
            analyzer.analyze_sentiment = MagicMock(return_value=mock_state)
            
            # Mock article_crud
            with patch('local_newsifier.tools.sentiment_analyzer_v2.article_crud') as mock_article_crud:
                mock_article_crud.get.return_value = mock_article
                
                # Act
                result = analyzer.analyze_article(article_id=1)
        
        # Assert
        mock_article_crud.get.assert_called_once_with(mock_session, id=1)
        assert result == {"document_sentiment": 0.5}
    
    def test_analyze_article_sentiment(self):
        """Test analyzing and storing article sentiment."""
        # Arrange
        mock_sentiment_service = MagicMock()
        mock_analysis_result = MagicMock()
        mock_sentiment_service.store_sentiment_analysis.return_value = mock_analysis_result
        
        # Create analyzer with mocked dependencies
        with patch('local_newsifier.tools.sentiment_analyzer_v2.spacy.load', MagicMock()):
            analyzer = SentimentAnalyzer(sentiment_service=mock_sentiment_service)
            
            # Mock analyze_article method
            analyzer.analyze_article = MagicMock(return_value={"document_sentiment": 0.5})
            
            # Act
            result = analyzer.analyze_article_sentiment(article_id=1)
        
        # Assert
        analyzer.analyze_article.assert_called_once_with(1)
        mock_sentiment_service.store_sentiment_analysis.assert_called_once_with(
            article_id=1,
            sentiment_results={"document_sentiment": 0.5}
        )
        assert result == mock_analysis_result

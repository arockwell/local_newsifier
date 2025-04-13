"""Tests for the SentimentAnalysisTool."""

import unittest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from pytest_mock import MockFixture

from src.local_newsifier.tools.sentiment_analyzer import SentimentAnalysisTool
from src.local_newsifier.models.state import NewsAnalysisState, AnalysisStatus


class TestSentimentAnalysisTool:
    """Test class for SentimentAnalysisTool."""

    @pytest.fixture
    def sentiment_analyzer(self):
        """Create a sentiment analyzer instance."""
        with patch('spacy.load') as mock_load:
            mock_nlp = MagicMock()
            mock_load.return_value = mock_nlp
            return SentimentAnalysisTool()

    @pytest.fixture
    def mock_state(self):
        """Create a mock state for testing."""
        # Mock the state instead of using actual NewsAnalysisState to avoid validation issues
        state = MagicMock()
        state.article_id = 1
        state.article_url = "https://example.com/article1"
        state.scraped_text = "This is a good test article about climate change. The politicians have failed to address this terrible crisis."
        state.status = None
        state.analysis_results = {}
        state.add_log = MagicMock()
        state.set_error = MagicMock()
        return state

    def test_init_with_spacy_error(self):
        """Test initialization with spaCy load error."""
        with patch('spacy.load') as mock_load:
            mock_load.side_effect = OSError("Model not found")
            analyzer = SentimentAnalysisTool()
            assert analyzer.nlp is None

    def test_analyze_text_sentiment_empty(self, sentiment_analyzer):
        """Test sentiment analysis with empty text."""
        result = sentiment_analyzer._analyze_text_sentiment("")
        assert result["sentiment"] == 0.0
        assert result["magnitude"] == 0.0

    def test_analyze_text_sentiment_positive(self, sentiment_analyzer):
        """Test sentiment analysis with positive text."""
        # Patch the score_sentence method to return a positive score
        with patch.object(sentiment_analyzer, '_score_sentence', return_value=0.5):
            text = "This is good, great, and excellent news. The project was very successful."
            result = sentiment_analyzer._analyze_text_sentiment(text)
            
            # Positive sentiment expected
            assert result["sentiment"] > 0
            assert result["magnitude"] > 0

    def test_analyze_text_sentiment_negative(self, sentiment_analyzer):
        """Test sentiment analysis with negative text."""
        # Patch the score_sentence method to return a negative score
        with patch.object(sentiment_analyzer, '_score_sentence', return_value=-0.5):
            text = "This is bad, terrible, and horrible news. The project was a complete failure."
            result = sentiment_analyzer._analyze_text_sentiment(text)
            
            # Negative sentiment expected
            assert result["sentiment"] < 0
            assert result["magnitude"] > 0

    def test_analyze_text_sentiment_neutral(self, sentiment_analyzer):
        """Test sentiment analysis with neutral text."""
        text = "The meeting is scheduled for tomorrow. We will discuss the project status."
        result = sentiment_analyzer._analyze_text_sentiment(text)
        
        # Neutral sentiment expected (close to zero)
        assert abs(result["sentiment"]) < 0.2

    def test_analyze_text_sentiment_mixed(self, sentiment_analyzer):
        """Test sentiment analysis with mixed text."""
        # Patch the score_sentence method to return different scores for each sentence
        with patch.object(sentiment_analyzer, '_score_sentence', side_effect=[0.5, -0.5]):
            text = "The good news is the project is on schedule, but the bad news is we're over budget."
            result = sentiment_analyzer._analyze_text_sentiment(text)
            
            # Should detect both positive and negative, resulting in a mixed sentiment
            assert result["magnitude"] > 0
            # Sentiment should be neutral (average of positive and negative)
            assert abs(result["sentiment"]) < 0.1

    def test_analyze_text_sentiment_with_negation(self, sentiment_analyzer):
        """Test sentiment analysis with negation."""
        # Set up the mocks
        with patch.object(sentiment_analyzer, '_score_sentence') as mock_score:
            # Return positive score for positive text, negative for negative text
            mock_score.side_effect = [0.5, -0.3]
            
            positive_text = "This is good news."
            negative_text = "This is not good news."
            
            pos_result = sentiment_analyzer._analyze_text_sentiment(positive_text)
            neg_result = sentiment_analyzer._analyze_text_sentiment(negative_text)
            
            # Negation should flip or reduce sentiment
            assert pos_result["sentiment"] > 0
            assert neg_result["sentiment"] < pos_result["sentiment"]

    def test_score_sentence(self, sentiment_analyzer):
        """Test sentence scoring."""
        # Positive sentence
        pos_score = sentiment_analyzer._score_sentence("good great excellent")
        assert pos_score > 0
        
        # Negative sentence
        neg_score = sentiment_analyzer._score_sentence("bad terrible horrible")
        assert neg_score < 0
        
        # Neutral sentence
        neutral_score = sentiment_analyzer._score_sentence("the project schedule")
        assert abs(neutral_score) < 0.1
        
        # Sentence with negation
        negated_score = sentiment_analyzer._score_sentence("not good")
        assert negated_score < 0  # Should be negative or less positive

    def test_extract_entity_sentiments(self, sentiment_analyzer):
        """Test extracting entity sentiments."""
        text = "John Smith is an excellent CEO. ABC Corp has terrible customer service."
        entities = {
            "PERSON": [
                {"text": "John Smith", "sentence": "John Smith is an excellent CEO."}
            ],
            "ORG": [
                {"text": "ABC Corp", "sentence": "ABC Corp has terrible customer service."}
            ]
        }
        
        # Mock the analyze_text_sentiment method to return different sentiments for each sentence
        with patch.object(sentiment_analyzer, '_analyze_text_sentiment') as mock_analyze:
            mock_analyze.side_effect = [
                {"sentiment": 0.7, "magnitude": 0.8},  # Positive for John Smith
                {"sentiment": -0.6, "magnitude": 0.7}  # Negative for ABC Corp
            ]
            
            results = sentiment_analyzer._extract_entity_sentiments(text, entities)
            
            assert "John Smith" in results
            assert "ABC Corp" in results
            assert results["John Smith"] > 0  # Positive sentiment
            assert results["ABC Corp"] < 0  # Negative sentiment

    def test_extract_topic_sentiments_no_nlp(self, sentiment_analyzer):
        """Test extracting topic sentiments when NLP is not available."""
        sentiment_analyzer.nlp = None
        text = "Climate change is a serious problem. Renewable energy is a great solution."
        
        results = sentiment_analyzer._extract_topic_sentiments(text)
        
        # Should return an empty dict if NLP is not available
        assert results == {}

    def test_extract_topic_sentiments_with_nlp(self, sentiment_analyzer):
        """Test extracting topic sentiments with NLP."""
        # Create mock document with noun chunks
        mock_doc = MagicMock()
        
        # Create mock chunks
        mock_chunk1 = MagicMock()
        mock_chunk1.text = "climate change"
        mock_sent1 = MagicMock()
        mock_sent1.text = "Climate change is a serious problem."
        mock_chunk1.sent = mock_sent1
        
        mock_chunk2 = MagicMock()
        mock_chunk2.text = "renewable energy"
        mock_sent2 = MagicMock()
        mock_sent2.text = "Renewable energy is a great solution."
        mock_chunk2.sent = mock_sent2
        
        mock_token = MagicMock()
        mock_token.is_stop = False
        mock_chunk1.__iter__ = lambda s: iter([mock_token])
        mock_chunk2.__iter__ = lambda s: iter([mock_token])
        
        mock_doc.noun_chunks = [mock_chunk1, mock_chunk2]
        
        # Mock both NLP and analyze_text_sentiment
        with patch.object(sentiment_analyzer, 'nlp') as mock_nlp, \
             patch.object(sentiment_analyzer, '_analyze_text_sentiment') as mock_analyze:
            
            # NLP should return our mock document
            mock_nlp.return_value = mock_doc
            
            # Set up mock return values for each sentence
            mock_analyze.side_effect = [
                {"sentiment": -0.5, "magnitude": 0.5},  # For climate change
                {"sentiment": 0.7, "magnitude": 0.5},   # For renewable energy
            ]
            
            text = "Climate change is a serious problem. Renewable energy is a great solution."
            results = sentiment_analyzer._extract_topic_sentiments(text)
            
            assert "climate change" in results
            assert "renewable energy" in results
            assert results["climate change"] < 0  # Negative sentiment
            assert results["renewable energy"] > 0  # Positive sentiment

    def test_analyze_full_state(self, sentiment_analyzer, mock_state):
        """Test full sentiment analysis of state."""
        # Mock the results of the analysis functions
        with patch.object(
            sentiment_analyzer, '_analyze_text_sentiment'
        ) as mock_analyze_text, patch.object(
            sentiment_analyzer, '_extract_topic_sentiments'
        ) as mock_extract_topics:
            
            mock_analyze_text.return_value = {
                "sentiment": 0.5,
                "magnitude": 0.8,
                "sentence_count": 2
            }
            
            mock_extract_topics.return_value = {
                "climate change": -0.3,
                "politicians": -0.6
            }
            
            # Set up state with NER results
            mock_state.analysis_results = {
                "entities": {
                    "PERSON": [
                        {"text": "Politician", "sentence": "The politicians have failed."}
                    ]
                }
            }
            
            # Analyze the state
            result_state = sentiment_analyzer.analyze(mock_state)
            
            # Verify the state was updated correctly
            assert result_state.status == AnalysisStatus.ANALYSIS_SUCCEEDED
            assert "sentiment" in result_state.analysis_results
            assert result_state.analysis_results["sentiment"]["document_sentiment"] == 0.5
            assert result_state.analysis_results["sentiment"]["document_magnitude"] == 0.8
            assert "topic_sentiments" in result_state.analysis_results["sentiment"]
            assert "entity_sentiments" in result_state.analysis_results["sentiment"]

    def test_analyze_empty_content(self, sentiment_analyzer):
        """Test analysis with empty content."""
        # Create a mock state with empty content
        state = MagicMock()
        state.article_id = 1
        state.article_url = "https://example.com/article1"
        state.scraped_text = ""
        state.status = None
        state.set_error = MagicMock()
        
        # Analysis should fail with empty content
        with pytest.raises(ValueError) as excinfo:
            sentiment_analyzer.analyze(state)
        
        assert "No text content available" in str(excinfo.value)
        # Verify error was set
        state.set_error.assert_called_once()

    def test_analyze_article(self, sentiment_analyzer):
        """Test analyzing an article from the database."""
        # Mock database manager
        mock_db_manager = MagicMock()
        
        # Mock article
        mock_article = MagicMock()
        mock_article.id = 1
        mock_article.url = "https://example.com/article1"
        mock_article.content = "This is a good test article."
        mock_db_manager.get_article.return_value = mock_article
        
        # Mock analysis results
        mock_analysis_result = MagicMock()
        mock_analysis_result.analysis_type = "NER"
        mock_analysis_result.results = {
            "entities": {
                "PERSON": [
                    {"text": "John", "sentence": "John is good."}
                ]
            }
        }
        mock_db_manager.get_analysis_results_by_article.return_value = [mock_analysis_result]
        
        # Mock the sentiment analysis method
        with patch.object(sentiment_analyzer, 'analyze') as mock_analyze:
            # Set up the side effect to add sentiment results to the state
            def side_effect(state):
                if not hasattr(state, 'analysis_results'):
                    state.analysis_results = {}
                state.analysis_results["sentiment"] = {
                    "document_sentiment": 0.5,
                    "document_magnitude": 0.8,
                    "entity_sentiments": {"John": 0.6},
                    "topic_sentiments": {"test": 0.5}
                }
                return state
            
            mock_analyze.side_effect = side_effect
            
            # Analyze article
            result = sentiment_analyzer.analyze_article(mock_db_manager, 1)
            
            # Verify result
            assert result["document_sentiment"] == 0.5
            assert result["document_magnitude"] == 0.8
            assert "entity_sentiments" in result
            assert "topic_sentiments" in result
            assert result["entity_sentiments"]["John"] == 0.6
            
            # Verify analysis result was added
            mock_db_manager.add_analysis_result.assert_called_once()

    def test_analyze_article_error(self, sentiment_analyzer):
        """Test error handling in analyze_article."""
        # Mock database manager
        mock_db_manager = MagicMock()
        
        # No article found
        mock_db_manager.get_article.return_value = None
        
        # Should raise ValueError
        with pytest.raises(ValueError) as excinfo:
            sentiment_analyzer.analyze_article(mock_db_manager, 999)
        
        assert "not found" in str(excinfo.value)
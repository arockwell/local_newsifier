import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

# Import with patch to avoid DI issues in tests
with patch('fastapi_injectable.injectable', return_value=lambda cls: cls):
    from local_newsifier.tools.sentiment_analyzer import SentimentAnalysisTool
from local_newsifier.models.state import NewsAnalysisState, AnalysisStatus

@pytest.fixture
def mock_session():
    """Create a mock database session."""
    return MagicMock()

@pytest.fixture
def mock_nlp():
    """Mock spaCy NLP model for testing."""
    mock = MagicMock()
    
    # Mock noun chunks for topic extraction
    mock_doc = MagicMock()
    mock_chunk1 = MagicMock()
    mock_chunk1.text = "downtown cafe"
    mock_chunk1.sent.text = "The new downtown cafe is thriving."
    
    mock_chunk2 = MagicMock()
    mock_chunk2.text = "atmosphere"
    mock_chunk2.sent.text = "Customers love the atmosphere and service."
    
    # Setup for test_analyze_mixed_sentiment
    mock_chunk3 = MagicMock()
    mock_chunk3.text = "food"
    mock_chunk3.sent.text = "The food was excellent but the service was slow and disappointing."
    
    mock_chunk4 = MagicMock()
    mock_chunk4.text = "service"
    mock_chunk4.sent.text = "The food was excellent but the service was slow and disappointing."
    
    # Mock attributes to handle len() and iteration
    mock_chunk1.__len__.return_value = 2
    mock_chunk2.__len__.return_value = 1
    mock_chunk3.__len__.return_value = 1
    mock_chunk4.__len__.return_value = 1
    
    # Set up token.is_stop behavior
    mock_token = MagicMock()
    mock_token.is_stop = False
    mock_chunk1.__iter__.return_value = [mock_token, mock_token]
    mock_chunk2.__iter__.return_value = [mock_token]
    mock_chunk3.__iter__.return_value = [mock_token]
    mock_chunk4.__iter__.return_value = [mock_token]
    
    mock_doc.noun_chunks = [mock_chunk1, mock_chunk2, mock_chunk3, mock_chunk4]
    mock.return_value = mock_doc
    
    return mock

@pytest.fixture
def mock_textblob():
    """Mock TextBlob for sentiment analysis."""
    mock_sentiment = MagicMock()
    mock_sentiment.polarity = 0.75
    mock_sentiment.subjectivity = 0.8
    
    # For test_analyze_negative_sentiment
    mock_negative_sentiment = MagicMock()
    mock_negative_sentiment.polarity = -0.6
    mock_negative_sentiment.subjectivity = 0.9
    
    # For test_analyze_mixed_sentiment
    mock_mixed_sentiment = MagicMock()
    mock_mixed_sentiment.polarity = 0.1
    mock_mixed_sentiment.subjectivity = 0.7
    
    mock_blob_class = MagicMock()
    
    # Different sentiment returns based on input text
    def mock_blob_init(text):
        mock_blob = MagicMock()
        if "terrible" in text or "not recommend" in text:
            mock_blob.sentiment = mock_negative_sentiment
        elif "excellent" in text and "slow" in text:
            mock_blob.sentiment = mock_mixed_sentiment
        else:
            mock_blob.sentiment = mock_sentiment
        return mock_blob
        
    mock_blob_class.side_effect = mock_blob_init
    return mock_blob_class

@pytest.fixture
def sentiment_analyzer(mock_session, mock_nlp, mock_textblob):
    """Create a SentimentAnalyzer instance with mocked dependencies."""
    with patch('spacy.load', return_value=mock_nlp):
        with patch('local_newsifier.tools.sentiment_analyzer.TextBlob', mock_textblob):
            analyzer = SentimentAnalysisTool(session=mock_session)
            return analyzer

@pytest.fixture
def sample_state():
    """Create a sample NewsAnalysisState for testing."""
    return NewsAnalysisState(
        target_url="http://example.com",
        scraped_text="The new downtown cafe is thriving. Customers love the atmosphere and service.",
        status=AnalysisStatus.ANALYSIS_SUCCEEDED,
        analysis_results={}
    )

def test_analyze_document_sentiment(sentiment_analyzer, sample_state):
    """Test document-level sentiment analysis."""
    result = sentiment_analyzer.analyze_sentiment(sample_state)
    
    assert "sentiment" in result.analysis_results
    assert "document_sentiment" in result.analysis_results["sentiment"]
    assert "document_magnitude" in result.analysis_results["sentiment"]
    assert isinstance(result.analysis_results["sentiment"]["document_sentiment"], float)
    assert isinstance(result.analysis_results["sentiment"]["document_magnitude"], float)

def test_analyze_entity_sentiment(sentiment_analyzer, sample_state):
    """Test entity-level sentiment analysis."""
    # Add some entities to the state in the correct format
    sample_state.analysis_results["entities"] = {
        "ORGANIZATION": [{"text": "downtown cafe", "sentence": "The new downtown cafe is thriving."}],
        "PERSON": [{"text": "customers", "sentence": "Customers love the atmosphere and service."}]
    }
    
    result = sentiment_analyzer.analyze_sentiment(sample_state)
    
    assert "sentiment" in result.analysis_results
    assert "entity_sentiments" in result.analysis_results["sentiment"]
    entity_sentiments = result.analysis_results["sentiment"]["entity_sentiments"]
    assert isinstance(entity_sentiments, dict)
    assert len(entity_sentiments) > 0
    assert "downtown cafe" in entity_sentiments
    assert "customers" in entity_sentiments
    assert isinstance(entity_sentiments["downtown cafe"], float)
    assert isinstance(entity_sentiments["customers"], float)

def test_analyze_topic_sentiment(sentiment_analyzer, sample_state):
    """Test topic-level sentiment analysis."""
    # Add some topics to the state
    sample_state.analysis_results["topics"] = [
        "local business",
        "customer satisfaction"
    ]
    
    result = sentiment_analyzer.analyze_sentiment(sample_state)
    
    assert "sentiment" in result.analysis_results
    assert "topic_sentiments" in result.analysis_results["sentiment"]
    assert len(result.analysis_results["sentiment"]["topic_sentiments"]) > 0
    # Topic sentiments are returned as a dictionary mapping topics to sentiment scores
    for topic, sentiment in result.analysis_results["sentiment"]["topic_sentiments"].items():
        assert isinstance(topic, str)
        assert isinstance(sentiment, float)

def test_analyze_empty_text(sentiment_analyzer):
    """Test sentiment analysis with empty text."""
    empty_state = NewsAnalysisState(
        target_url="http://example.com",
        scraped_text="",  # Empty text should be handled by the analyzer
        status=AnalysisStatus.ANALYSIS_SUCCEEDED,
        analysis_results={}
    )
    
    with pytest.raises(ValueError, match="No text content available for analysis"):
        sentiment_analyzer.analyze_sentiment(empty_state)

def test_analyze_negative_sentiment(sentiment_analyzer):
    """Test sentiment analysis with negative text."""
    negative_state = NewsAnalysisState(
        target_url="http://example.com",
        scraped_text="The service was terrible. I would not recommend this place to anyone.",
        status=AnalysisStatus.ANALYSIS_SUCCEEDED,
        analysis_results={}
    )
    
    result = sentiment_analyzer.analyze_sentiment(negative_state)
    
    assert "sentiment" in result.analysis_results
    assert result.analysis_results["sentiment"]["document_sentiment"] < 0
    assert result.analysis_results["sentiment"]["document_magnitude"] > 0

def test_analyze_mixed_sentiment(sentiment_analyzer):
    """Test sentiment analysis with mixed sentiment text."""
    mixed_state = NewsAnalysisState(
        target_url="http://example.com",
        scraped_text="The food was excellent but the service was slow and disappointing.",
        status=AnalysisStatus.ANALYSIS_SUCCEEDED,
        analysis_results={}
    )
    
    result = sentiment_analyzer.analyze_sentiment(mixed_state)
    
    assert "sentiment" in result.analysis_results
    # Mixed sentiment should have lower magnitude than strong positive/negative
    assert abs(result.analysis_results["sentiment"]["document_sentiment"]) < 0.5
    assert result.analysis_results["sentiment"]["document_magnitude"] > 0 
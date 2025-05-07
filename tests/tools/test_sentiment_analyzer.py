import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
from sqlmodel import Session
from local_newsifier.tools.sentiment_analyzer import SentimentAnalysisTool
from local_newsifier.models.state import NewsAnalysisState, AnalysisStatus

@pytest.fixture
def mock_session():
    """Create a mock database session."""
    return MagicMock(spec=Session)

@pytest.fixture
def sentiment_analyzer(mock_session):
    """Create a SentimentAnalyzer instance with mocked spaCy."""
    with patch("spacy.load") as mock_spacy_load:
        # Create a more detailed mock of spaCy NLP
        mock_nlp = MagicMock()
        
        # Create mock chunk for noun chunks
        mock_chunk = MagicMock()
        mock_chunk.text = "downtown cafe"
        
        # Create mock sentence for the chunk
        mock_sent = MagicMock()
        mock_sent.text = "The new downtown cafe is thriving."
        mock_chunk.sent = mock_sent
        
        # Create mock doc with noun chunks
        mock_doc = MagicMock()
        mock_doc.noun_chunks = [mock_chunk]
        
        # Set up the mock nlp to return the mock doc
        mock_nlp.return_value = mock_doc
        
        # Return the mock NLP from spacy.load
        mock_spacy_load.return_value = mock_nlp
        
        analyzer = SentimentAnalysisTool(session=mock_session)
        return analyzer

@patch("spacy.load")
def test_initialization(mock_spacy_load):
    """Test that the class can be initialized properly with dependencies."""
    # Create a mock session and spaCy model
    mock_session = MagicMock(spec=Session)
    mock_nlp = MagicMock()
    mock_spacy_load.return_value = mock_nlp
    
    # Initialize the tool directly
    analyzer = SentimentAnalysisTool(session=mock_session)
    
    # Assert
    assert analyzer.session == mock_session
    assert analyzer.nlp == mock_nlp
    mock_spacy_load.assert_called_once_with("en_core_web_sm")

@pytest.fixture
def sample_state():
    """Create a sample NewsAnalysisState for testing."""
    return NewsAnalysisState(
        target_url="http://example.com",
        scraped_text="The new downtown cafe is thriving. Customers love the atmosphere and service.",
        status=AnalysisStatus.ANALYSIS_SUCCEEDED,
        analysis_results={}
    )

@patch("textblob.TextBlob")
def test_analyze_document_sentiment(mock_textblob, sentiment_analyzer, sample_state):
    """Test document-level sentiment analysis."""
    # Mock the TextBlob sentiment return value
    mock_sentiment = MagicMock()
    mock_sentiment.polarity = 0.5
    mock_sentiment.subjectivity = 0.8
    
    mock_blob = MagicMock()
    mock_blob.sentiment = mock_sentiment
    mock_textblob.return_value = mock_blob
    
    result = sentiment_analyzer.analyze_sentiment(sample_state)
    
    assert "sentiment" in result.analysis_results
    assert "document_sentiment" in result.analysis_results["sentiment"]
    assert "document_magnitude" in result.analysis_results["sentiment"]
    assert isinstance(result.analysis_results["sentiment"]["document_sentiment"], float)
    assert isinstance(result.analysis_results["sentiment"]["document_magnitude"], float)

@patch("textblob.TextBlob")
def test_analyze_entity_sentiment(mock_textblob, sentiment_analyzer, sample_state):
    """Test entity-level sentiment analysis."""
    # Mock the TextBlob sentiment return value
    mock_sentiment = MagicMock()
    mock_sentiment.polarity = 0.7
    mock_sentiment.subjectivity = 0.6
    
    mock_blob = MagicMock()
    mock_blob.sentiment = mock_sentiment
    mock_textblob.return_value = mock_blob
    
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
    # Directly patch the internal method to return some topic sentiments
    with patch.object(
        sentiment_analyzer, 
        '_extract_topic_sentiments',
        return_value={"downtown cafe": 0.5, "customer satisfaction": -0.2}
    ):
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

@patch("textblob.TextBlob")
def test_analyze_negative_sentiment(mock_textblob, sentiment_analyzer):
    """Test sentiment analysis with negative text."""
    # Mock the TextBlob sentiment return value with negative polarity
    mock_sentiment = MagicMock()
    mock_sentiment.polarity = -0.7
    mock_sentiment.subjectivity = 0.8
    
    mock_blob = MagicMock()
    mock_blob.sentiment = mock_sentiment
    mock_textblob.return_value = mock_blob
    
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

@patch("textblob.TextBlob")
def test_analyze_mixed_sentiment(mock_textblob, sentiment_analyzer):
    """Test sentiment analysis with mixed sentiment text."""
    # Mock the TextBlob sentiment return value with mixed (slightly positive) polarity
    mock_sentiment = MagicMock()
    mock_sentiment.polarity = 0.2 # Slightly positive
    mock_sentiment.subjectivity = 0.9
    
    mock_blob = MagicMock()
    mock_blob.sentiment = mock_sentiment
    mock_textblob.return_value = mock_blob
    
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
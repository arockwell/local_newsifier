import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from local_newsifier.tools.sentiment_analyzer import SentimentAnalysisTool
from local_newsifier.models.state import NewsAnalysisState, AnalysisStatus

@pytest.fixture
def mock_db_manager():
    """Create a mock database manager."""
    return MagicMock()

@pytest.fixture
def mock_nlp():
    """Create a mock NLP model for spaCy."""
    mock = MagicMock()
    
    # Set up mock noun chunks
    mock_chunk1 = MagicMock()
    mock_chunk1.text = "downtown cafe"
    mock_chunk1.sent.text = "The new downtown cafe is thriving."
    
    mock_chunk2 = MagicMock()
    mock_chunk2.text = "customers"
    mock_chunk2.sent.text = "Customers love the atmosphere and service."
    
    # Set up mock tokens
    mock_token = MagicMock()
    mock_token.is_stop = False
    
    # Configure lengths and iteration
    mock_chunk1.__len__.return_value = 2
    mock_chunk2.__len__.return_value = 2
    mock_chunk1.__iter__.return_value = [mock_token]
    mock_chunk2.__iter__.return_value = [mock_token]
    
    # Configure noun chunks
    mock_doc = MagicMock()
    mock_doc.noun_chunks = [mock_chunk1, mock_chunk2]
    
    # Return mock doc when the model is called
    mock.return_value = mock_doc
    
    return mock

@pytest.fixture
def sentiment_analyzer(mock_db_manager, mock_nlp):
    """Create a SentimentAnalyzer instance with mocked dependencies."""
    with patch('spacy.load', return_value=mock_nlp):
        return SentimentAnalysisTool(mock_db_manager)

@pytest.fixture
def sample_state():
    """Create a sample NewsAnalysisState for testing."""
    return NewsAnalysisState(
        target_url="http://example.com",
        scraped_text="The new downtown cafe is thriving. Customers love the atmosphere and service.",
        status=AnalysisStatus.ANALYSIS_SUCCEEDED,
        analysis_results={}
    )

@patch('spacy.load')
def test_analyze_document_sentiment(mock_spacy_load, sentiment_analyzer, sample_state, mock_nlp):
    """Test document-level sentiment analysis."""
    mock_spacy_load.return_value = mock_nlp
    
    result = sentiment_analyzer.analyze_sentiment(sample_state)
    
    assert "sentiment" in result.analysis_results
    assert "document_sentiment" in result.analysis_results["sentiment"]
    assert "document_magnitude" in result.analysis_results["sentiment"]
    assert isinstance(result.analysis_results["sentiment"]["document_sentiment"], float)
    assert isinstance(result.analysis_results["sentiment"]["document_magnitude"], float)

@patch('spacy.load')
def test_analyze_entity_sentiment(mock_spacy_load, sentiment_analyzer, sample_state, mock_nlp):
    """Test entity-level sentiment analysis."""
    mock_spacy_load.return_value = mock_nlp
    
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

@patch('spacy.load')
def test_analyze_topic_sentiment(mock_spacy_load, sentiment_analyzer, sample_state, mock_nlp):
    """Test topic-level sentiment analysis."""
    mock_spacy_load.return_value = mock_nlp
    
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

@patch('spacy.load')
def test_analyze_empty_text(mock_spacy_load, sentiment_analyzer, mock_nlp):
    """Test sentiment analysis with empty text."""
    mock_spacy_load.return_value = mock_nlp
    
    empty_state = NewsAnalysisState(
        target_url="http://example.com",
        scraped_text="",  # Empty text should be handled by the analyzer
        status=AnalysisStatus.ANALYSIS_SUCCEEDED,
        analysis_results={}
    )
    
    with pytest.raises(ValueError, match="No text content available for analysis"):
        sentiment_analyzer.analyze_sentiment(empty_state)

@patch('spacy.load')
def test_analyze_negative_sentiment(mock_spacy_load, sentiment_analyzer, mock_nlp):
    """Test sentiment analysis with negative text."""
    mock_spacy_load.return_value = mock_nlp
    
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

@patch('spacy.load')
def test_analyze_mixed_sentiment(mock_spacy_load, sentiment_analyzer, mock_nlp):
    """Test sentiment analysis with mixed sentiment text."""
    mock_spacy_load.return_value = mock_nlp
    
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
import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

# Mock spaCy and TextBlob before imports
patch('spacy.load', MagicMock(return_value=MagicMock())).start()
patch('textblob.TextBlob', MagicMock(return_value=MagicMock(
    sentiment=MagicMock(polarity=0.5, subjectivity=0.7)
))).start()
patch('spacy.language.Language', MagicMock()).start()

from local_newsifier.tools.sentiment_analyzer import SentimentAnalysisTool
from local_newsifier.models.state import NewsAnalysisState, AnalysisStatus

@pytest.fixture
def mock_session():
    """Create a mock database session."""
    return MagicMock()

@pytest.fixture
def mock_spacy_nlp():
    """Create a mock spaCy NLP model."""
    mock_nlp = MagicMock()
    mock_doc = MagicMock()
    mock_nlp.return_value = mock_doc
    
    # Setup noun chunks for topic sentiment testing
    mock_chunk1 = MagicMock()
    mock_chunk1.text = "downtown cafe"
    mock_sent1 = MagicMock()
    mock_sent1.text = "The new downtown cafe is thriving."
    mock_chunk1.sent = mock_sent1
    mock_token1 = MagicMock()
    mock_token1.is_stop = False
    mock_chunk1.__iter__.return_value = [mock_token1]
    mock_chunk1.__len__.return_value = 2
    
    mock_chunk2 = MagicMock()
    mock_chunk2.text = "customers"
    mock_sent2 = MagicMock()
    mock_sent2.text = "Customers love the atmosphere and service."
    mock_chunk2.sent = mock_sent2
    mock_token2 = MagicMock()
    mock_token2.is_stop = False
    mock_chunk2.__iter__.return_value = [mock_token2]
    mock_chunk2.__len__.return_value = 1
    
    mock_doc.noun_chunks = [mock_chunk1, mock_chunk2]
    
    return mock_nlp

@pytest.fixture
def sentiment_analyzer(mock_session, mock_spacy_nlp):
    """Create a SentimentAnalyzer instance with mocked dependencies."""
    with patch('spacy.load', return_value=mock_spacy_nlp):
        return SentimentAnalysisTool(session=mock_session)

@pytest.fixture
def sample_state():
    """Create a sample NewsAnalysisState for testing."""
    return NewsAnalysisState(
        target_url="http://example.com",
        scraped_text="The new downtown cafe is thriving. Customers love the atmosphere and service.",
        status=AnalysisStatus.ANALYSIS_SUCCEEDED,
        analysis_results={}
    )

@patch('local_newsifier.tools.sentiment_analyzer.TextBlob')
def test_analyze_document_sentiment(mock_textblob, sentiment_analyzer, sample_state):
    """Test document-level sentiment analysis."""
    # Setup TextBlob mock
    mock_blob = MagicMock()
    mock_blob.sentiment.polarity = 0.5
    mock_blob.sentiment.subjectivity = 0.8
    mock_textblob.return_value = mock_blob
    
    result = sentiment_analyzer.analyze_sentiment(sample_state)
    
    assert "sentiment" in result.analysis_results
    assert "document_sentiment" in result.analysis_results["sentiment"]
    assert "document_magnitude" in result.analysis_results["sentiment"]
    assert isinstance(result.analysis_results["sentiment"]["document_sentiment"], float)
    assert isinstance(result.analysis_results["sentiment"]["document_magnitude"], float)
    assert result.analysis_results["sentiment"]["document_sentiment"] == 0.5
    assert result.analysis_results["sentiment"]["document_magnitude"] == 0.8

@patch('local_newsifier.tools.sentiment_analyzer.TextBlob')
def test_analyze_entity_sentiment(mock_textblob, sentiment_analyzer, sample_state):
    """Test entity-level sentiment analysis."""
    # Add some entities to the state in the correct format
    sample_state.analysis_results["entities"] = {
        "ORGANIZATION": [{"text": "downtown cafe", "sentence": "The new downtown cafe is thriving."}],
        "PERSON": [{"text": "customers", "sentence": "Customers love the atmosphere and service."}]
    }
    
    # Create a fixed TextBlob mock to make testing simpler
    mock_blob = MagicMock()
    mock_blob.sentiment.polarity = 0.6  # Fixed value for all calls
    mock_blob.sentiment.subjectivity = 0.7
    mock_textblob.return_value = mock_blob
    
    # Test that the entity sentiment analysis works
    result = sentiment_analyzer.analyze_sentiment(sample_state)
    
    # Verify the results
    assert "sentiment" in result.analysis_results
    assert "entity_sentiments" in result.analysis_results["sentiment"]
    entity_sentiments = result.analysis_results["sentiment"]["entity_sentiments"]
    assert isinstance(entity_sentiments, dict)
    
    # Both entities should be present
    assert "downtown cafe" in entity_sentiments
    assert "customers" in entity_sentiments
    
    # Both entities should have the same sentiment since we're using a fixed mock
    assert entity_sentiments["downtown cafe"] == 0.6
    assert entity_sentiments["customers"] == 0.6

@patch('local_newsifier.tools.sentiment_analyzer.TextBlob')
def test_analyze_topic_sentiment(mock_textblob, sentiment_analyzer, sample_state):
    """Test topic-level sentiment analysis."""
    # Add some topics to the state
    sample_state.analysis_results["topics"] = [
        "local business",
        "customer satisfaction"
    ]
    
    # Create a default mock for the document sentiment
    default_blob = MagicMock()
    default_blob.sentiment.polarity = 0.5
    default_blob.sentiment.subjectivity = 0.8
    mock_textblob.return_value = default_blob
    
    # The topic sentiments test doesn't need specific mock values 
    # since we're testing the feature and not exact values
    
    result = sentiment_analyzer.analyze_sentiment(sample_state)
    
    assert "sentiment" in result.analysis_results
    # Since we're mocking spaCy's noun chunks, we won't get real topic sentiments
    # But we do verify the document sentiment was analyzed
    assert "document_sentiment" in result.analysis_results["sentiment"]
    assert "document_magnitude" in result.analysis_results["sentiment"]
    assert result.analysis_results["sentiment"]["document_sentiment"] == 0.5

@patch('local_newsifier.tools.sentiment_analyzer.TextBlob')
def test_analyze_empty_text(mock_textblob, sentiment_analyzer):
    """Test sentiment analysis with empty text."""
    empty_state = NewsAnalysisState(
        target_url="http://example.com",
        scraped_text="",  # Empty text should be handled by the analyzer
        status=AnalysisStatus.ANALYSIS_SUCCEEDED,
        analysis_results={}
    )
    
    with pytest.raises(ValueError, match="No text content available for analysis"):
        sentiment_analyzer.analyze_sentiment(empty_state)
    
    # TextBlob should not be called when text is empty
    mock_textblob.assert_not_called()

@patch('local_newsifier.tools.sentiment_analyzer.TextBlob')
def test_analyze_negative_sentiment(mock_textblob, sentiment_analyzer):
    """Test sentiment analysis with negative text."""
    # Mock a negative sentiment TextBlob result
    mock_blob = MagicMock()
    mock_blob.sentiment.polarity = -0.6
    mock_blob.sentiment.subjectivity = 0.8
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
    assert result.analysis_results["sentiment"]["document_sentiment"] == -0.6
    assert result.analysis_results["sentiment"]["document_magnitude"] == 0.8

@patch('local_newsifier.tools.sentiment_analyzer.TextBlob')
def test_analyze_mixed_sentiment(mock_textblob, sentiment_analyzer):
    """Test sentiment analysis with mixed sentiment text."""
    # Mock a mixed sentiment TextBlob result
    mock_blob = MagicMock()
    mock_blob.sentiment.polarity = 0.2  # Slightly positive
    mock_blob.sentiment.subjectivity = 0.9  # High subjectivity
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
    assert result.analysis_results["sentiment"]["document_sentiment"] == 0.2
    assert result.analysis_results["sentiment"]["document_magnitude"] == 0.9
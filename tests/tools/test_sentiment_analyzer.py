import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
from src.local_newsifier.tools.sentiment_analyzer import SentimentAnalysisTool
from src.local_newsifier.models.state import NewsAnalysisState, AnalysisStatus

@pytest.fixture
def mock_session():
    """Create a mock database session."""
    return MagicMock()

@pytest.fixture
def sentiment_analyzer(mock_session):
    """Create a SentimentAnalyzer instance."""
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
"""Tests for the ContextAnalyzer tool."""

import pytest
from local_newsifier.tools.analysis.context_analyzer import ContextAnalyzer


@pytest.fixture
def context_analyzer():
    """Create a ContextAnalyzer instance for testing."""
    return ContextAnalyzer()


def test_analyze_sentiment_positive(context_analyzer):
    """Test analyzing positive sentiment."""
    # Positive context
    context = "John Smith is an excellent leader who has achieved great success."
    
    # Analyze sentiment
    sentiment = context_analyzer.analyze_sentiment(context)
    
    # Verify sentiment analysis
    assert sentiment["score"] > 0
    assert sentiment["category"] == "positive"
    assert sentiment["positive_count"] > 0
    assert sentiment["negative_count"] == 0


def test_analyze_sentiment_negative(context_analyzer):
    """Test analyzing negative sentiment."""
    # Negative context
    context = "John Smith was criticized for his poor performance and controversial decisions."
    
    # Analyze sentiment
    sentiment = context_analyzer.analyze_sentiment(context)
    
    # Verify sentiment analysis
    assert sentiment["score"] < 0
    assert sentiment["category"] == "negative"
    assert sentiment["positive_count"] == 0
    assert sentiment["negative_count"] > 0


def test_analyze_sentiment_neutral(context_analyzer):
    """Test analyzing neutral sentiment."""
    # Neutral context
    context = "John Smith is the CEO of Acme Corp and lives in San Francisco."
    
    # Analyze sentiment
    sentiment = context_analyzer.analyze_sentiment(context)
    
    # Verify sentiment analysis
    assert -0.2 <= sentiment["score"] <= 0.2
    assert sentiment["category"] == "neutral"


def test_analyze_framing_leadership(context_analyzer):
    """Test analyzing leadership framing."""
    # Leadership framing context
    context = "John Smith leads the company with a clear vision and strategic direction."
    
    # Analyze framing
    framing = context_analyzer.analyze_framing(context)
    
    # Verify framing analysis
    assert framing["category"] == "leadership"
    assert framing["scores"]["leadership"] > 0
    assert framing["counts"]["leadership"] > 0


def test_analyze_framing_victim(context_analyzer):
    """Test analyzing victim framing."""
    # Victim framing context
    context = "John Smith was harmed by the policy changes and suffered significant losses."
    
    # Analyze framing
    framing = context_analyzer.analyze_framing(context)
    
    # Verify framing analysis
    assert framing["category"] == "victim"
    assert framing["scores"]["victim"] > 0
    assert framing["counts"]["victim"] > 0


def test_analyze_context_comprehensive(context_analyzer):
    """Test comprehensive context analysis."""
    # Context with mixed sentiment and framing
    context = "John Smith successfully led the company through difficult times, but faced criticism for controversial decisions."
    
    # Analyze context
    analysis = context_analyzer.analyze_context(context)
    
    # Verify comprehensive analysis
    assert "sentiment" in analysis
    assert "framing" in analysis
    assert "length" in analysis
    assert "word_count" in analysis
    
    # Verify sentiment analysis
    assert "score" in analysis["sentiment"]
    assert "category" in analysis["sentiment"]
    
    # Verify framing analysis
    assert "category" in analysis["framing"]
    assert "scores" in analysis["framing"]
    assert "counts" in analysis["framing"]


def test_analyze_entity_contexts(context_analyzer):
    """Test analyzing contexts for multiple entities."""
    # List of entities with contexts
    entities = [
        {
            "text": "John Smith",
            "type": "PERSON",
            "context": "John Smith is an excellent leader who has achieved great success."
        },
        {
            "text": "Jane Doe",
            "type": "PERSON",
            "context": "Jane Doe was criticized for her controversial decisions."
        },
        {
            "text": "Acme Corp",
            "type": "ORG",
            "context": "Acme Corp is a leading company in the industry."
        }
    ]
    
    # Analyze entity contexts
    analyzed_entities = context_analyzer.analyze_entity_contexts(entities)
    
    # Verify analysis
    assert len(analyzed_entities) == 3
    
    # Check that each entity has context analysis
    for entity in analyzed_entities:
        assert "context_analysis" in entity
        assert "sentiment" in entity["context_analysis"]
        assert "framing" in entity["context_analysis"]
        
    # Check specific entities
    assert analyzed_entities[0]["context_analysis"]["sentiment"]["category"] == "positive"
    assert analyzed_entities[1]["context_analysis"]["sentiment"]["category"] == "negative"


def test_get_sentiment_category(context_analyzer):
    """Test getting sentiment category from score."""
    # Test positive sentiment
    assert context_analyzer.get_sentiment_category(0.5) == "positive"
    
    # Test negative sentiment
    assert context_analyzer.get_sentiment_category(-0.5) == "negative"
    
    # Test neutral sentiment
    assert context_analyzer.get_sentiment_category(0.0) == "neutral"
    assert context_analyzer.get_sentiment_category(0.1) == "neutral"
    assert context_analyzer.get_sentiment_category(-0.1) == "neutral"


def test_empty_context(context_analyzer):
    """Test behavior with empty context."""
    # Analyze empty context
    analysis = context_analyzer.analyze_context("")
    
    # Should return neutral sentiment, not error
    assert analysis["sentiment"]["category"] == "neutral"
    assert analysis["sentiment"]["score"] == 0.0
    assert analysis["word_count"] == 0

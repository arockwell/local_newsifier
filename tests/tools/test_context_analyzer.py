"""Tests for the Context Analyzer tool."""

from unittest.mock import Mock, patch

import pytest
import spacy

from local_newsifier.tools.context_analyzer import ContextAnalyzer


class MockSent:
    """Mock spaCy sentence."""
    
    def __init__(self, text):
        self.text = text


class MockToken:
    """Mock spaCy token."""
    
    def __init__(self, text, lemma):
        self.text = text
        self.lemma_ = lemma


class MockDoc:
    """Mock spaCy document."""
    
    def __init__(self, tokens, sents):
        self.tokens = tokens
        self.sents = sents
    
    def __iter__(self):
        return iter(self.tokens)


@pytest.fixture
def mock_nlp():
    """Create a mock spaCy NLP model."""
    nlp = Mock()
    
    # Sample sentences
    sents = [
        MockSent("Joe Biden is the president of the United States."),
        MockSent("He has implemented several policies during his term."),
        MockSent("Critics say some policies have been controversial.")
    ]
    
    # Sample tokens with positive sentiment
    positive_tokens = [
        MockToken("good", "good"),
        MockToken("great", "great"),
        MockToken("success", "success")
    ]
    
    # Sample tokens with negative sentiment
    negative_tokens = [
        MockToken("bad", "bad"),
        MockToken("controversial", "controversial")
    ]
    
    # Sample tokens with framing
    framing_tokens = [
        MockToken("leader", "leader"),
        MockToken("president", "president"),
        MockToken("critics", "critic")
    ]
    
    # Create mock document
    doc = MockDoc(
        positive_tokens + negative_tokens + framing_tokens,
        sents
    )
    
    nlp.return_value = doc
    
    return nlp


@patch("spacy.load")
def test_context_analyzer_init(mock_spacy_load):
    """Test initializing the context analyzer."""
    mock_spacy_load.return_value = Mock()
    
    analyzer = ContextAnalyzer()
    
    mock_spacy_load.assert_called_once_with("en_core_web_lg")
    assert analyzer.nlp is not None


@patch("spacy.load")
def test_context_analyzer_extract_context(mock_spacy_load, mock_nlp):
    """Test extracting context around an entity mention."""
    mock_spacy_load.return_value = mock_nlp
    
    analyzer = ContextAnalyzer()
    
    # Test with found entity
    context = analyzer.extract_context(
        "Joe Biden is the president. He has implemented policies.",
        "Joe Biden"
    )
    
    assert "Joe Biden" in context
    assert len(context) > 0


@patch("spacy.load")
def test_context_analyzer_analyze_sentiment(mock_spacy_load, mock_nlp):
    """Test analyzing sentiment in context."""
    mock_spacy_load.return_value = mock_nlp
    
    analyzer = ContextAnalyzer()
    
    # Test with mixed sentiment
    sentiment = analyzer.analyze_sentiment(
        "Joe Biden has done some good things but also made some bad decisions."
    )
    
    assert "score" in sentiment
    assert "positive_count" in sentiment
    assert "negative_count" in sentiment
    assert sentiment["positive_count"] >= 1
    assert sentiment["negative_count"] >= 1


@patch("spacy.load")
def test_context_analyzer_analyze_framing(mock_spacy_load, mock_nlp):
    """Test analyzing framing in context."""
    mock_spacy_load.return_value = mock_nlp
    
    analyzer = ContextAnalyzer()
    
    # Test with leadership framing
    framing = analyzer.analyze_framing(
        "Joe Biden is a leader who has taken charge of the situation."
    )
    
    assert "category" in framing
    assert "scores" in framing
    assert "counts" in framing
    
    # Check for leadership framing
    assert framing["category"] in analyzer.framing_categories or framing["category"] == "neutral"


@patch("spacy.load")
def test_context_analyzer_analyze_context(mock_spacy_load, mock_nlp):
    """Test complete context analysis."""
    mock_spacy_load.return_value = mock_nlp
    
    analyzer = ContextAnalyzer()
    
    # Test complete analysis
    analysis = analyzer.analyze_context(
        "Joe Biden is a good leader who has made some controversial decisions."
    )
    
    assert "sentiment" in analysis
    assert "framing" in analysis
    assert "length" in analysis
    assert "word_count" in analysis
    
    assert analysis["sentiment"]["score"] is not None
    assert analysis["framing"]["category"] is not None
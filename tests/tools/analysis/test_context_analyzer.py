"""
Tests for the Context Analyzer tool.

This test suite covers:
1. Sentiment analysis functionality
2. Framing detection and categorization
3. Context window handling
4. Analysis with minimal or empty context
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from local_newsifier.tools.analysis.context_analyzer import ContextAnalyzer


class MockSpacyDoc:
    """Mock spaCy Doc for testing."""
    
    def __init__(self, tokens=None):
        self.tokens = tokens or []
    
    def __iter__(self):
        return iter(self.tokens)


class MockSpacyToken:
    """Mock spaCy Token for testing."""
    
    def __init__(self, text, lemma_):
        self.text = text
        self.lemma_ = lemma_


@pytest.fixture
def mock_spacy_model():
    """Create a mock spaCy model."""
    with patch('spacy.load') as mock_load:
        mock_nlp = Mock()
        mock_load.return_value = mock_nlp
        yield mock_nlp


@pytest.fixture
def context_analyzer(mock_spacy_model):
    """Create a ContextAnalyzer instance with mocked spaCy model."""
    analyzer = ContextAnalyzer()
    return analyzer


@pytest.fixture
def positive_tokens():
    """Create tokens with positive sentiment words."""
    return [
        MockSpacyToken("good", "good"),
        MockSpacyToken("excellent", "excellent"),
        MockSpacyToken("impressive", "impressive"),
        MockSpacyToken("words", "word")
    ]


@pytest.fixture
def negative_tokens():
    """Create tokens with negative sentiment words."""
    return [
        MockSpacyToken("bad", "bad"),
        MockSpacyToken("terrible", "terrible"),
        MockSpacyToken("disappointing", "disappointing"),
        MockSpacyToken("words", "word")
    ]


@pytest.fixture
def neutral_tokens():
    """Create tokens with neutral sentiment words."""
    return [
        MockSpacyToken("the", "the"),
        MockSpacyToken("is", "be"),
        MockSpacyToken("a", "a"),
        MockSpacyToken("person", "person")
    ]


@pytest.fixture
def leadership_tokens():
    """Create tokens with leadership framing words."""
    return [
        MockSpacyToken("leader", "leader"),
        MockSpacyToken("executive", "executive"),
        MockSpacyToken("vision", "vision"),
        MockSpacyToken("words", "word")
    ]


@pytest.fixture
def victim_tokens():
    """Create tokens with victim framing words."""
    return [
        MockSpacyToken("victim", "victim"),
        MockSpacyToken("suffered", "suffer"),
        MockSpacyToken("harmed", "harm"),
        MockSpacyToken("words", "word")
    ]


class TestContextAnalyzer:
    """Test suite for ContextAnalyzer."""
    
    def test_initialization(self, mock_spacy_model):
        """Test initialization of ContextAnalyzer."""
        analyzer = ContextAnalyzer()
        assert analyzer.nlp is mock_spacy_model
        assert isinstance(analyzer.sentiment_words, dict)
        assert isinstance(analyzer.framing_categories, dict)
    
    def test_initialization_error(self):
        """Test initialization error handling."""
        with patch('spacy.load', side_effect=OSError("Model not found")):
            # Should not raise an exception, but set nlp to None
            analyzer = ContextAnalyzer()
            assert analyzer.nlp is None
    
    def test_analyze_sentiment_positive(self, context_analyzer, mock_spacy_model, positive_tokens):
        """Test sentiment analysis with positive text."""
        # Setup mock document with positive tokens
        mock_doc = MockSpacyDoc(tokens=positive_tokens)
        mock_spacy_model.return_value = mock_doc
        
        # Analyze sentiment
        result = context_analyzer.analyze_sentiment("This is a positive text.")
        
        # Verify results
        assert result["score"] > 0
        assert result["category"] == "positive"
        assert result["positive_count"] == 3
        assert result["negative_count"] == 0
        assert result["total_count"] == 3
    
    def test_analyze_sentiment_negative(self, context_analyzer, mock_spacy_model, negative_tokens):
        """Test sentiment analysis with negative text."""
        # Setup mock document with negative tokens
        mock_doc = MockSpacyDoc(tokens=negative_tokens)
        mock_spacy_model.return_value = mock_doc
        
        # Analyze sentiment
        result = context_analyzer.analyze_sentiment("This is a negative text.")
        
        # Verify results
        assert result["score"] < 0
        assert result["category"] == "negative"
        assert result["positive_count"] == 0
        assert result["negative_count"] == 3
        assert result["total_count"] == 3
    
    def test_analyze_sentiment_neutral(self, context_analyzer, mock_spacy_model, neutral_tokens):
        """Test sentiment analysis with neutral text."""
        # Setup mock document with neutral tokens
        mock_doc = MockSpacyDoc(tokens=neutral_tokens)
        mock_spacy_model.return_value = mock_doc
        
        # Analyze sentiment
        result = context_analyzer.analyze_sentiment("This is a neutral text.")
        
        # Verify results
        assert result["score"] == 0.0
        assert result["category"] == "neutral"
        assert result["positive_count"] == 0
        assert result["negative_count"] == 0
        assert result["total_count"] == 0
    
    def test_analyze_sentiment_mixed(self, context_analyzer, mock_spacy_model):
        """Test sentiment analysis with mixed sentiment."""
        # Create mixed tokens
        mixed_tokens = [
            MockSpacyToken("good", "good"),
            MockSpacyToken("but", "but"),
            MockSpacyToken("disappointing", "disappointing")
        ]
        
        # Setup mock document with mixed tokens
        mock_doc = MockSpacyDoc(tokens=mixed_tokens)
        mock_spacy_model.return_value = mock_doc
        
        # Analyze sentiment
        result = context_analyzer.analyze_sentiment("This is a mixed sentiment text.")
        
        # Verify results
        assert result["positive_count"] == 1
        assert result["negative_count"] == 1
        assert result["total_count"] == 2
        assert result["score"] == 0.0  # Equal positive and negative
        assert result["category"] == "neutral"
    
    def test_analyze_sentiment_no_nlp(self, context_analyzer):
        """Test sentiment analysis when NLP model is not available."""
        # Set nlp to None to simulate unavailable model
        context_analyzer.nlp = None
        
        # Analyze sentiment
        result = context_analyzer.analyze_sentiment("This text won't be processed.")
        
        # Verify default results
        assert result["score"] == 0.0
        assert result["category"] == "neutral"
        assert result["positive_count"] == 0
        assert result["negative_count"] == 0
        assert result["total_count"] == 0
    
    def test_analyze_framing_leadership(self, context_analyzer, mock_spacy_model, leadership_tokens):
        """Test framing analysis with leadership framing."""
        # Setup mock document with leadership tokens
        mock_doc = MockSpacyDoc(tokens=leadership_tokens)
        mock_spacy_model.return_value = mock_doc
        
        # Analyze framing
        result = context_analyzer.analyze_framing("This text has leadership framing.")
        
        # Verify results
        assert result["category"] == "leadership"
        assert result["scores"]["leadership"] > 0
        assert result["counts"]["leadership"] == 3
        assert result["total_count"] == 3
    
    def test_analyze_framing_victim(self, context_analyzer, mock_spacy_model, victim_tokens):
        """Test framing analysis with victim framing."""
        # Setup mock document with victim tokens
        mock_doc = MockSpacyDoc(tokens=victim_tokens)
        mock_spacy_model.return_value = mock_doc
        
        # Analyze framing
        result = context_analyzer.analyze_framing("This text has victim framing.")
        
        # Verify results
        assert result["category"] == "victim"
        assert result["scores"]["victim"] > 0
        assert result["counts"]["victim"] == 3
        assert result["total_count"] == 3
    
    def test_analyze_framing_neutral(self, context_analyzer, mock_spacy_model, neutral_tokens):
        """Test framing analysis with neutral text."""
        # Setup mock document with neutral tokens
        mock_doc = MockSpacyDoc(tokens=neutral_tokens)
        mock_spacy_model.return_value = mock_doc
        
        # Analyze framing
        result = context_analyzer.analyze_framing("This is a neutral text.")
        
        # Verify results
        assert result["category"] == "neutral"
        assert all(score == 0.0 for score in result["scores"].values())
        assert all(count == 0 for count in result["counts"].values())
        assert result["total_count"] == 0
    
    def test_analyze_framing_mixed(self, context_analyzer, mock_spacy_model):
        """Test framing analysis with mixed framing."""
        # Create mixed tokens
        mixed_tokens = [
            MockSpacyToken("leader", "leader"),
            MockSpacyToken("and", "and"),
            MockSpacyToken("victim", "victim")
        ]
        
        # Setup mock document with mixed tokens
        mock_doc = MockSpacyDoc(tokens=mixed_tokens)
        mock_spacy_model.return_value = mock_doc
        
        # Analyze framing
        result = context_analyzer.analyze_framing("This text has mixed framing.")
        
        # Verify results
        assert result["counts"]["leadership"] == 1
        assert result["counts"]["victim"] == 1
        assert result["total_count"] == 2
        # The dominant category depends on the order in which they're checked
        assert result["category"] in ["leadership", "victim"]
    
    def test_analyze_framing_no_nlp(self, context_analyzer):
        """Test framing analysis when NLP model is not available."""
        # Set nlp to None to simulate unavailable model
        context_analyzer.nlp = None
        
        # Analyze framing
        result = context_analyzer.analyze_framing("This text won't be processed.")
        
        # Verify default results
        assert result["category"] == "neutral"
        assert all(score == 0.0 for score in result["scores"].values())
        assert all(count == 0 for count in result["counts"].values())
        assert result["total_count"] == 0
    
    def test_analyze_context(self, context_analyzer, mock_spacy_model, positive_tokens, leadership_tokens):
        """Test comprehensive context analysis."""
        # For this test, we'll mock the analyze_sentiment and analyze_framing methods directly
        # to ensure they return the expected values
        context_analyzer.analyze_sentiment = Mock(return_value={
            "score": 0.5,
            "category": "positive",
            "positive_count": 3,
            "negative_count": 0,
            "total_count": 3
        })
        
        context_analyzer.analyze_framing = Mock(return_value={
            "category": "leadership",
            "scores": {"leadership": 1.0},
            "counts": {"leadership": 3},
            "total_count": 3
        })
        
        # Analyze context
        result = context_analyzer.analyze_context("This text has positive sentiment and leadership framing.")
        
        # Verify results
        assert "sentiment" in result
        assert "framing" in result
        assert "length" in result
        assert "word_count" in result
        
        assert result["sentiment"]["category"] == "positive"
        assert result["framing"]["category"] == "leadership"
        assert result["length"] > 0
        assert result["word_count"] > 0
    
    def test_analyze_entity_contexts(self, context_analyzer):
        """Test analyzing contexts for multiple entities."""
        # Mock analyze_context to return predictable results
        context_analyzer.analyze_context = Mock(return_value={
            "sentiment": {"category": "positive", "score": 0.5},
            "framing": {"category": "leadership"},
            "length": 10,
            "word_count": 2
        })
        
        # Create test entities
        entities = [
            {"text": "John Smith", "type": "PERSON", "context": "John Smith is a good leader."},
            {"text": "Jane Doe", "type": "PERSON", "context": "Jane Doe was praised for her work."}
        ]
        
        # Analyze entity contexts
        result = context_analyzer.analyze_entity_contexts(entities)
        
        # Verify results
        assert len(result) == 2
        assert all("context_analysis" in entity for entity in result)
        assert all(entity["context_analysis"]["sentiment"]["category"] == "positive" for entity in result)
        assert all(entity["context_analysis"]["framing"]["category"] == "leadership" for entity in result)
    
    def test_analyze_entity_contexts_no_context(self, context_analyzer):
        """Test analyzing entities without context field."""
        # Create test entities without context
        entities = [
            {"text": "John Smith", "type": "PERSON"},
            {"text": "Jane Doe", "type": "PERSON"}
        ]
        
        # Analyze entity contexts
        result = context_analyzer.analyze_entity_contexts(entities)
        
        # Verify results
        assert len(result) == 2
        assert all("context_analysis" not in entity for entity in result)
    
    def test_analyze_entity_contexts_mixed(self, context_analyzer):
        """Test analyzing entities with and without context."""
        # Mock analyze_context to return predictable results
        context_analyzer.analyze_context = Mock(return_value={
            "sentiment": {"category": "positive", "score": 0.5},
            "framing": {"category": "leadership"},
            "length": 10,
            "word_count": 2
        })
        
        # Create test entities
        entities = [
            {"text": "John Smith", "type": "PERSON", "context": "John Smith is a good leader."},
            {"text": "Jane Doe", "type": "PERSON"}  # No context
        ]
        
        # Analyze entity contexts
        result = context_analyzer.analyze_entity_contexts(entities)
        
        # Verify results
        assert len(result) == 2
        assert "context_analysis" in result[0]
        assert "context_analysis" not in result[1]
    
    def test_get_sentiment_category(self, context_analyzer):
        """Test sentiment category determination from score."""
        # Test positive sentiment
        assert context_analyzer.get_sentiment_category(0.5) == "positive"
        assert context_analyzer.get_sentiment_category(0.21) == "positive"
        
        # Test negative sentiment
        assert context_analyzer.get_sentiment_category(-0.5) == "negative"
        assert context_analyzer.get_sentiment_category(-0.21) == "negative"
        
        # Test neutral sentiment
        assert context_analyzer.get_sentiment_category(0.0) == "neutral"
        assert context_analyzer.get_sentiment_category(0.1) == "neutral"
        assert context_analyzer.get_sentiment_category(-0.1) == "neutral"
        assert context_analyzer.get_sentiment_category(0.2) == "neutral"
        assert context_analyzer.get_sentiment_category(-0.2) == "neutral"
    
    def test_empty_context(self, context_analyzer, mock_spacy_model):
        """Test analysis with empty context."""
        # Setup mock document with no tokens
        mock_doc = MockSpacyDoc(tokens=[])
        mock_spacy_model.return_value = mock_doc
        
        # Analyze empty context
        sentiment_result = context_analyzer.analyze_sentiment("")
        framing_result = context_analyzer.analyze_framing("")
        context_result = context_analyzer.analyze_context("")
        
        # Verify sentiment results
        assert sentiment_result["score"] == 0.0
        assert sentiment_result["category"] == "neutral"
        
        # Verify framing results
        assert framing_result["category"] == "neutral"
        assert framing_result["total_count"] == 0
        
        # Verify context results
        assert context_result["sentiment"]["category"] == "neutral"
        assert context_result["framing"]["category"] == "neutral"
        assert context_result["length"] == 0
        assert context_result["word_count"] == 0
        
    def test_provider_function(self):
        """Test that the provider function creates a properly configured instance."""
        # Import the provider function
        from local_newsifier.di.providers import get_context_analyzer_tool
        
        # Act
        analyzer = get_context_analyzer_tool()
        
        # Assert
        assert isinstance(analyzer, ContextAnalyzer)

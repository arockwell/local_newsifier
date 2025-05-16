"""Tests for SentimentAnalyzer provider functions."""

import pytest
from unittest.mock import patch, MagicMock

# Tests for injectable sentiment analyzer providers

# Import event loop fixture
pytest.importorskip("tests.fixtures.event_loop")
from tests.fixtures.event_loop import event_loop_fixture  # noqa

@pytest.fixture
def mock_nlp():
    """Create a mock spaCy NLP model."""
    return MagicMock()


@patch('fastapi_injectable.decorator.run_coroutine_sync')
def test_get_sentiment_analyzer_config(mock_run_sync, event_loop_fixture):
    """Test the sentiment analyzer configuration provider."""
    # Set up the mock to use our event loop
    mock_run_sync.side_effect = lambda x: event_loop_fixture.run_until_complete(x)
    
    # Import here to avoid circular imports
    from local_newsifier.di.providers import get_sentiment_analyzer_config
    
    # Get configuration from the provider
    config = get_sentiment_analyzer_config()
    
    # Verify it has the expected keys
    assert isinstance(config, dict)
    assert "model_name" in config
    assert config["model_name"] == "en_core_web_sm"

@patch('fastapi_injectable.decorator.run_coroutine_sync')
def test_get_sentiment_analyzer_tool(mock_run_sync, mock_nlp, event_loop_fixture):
    """Test the sentiment analyzer tool provider."""
    # Set up the mock to use our event loop
    mock_run_sync.side_effect = lambda x: event_loop_fixture.run_until_complete(x)
    
    # Import here to avoid circular imports
    from local_newsifier.di.providers import get_sentiment_analyzer_tool
    
    with patch("local_newsifier.di.providers.get_nlp_model", return_value=mock_nlp):
        # Get the sentiment analyzer from the provider
        sentiment_analyzer = get_sentiment_analyzer_tool()
        
        # Verify it has the right attributes
        assert hasattr(sentiment_analyzer, "analyze_sentiment")
        
        # Verify it's using the injected NLP model
        assert sentiment_analyzer.nlp is mock_nlp

# Skip this test to avoid issues with PublicOpinionFlow's crewai imports
@pytest.mark.skip(reason="Skipping public opinion flow test due to crewai dependency")
def test_public_opinion_flow_with_sentiment_analyzer(mock_nlp):
    """Test the public opinion flow provider with sentiment analyzer."""
    pass
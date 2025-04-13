"""Tests for the NER analyzer tool."""

from unittest.mock import Mock, patch

import pytest

from local_newsifier.models.state import AnalysisStatus, NewsAnalysisState
from local_newsifier.tools.ner_analyzer import NERAnalyzerTool


@pytest.fixture
def sample_state():
    """Sample pipeline state for testing."""
    return NewsAnalysisState(
        target_url="https://example.com/news/1",
        scraped_text="John Smith visited Gainesville, Florida yesterday. "
        "He met with representatives from the University of Florida.",
    )


@patch("spacy.load")
def test_ner_analyzer(mock_spacy_load, sample_state):
    """Test NER analysis."""
    # Mock spaCy entities
    mock_doc = Mock()
    mock_ent1 = Mock(
        label_="PERSON",
        text="John Smith",
        sent=Mock(
            text="John Smith visited Gainesville, Florida yesterday.", start_char=0
        ),
        start_char=0,
        end_char=10,
    )
    mock_ent2 = Mock(
        label_="GPE",
        text="Gainesville",
        sent=Mock(
            text="John Smith visited Gainesville, Florida yesterday.", start_char=0
        ),
        start_char=18,
        end_char=28,
    )
    mock_doc.ents = [mock_ent1, mock_ent2]
    mock_nlp = Mock(return_value=mock_doc)
    mock_spacy_load.return_value = mock_nlp

    analyzer = NERAnalyzerTool()
    state = analyzer.analyze(sample_state)

    assert state.status == AnalysisStatus.ANALYSIS_SUCCEEDED
    assert "PERSON" in state.analysis_results["entities"]
    assert "GPE" in state.analysis_results["entities"]
    assert state.analysis_results["entities"]["PERSON"][0]["text"] == "John Smith"
    assert state.analysis_results["entities"]["GPE"][0]["text"] == "Gainesville"

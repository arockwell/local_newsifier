"""Tests for the news analysis pipeline."""

import json
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from bs4 import BeautifulSoup

from local_newsifier.models.state import AnalysisStatus, NewsAnalysisState
from local_newsifier.tools.file_writer import FileWriterTool
from local_newsifier.tools.ner_analyzer import NERAnalyzerTool
from local_newsifier.tools.web_scraper import WebScraperTool


@pytest.fixture
def sample_html():
    """Sample HTML content for testing."""
    return """
    <html>
        <body>
            <article>
                <p>John Smith visited Gainesville, Florida yesterday.</p>
                <p>He met with representatives from the University of Florida.</p>
            </article>
        </body>
    </html>
    """


@pytest.fixture
def sample_state():
    """Sample pipeline state for testing."""
    return NewsAnalysisState(
        target_url="https://example.com/news/1",
        scraped_text="John Smith visited Gainesville, Florida yesterday. "
                    "He met with representatives from the University of Florida."
    )


def test_web_scraper_extract_article(sample_html):
    """Test article text extraction."""
    scraper = WebScraperTool()
    text = scraper.extract_article_text(sample_html)
    
    assert "John Smith" in text
    assert "Gainesville, Florida" in text
    assert "University of Florida" in text


@patch("spacy.load")
def test_ner_analyzer(mock_spacy_load, sample_state):
    """Test NER analysis."""
    # Mock spaCy entities
    mock_doc = Mock()
    mock_ent1 = Mock(
        label_="PERSON",
        text="John Smith",
        sent=Mock(
            text="John Smith visited Gainesville, Florida yesterday.",
            start_char=0
        ),
        start_char=0,
        end_char=10
    )
    mock_ent2 = Mock(
        label_="GPE",
        text="Gainesville",
        sent=Mock(
            text="John Smith visited Gainesville, Florida yesterday.",
            start_char=0
        ),
        start_char=18,
        end_char=28
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


def test_file_writer(tmp_path, sample_state):
    """Test result file writing."""
    writer = FileWriterTool(output_dir=str(tmp_path))
    state = writer.save(sample_state)

    assert state.status == AnalysisStatus.COMPLETED_SUCCESS
    assert state.save_path is not None
    
    # Verify file exists and content
    save_path = Path(state.save_path)
    assert save_path.exists()
    
    with open(save_path) as f:
        data = json.load(f)
        assert data["url"] == sample_state.target_url
        assert data["scraping"]["text_length"] == len(sample_state.scraped_text)


def test_state_management():
    """Test state management functionality."""
    state = NewsAnalysisState(target_url="https://example.com/news/1")
    
    # Test logging
    state.add_log("Test message")
    assert len(state.run_logs) == 1
    assert "Test message" in state.run_logs[0]
    
    # Test error handling
    error = ValueError("Test error")
    state.set_error("test_task", error)
    assert state.error_details.task == "test_task"
    assert state.error_details.type == "ValueError"
    assert state.error_details.message == "Test error"
    
    # Test timestamps
    assert isinstance(state.created_at, datetime)
    assert isinstance(state.last_updated, datetime)
    
    # Test touch
    original_updated = state.last_updated
    state.touch()
    assert state.last_updated > original_updated 
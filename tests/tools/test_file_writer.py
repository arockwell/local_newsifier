"""Tests for the file writer tool."""

import json
from pathlib import Path

import pytest

from local_newsifier.models.state import AnalysisStatus, NewsAnalysisState
from local_newsifier.tools.file_writer import FileWriterTool


@pytest.fixture
def sample_state():
    """Sample pipeline state for testing."""
    return NewsAnalysisState(
        target_url="https://example.com/news/1",
        scraped_text="John Smith visited Gainesville, Florida yesterday. "
                    "He met with representatives from the University of Florida."
    )


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
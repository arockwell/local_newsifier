"""Tests for the file writer tool."""

import json
import os
from pathlib import Path
from unittest.mock import mock_open, patch

import pytest

from local_newsifier.models.state import (AnalysisStatus, ErrorDetails,
                                          NewsAnalysisState)
from local_newsifier.tools.file_writer import FileWriterTool


@pytest.fixture
def sample_state():
    """Sample pipeline state for testing."""
    return NewsAnalysisState(
        target_url="https://example.com/news/1",
        scraped_text="John Smith visited Gainesville, Florida yesterday. "
        "He met with representatives from the University of Florida.",
    )


@pytest.fixture
def error_state(sample_state):
    """Sample state with error details."""
    state = sample_state
    state.error_details = ErrorDetails(
        task="analysis", type="ValueError", message="Failed to analyze content"
    )
    return state


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


def test_file_writer_with_errors(tmp_path, error_state):
    """Test file writing with error details."""
    writer = FileWriterTool(output_dir=str(tmp_path))
    state = writer.save(error_state)

    assert state.status == AnalysisStatus.COMPLETED_WITH_ERRORS
    assert state.save_path is not None

    with open(state.save_path) as f:
        data = json.load(f)
        error = data["metadata"]["error"]
        assert error["task"] == "analysis"
        assert error["type"] == "ValueError"
        assert error["message"] == "Failed to analyze content"


def test_file_writer_permission_error(tmp_path, sample_state):
    """Test file writing with permission error."""
    writer = FileWriterTool(output_dir=str(tmp_path))

    # Mock os.replace to raise PermissionError
    with patch("os.replace", side_effect=PermissionError("Permission denied")):
        with pytest.raises(PermissionError):
            writer.save(sample_state)

        assert sample_state.status == AnalysisStatus.SAVE_FAILED
        assert sample_state.error_details is not None
        assert sample_state.error_details.task == "saving"
        assert "Permission denied" in sample_state.error_details.message


def test_file_writer_json_error(tmp_path, sample_state):
    """Test file writing with JSON serialization error."""
    writer = FileWriterTool(output_dir=str(tmp_path))

    # Create an object that can't be JSON serialized
    sample_state.analysis_results = {"invalid": complex(1, 2)}

    with pytest.raises(TypeError):
        writer.save(sample_state)

    assert sample_state.status == AnalysisStatus.SAVE_FAILED
    assert sample_state.error_details is not None
    assert sample_state.error_details.task == "saving"


def test_file_writer_status_transitions(tmp_path, sample_state):
    """Test status transitions during save operation."""
    writer = FileWriterTool(output_dir=str(tmp_path))

    # Initial status
    assert sample_state.status != AnalysisStatus.SAVING

    state = writer.save(sample_state)

    # Check status transitions
    assert state.status == AnalysisStatus.COMPLETED_SUCCESS
    assert len(state.run_logs) >= 2  # Should have at least start and success logs


def test_generate_filename(tmp_path, sample_state):
    """Test filename generation with different URLs."""
    writer = FileWriterTool(output_dir=str(tmp_path))

    # Test with www subdomain
    sample_state.target_url = "https://www.example.com/news/1"
    state = writer.save(sample_state)
    filename = Path(state.save_path or "").name
    assert "www." not in filename
    assert "example.com" in filename

    # Test with subdomain
    sample_state.target_url = "https://news.example.com/article/1"
    state = writer.save(sample_state)
    filename = Path(state.save_path or "").name
    assert "news.example.com" in filename


def test_ensure_output_dir(tmp_path):
    """Test output directory creation."""
    nested_path = tmp_path / "nested" / "path"
    writer = FileWriterTool(output_dir=str(nested_path))

    # Directory should be created
    assert nested_path.exists()
    assert nested_path.is_dir()

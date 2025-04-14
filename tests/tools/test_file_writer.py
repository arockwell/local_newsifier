"""Tests for the file writer tool."""

import json
import os
from pathlib import Path
from unittest.mock import mock_open, patch, MagicMock

import pytest

from local_newsifier.models.state import (AnalysisStatus, ErrorDetails,
                                          NewsAnalysisState)
from local_newsifier.tools.file_writer import FileWriter, FileWriterTool


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

    # Mock the write_json method to raise PermissionError
    with patch.object(writer.file_writer, "write_json", side_effect=PermissionError("Permission denied")):
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

    # Mock the write_json method to return False (error)
    with patch.object(writer.file_writer, "write_json", return_value=False):
        with pytest.raises(Exception) as exc_info:
            writer.save(sample_state)
        
        assert "Failed to write file" in str(exc_info.value)

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


class TestFileWriter:
    """Tests for the FileWriter class."""

    @pytest.fixture
    def file_writer(self, tmp_path):
        """Create a file writer with a temporary directory."""
        return FileWriter(output_dir=str(tmp_path))

    def test_init(self, file_writer, tmp_path):
        """Test initialization creates the output directory."""
        assert file_writer.output_dir.exists()
        assert file_writer.output_dir.is_dir()

    def test_write_file(self, file_writer, tmp_path):
        """Test writing a file."""
        test_path = tmp_path / "test.txt"
        test_content = "Hello, world!"
        
        # Write the file
        result = file_writer.write_file(str(test_path), test_content)
        
        # Verify the result
        assert result is True
        assert test_path.exists()
        assert test_path.read_text() == test_content

    def test_write_file_with_nonexistent_dir(self, file_writer, tmp_path):
        """Test writing a file to a nonexistent directory."""
        test_path = tmp_path / "subdir" / "test.txt"
        test_content = "Hello, world!"
        
        # Write the file
        result = file_writer.write_file(str(test_path), test_content)
        
        # Verify the result
        assert result is True
        assert test_path.exists()
        assert test_path.read_text() == test_content
        assert test_path.parent.is_dir()

    def test_write_file_with_error(self, file_writer):
        """Test error handling when writing a file."""
        with patch("tempfile.NamedTemporaryFile") as mock_tempfile:
            mock_tempfile.side_effect = Exception("Test exception")
            
            # Attempt to write the file
            result = file_writer.write_file("test.txt", "Test content")
            
            # Verify the result
            assert result is False

    def test_write_json(self, file_writer, tmp_path):
        """Test writing a JSON file."""
        test_path = tmp_path / "test.json"
        test_data = {"key": "value", "list": [1, 2, 3]}
        
        # Write the file
        result = file_writer.write_json(str(test_path), test_data)
        
        # Verify the result
        assert result is True
        assert test_path.exists()
        
        # Verify the content
        loaded_data = json.loads(test_path.read_text())
        assert loaded_data == test_data

    def test_write_json_with_error(self, file_writer):
        """Test error handling when writing a JSON file."""
        with patch.object(file_writer, "write_file") as mock_write_file:
            mock_write_file.return_value = False
            
            # Attempt to write the file
            result = file_writer.write_json("test.json", {"key": "value"})
            
            # Verify the result
            assert result is False

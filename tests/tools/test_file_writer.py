"""Tests for the file writer tool.

This file demonstrates multiple approaches to testing injectable components as recommended
in docs/testing_injectable_dependencies.md:

1. Using event_loop_fixture with @pytest.mark.asyncio (proper event loop handling)
2. Direct instantiation with mocked dependencies (approach i)
3. Using helper functions like create_file_writer_tool (approach ii)
4. Using fixtures for dependency injection (approach iii)
5. Fallback to ci_skip_injectable for tests that still have event loop issues in CI

These approaches ensure that tests run properly both locally and in CI environments.
"""

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest
from tests.ci_skip_config import ci_skip_injectable
from tests.fixtures.event_loop import event_loop_fixture

from local_newsifier.models.state import AnalysisStatus, NewsAnalysisState
from local_newsifier.models.base_state import ErrorDetails
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


@pytest.fixture
def complex_state():
    """Sample state with complex analysis results."""
    state = NewsAnalysisState(
        target_url="https://example.com/news/complex",
        scraped_text="This is a complex article with various data types.",
    )
    state.analysis_results = {
        "entities": [
            {"name": "John Doe", "type": "PERSON"},
            {"name": "Acme Corp", "type": "ORG"}
        ],
        "sentiment": {
            "score": 0.75,
            "magnitude": 0.9,
            "label": "positive"
        },
        "keywords": ["technology", "innovation", "research"],
        "summary": "This is a summary of the article content.",
        "metadata": {
            "word_count": 150,
            "language": "en",
            "processed_at": datetime.now(timezone.utc).isoformat()
        }
    }
    return state


def test_file_writer(tmp_path, sample_state, event_loop_fixture):
    """Test result file writing using event loop fixture."""
    # Direct instantiation with mocked dependencies (approach i)
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


# Helper function to create a FileWriterTool instance for testing (approach ii)
def create_file_writer_tool(output_dir=None):
    """Create a FileWriterTool instance for testing.

    Args:
        output_dir: The output directory to use (optional)

    Returns:
        A FileWriterTool instance
    """
    if output_dir is None:
        output_dir = "output"

    return FileWriterTool(output_dir=output_dir)

def test_file_writer_with_errors(tmp_path, error_state, event_loop_fixture):
    """Test file writing with error details using event loop fixture."""
    # Use helper function to create FileWriterTool (approach ii)
    writer = create_file_writer_tool(output_dir=str(tmp_path))
    state = writer.save(error_state)

    assert state.status == AnalysisStatus.COMPLETED_WITH_ERRORS
    assert state.save_path is not None

    with open(state.save_path) as f:
        data = json.load(f)
        error = data["metadata"]["error"]
        assert error["task"] == "analysis"
        assert error["type"] == "ValueError"
        assert error["message"] == "Failed to analyze content"


# Create a fixture for FileWriterTool (approach iii)
@pytest.fixture
def file_writer_tool(tmp_path):
    """Fixture to create a FileWriterTool instance for testing.

    This fixture provides a ready-to-use FileWriterTool instance
    with a temporary output directory.

    Args:
        tmp_path: pytest's temporary path fixture

    Returns:
        A FileWriterTool instance configured with the temporary path
    """
    return FileWriterTool(output_dir=str(tmp_path))

def test_file_writer_permission_error(tmp_path, sample_state, event_loop_fixture):
    """Test file writing with permission error."""
    # Direct instantiation instead of using the fixture (more reliable in CI)
    writer = FileWriterTool(output_dir=str(tmp_path))

    # Mock os.replace to raise PermissionError
    with patch("os.replace", side_effect=PermissionError("Permission denied")):
        with pytest.raises(PermissionError):
            writer.save(sample_state)

        assert sample_state.status == AnalysisStatus.SAVE_FAILED
        assert sample_state.error_details is not None
        assert sample_state.error_details.task == "saving"
        assert "Permission denied" in sample_state.error_details.message


def test_file_writer_json_error(tmp_path, sample_state, event_loop_fixture):
    """Test file writing with JSON serialization error using event loop fixture."""
    # Direct instantiation with mocked dependencies (approach i)
    writer = FileWriterTool(output_dir=str(tmp_path))

    # Create an object that can't be JSON serialized
    sample_state.analysis_results = {"invalid": complex(1, 2)}

    with pytest.raises(TypeError):
        writer.save(sample_state)

    assert sample_state.status == AnalysisStatus.SAVE_FAILED
    assert sample_state.error_details is not None
    assert sample_state.error_details.task == "saving"


def test_file_writer_status_transitions(tmp_path, sample_state, event_loop_fixture):
    """Test status transitions during save operation using event loop fixture."""
    # Use helper function to create FileWriterTool (approach ii)
    writer = create_file_writer_tool(output_dir=str(tmp_path))

    # Initial status
    assert sample_state.status != AnalysisStatus.SAVING

    state = writer.save(sample_state)

    # Check status transitions
    assert state.status == AnalysisStatus.COMPLETED_SUCCESS
    assert len(state.run_logs) >= 2  # Should have at least start and success logs


@pytest.mark.parametrize(
    "url, expected, check_www",
    [
        ("https://www.example.com/news/1", "example.com", True),
        ("https://news.example.com/article/1", "news.example.com", False),
        ("https://example.com/article", "example.com", False),
        ("http://192.168.1.1/page", "192.168.1.1", False),
        ("http://localhost:8000/test", "localhost", False),
        ("https://example.com/search?q=test&page=1", "example.com", False),
        ("https://example.com/article#section1", "example.com", False),
    ],
    ids=[
        "www_subdomain",
        "subdomain",
        "standard_url",
        "ip_address",
        "localhost",
        "query_params",
        "fragment",
    ],
)
def test_generate_filename(tmp_path, url, expected, check_www, event_loop_fixture):
    """Test filename generation for various URL forms."""
    # Arrange
    writer = FileWriterTool(output_dir=str(tmp_path))
    state = NewsAnalysisState(target_url=url)

    # Act
    filename = writer._generate_filename(state)

    # Assert
    assert expected in filename
    assert str(state.run_id) in filename
    assert filename.endswith(".json")
    if check_www:
        assert "www." not in filename


def test_ensure_output_dir(tmp_path, event_loop_fixture):
    """Test output directory creation using event loop fixture."""
    nested_path = tmp_path / "nested" / "path"
    writer = FileWriterTool(output_dir=str(nested_path))

    # Directory should be created
    assert nested_path.exists()
    assert nested_path.is_dir()


def test_file_writer_with_complex_data(tmp_path, complex_state, event_loop_fixture):
    """Test file writing with complex nested data structures using event loop fixture."""
    # Direct instantiation with mocked dependencies (approach i)
    writer = FileWriterTool(output_dir=str(tmp_path))
    state = writer.save(complex_state)

    assert state.status == AnalysisStatus.COMPLETED_SUCCESS
    assert state.save_path is not None

    # Verify file exists and content
    save_path = Path(state.save_path)
    assert save_path.exists()

    with open(save_path) as f:
        data = json.load(f)
        assert data["url"] == complex_state.target_url
        assert data["analysis"]["results"]["entities"][0]["name"] == "John Doe"
        assert data["analysis"]["results"]["sentiment"]["score"] == 0.75
        assert "technology" in data["analysis"]["results"]["keywords"]


def test_file_writer_atomic_write(tmp_path, event_loop_fixture):
    """Test that file writer performs atomic write operations using event loop fixture."""
    # Create test data and output path
    test_content = {"test": "data", "numbers": [1, 2, 3]}
    output_dir = tmp_path / "output"

    # Use helper function to create FileWriterTool (approach ii)
    writer = create_file_writer_tool(output_dir=str(output_dir))

    # Create state with test content
    state = NewsAnalysisState(
        target_url="https://example.com/atomic-test"
    )
    state.analysis_results = test_content

    # Create a real temporary file for testing
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_file:
        temp_path = temp_file.name

    # Mock json.dump to avoid actual writing
    with patch('json.dump') as mock_dump:
        # Mock os.replace to avoid actual file operations
        with patch('os.replace') as mock_replace:
            # Mock os.fsync to avoid file operations
            with patch('os.fsync') as mock_fsync:
                # Mock tempfile.NamedTemporaryFile to return our controlled file
                with patch('tempfile.NamedTemporaryFile') as mock_temp_file:
                    # Setup the mock to return a file-like object with proper methods
                    mock_file = MagicMock()
                    mock_file.name = temp_path
                    mock_file.fileno.return_value = 123  # Mock file descriptor
                    mock_file.__enter__.return_value = mock_file
                    mock_temp_file.return_value = mock_file

                    # Process write
                    writer.save(state)

                    # Verify temp file was used
                    mock_temp_file.assert_called_once()

                    # Verify json.dump was called
                    mock_dump.assert_called_once()

                    # Verify fsync was called
                    mock_fsync.assert_called_once()

                    # Verify atomic replace was called
                    mock_replace.assert_called_once()
                    assert temp_path in mock_replace.call_args[0]

    # Clean up the temporary file
    if os.path.exists(temp_path):
        os.unlink(temp_path)


def test_file_system_full_error(tmp_path, sample_state, event_loop_fixture):
    """Test handling of file system full error using event loop fixture."""
    # Use fixture through local instantiation (approach iii variant)
    writer = FileWriterTool(output_dir=str(tmp_path))

    # Mock tempfile.NamedTemporaryFile to raise OSError for disk full
    with patch("tempfile.NamedTemporaryFile",
               side_effect=OSError(28, "No space left on device")):
        with pytest.raises(OSError) as exc_info:
            writer.save(sample_state)

        # Verify the error is propagated correctly
        assert "No space left on device" in str(exc_info.value)

        # Verify state is updated correctly
        assert sample_state.status == AnalysisStatus.SAVE_FAILED
        assert sample_state.error_details is not None
        assert sample_state.error_details.task == "saving"
        assert "No space left on device" in sample_state.error_details.message


def test_readonly_filesystem_error(tmp_path, sample_state, event_loop_fixture):
    """Test handling of read-only filesystem errors using event loop fixture."""
    # Direct instantiation with mocked dependencies (approach i)
    writer = FileWriterTool(output_dir=str(tmp_path))

    # Mock os.makedirs to raise a read-only filesystem error
    with patch.object(Path, "mkdir", side_effect=PermissionError("Read-only file system")):
        with pytest.raises(PermissionError) as exc_info:
            # Force directory creation by using a new path
            writer = FileWriterTool(output_dir=str(tmp_path / "new_dir"))
            writer.save(sample_state)

        # Verify the error is propagated
        assert "Read-only file system" in str(exc_info.value)


def test_invalid_path_handling(sample_state, event_loop_fixture):
    """Test handling of invalid paths using event loop fixture."""
    # Try with an invalid path containing illegal characters
    invalid_path = "/\0invalid"  # Null character is invalid in paths

    with pytest.raises(Exception):
        writer = FileWriterTool(output_dir=invalid_path)
        writer.save(sample_state)


def test_prepare_output_format(tmp_path, sample_state, event_loop_fixture):
    """Test the format of prepared output using event loop fixture."""
    # Use helper function to create FileWriterTool (approach ii)
    writer = create_file_writer_tool(output_dir=str(tmp_path))

    # Add some analysis results
    sample_state.analysis_results = {
        "key1": "value1",
        "key2": 123,
        "nested": {"a": 1, "b": 2}
    }

    # Set some timestamps
    now = datetime.now(timezone.utc)
    sample_state.scraped_at = now
    sample_state.analyzed_at = now
    sample_state.status = AnalysisStatus.COMPLETED_SUCCESS

    # Get the prepared output
    output = writer._prepare_output(sample_state)

    # Verify structure
    assert "run_id" in output
    assert "url" in output
    assert "scraping" in output
    assert "analysis" in output
    assert "metadata" in output

    # Verify scraping section
    assert output["scraping"]["timestamp"] == now.isoformat()
    assert output["scraping"]["success"] is True
    assert output["scraping"]["text_length"] == len(sample_state.scraped_text)

    # Verify analysis section
    assert output["analysis"]["timestamp"] == now.isoformat()
    assert output["analysis"]["success"] is True
    assert output["analysis"]["results"] == sample_state.analysis_results

    # Verify metadata
    assert "created_at" in output["metadata"]
    assert "completed_at" in output["metadata"]
    assert "status" in output["metadata"]
    assert output["metadata"]["status"] == AnalysisStatus.COMPLETED_SUCCESS


def test_concurrent_writing(tmp_path, event_loop_fixture):
    """Test concurrent writing scenarios using event loop fixture."""
    import threading
    import time
    from uuid import uuid4

    # Use fixture approach (approach iii variant) with direct instantiation
    writer = FileWriterTool(output_dir=str(tmp_path))
    results = []
    errors = []

    def write_file(index):
        try:
            state = NewsAnalysisState(
                target_url=f"https://example.com/concurrent/{index}"
            )
            state.analysis_results = {"index": index, "data": f"Test data {index}"}
            result_state = writer.save(state)
            results.append(result_state.save_path)
        except Exception as e:
            errors.append(e)

    # Create and start threads
    threads = []
    for i in range(5):
        thread = threading.Thread(target=write_file, args=(i,))
        threads.append(thread)
        thread.start()

    # Wait for all threads to complete
    for thread in threads:
        thread.join()

    # Verify no errors occurred
    assert len(errors) == 0

    # Verify all files were created
    assert len(results) == 5
    for path in results:
        assert os.path.exists(path)

    # Verify each file has the correct content
    for path in results:
        with open(path) as f:
            data = json.load(f)
            index = data["analysis"]["results"]["index"]
            assert data["analysis"]["results"]["data"] == f"Test data {index}"


def test_special_character_handling_in_paths(tmp_path, event_loop_fixture):
    """Test handling of special characters in paths using event loop fixture."""
    # Create a path with spaces and special characters
    special_path = tmp_path / "special dir!@#$" / "sub dir"

    # Use helper function to create FileWriterTool (approach ii)
    writer = create_file_writer_tool(output_dir=str(special_path))

    # Verify directory was created
    assert special_path.exists()

    # Save a file
    state = NewsAnalysisState(
        target_url="https://example.com/special"
    )
    result_state = writer.save(state)

    # Verify file was saved
    assert os.path.exists(result_state.save_path)


@pytest.mark.parametrize(
    "path_factory, expected",
    [
        (lambda tp: "./relative/path", Path("./relative/path")),
        (lambda tp: "../parent/path", Path("../parent/path")),
        (lambda tp: str(tp), lambda tp: tp),
    ],
    ids=["relative", "parent", "absolute"],
)
def test_path_normalization(tmp_path, path_factory, expected, event_loop_fixture):
    """Ensure paths are normalized correctly."""
    # Arrange
    path = path_factory(tmp_path)
    expected_path = expected(tmp_path) if callable(expected) else expected

    with patch("os.makedirs"):
        # Act
        writer = FileWriterTool(output_dir=path)

    # Assert
    assert writer.output_dir == expected_path



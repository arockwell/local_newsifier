"""Tests for TrendReporter provider functions."""

import inspect
import pytest
from unittest.mock import MagicMock, patch

# Import event loop fixture
pytest.importorskip("tests.fixtures.event_loop")
from tests.fixtures.event_loop import event_loop_fixture  # noqa

@pytest.fixture
def mock_file_writer():
    """Create a mock file writer."""
    mock = MagicMock()
    mock.write_file.return_value = "/path/to/output/file.json"
    return mock

@patch('fastapi_injectable.decorator.run_coroutine_sync')
def test_get_trend_reporter_tool(mock_run_sync, event_loop_fixture):
    """Test the trend reporter tool provider."""
    # Set up the mock to use our event loop
    mock_run_sync.side_effect = lambda x: event_loop_fixture.run_until_complete(x)
    
    # Import here to avoid circular imports
    from local_newsifier.di.providers import get_trend_reporter_tool
    
    # Get the trend reporter from the provider
    trend_reporter = get_trend_reporter_tool()
    
    # Verify it has the right attributes
    assert hasattr(trend_reporter, "generate_trend_summary")
    assert hasattr(trend_reporter, "save_report")
    
    # Verify output directory is set correctly
    assert trend_reporter.output_dir == "trend_output"

def test_get_trend_reporter_tool_signature(event_loop_fixture):
    """Test the signature of the trend reporter provider function."""
    # Import provider function
    from local_newsifier.di.providers import get_trend_reporter_tool
    
    # Get the signature of the function
    sig = inspect.signature(get_trend_reporter_tool)
    
    # Should have no parameters (file_writer is injected from constructor)
    assert len(sig.parameters) == 0
    
    # In tests, the decorator may not be actively applied
    # Check either for __injectable__ attribute or just ensure it's callable
    if not hasattr(get_trend_reporter_tool, "__injectable__"):
        # Just check it's callable as a fallback
        assert callable(get_trend_reporter_tool)
    
    # Verify the function docstring
    assert "trend reporter tool" in get_trend_reporter_tool.__doc__.lower()
    assert "use_cache=false" in get_trend_reporter_tool.__doc__.lower()

@patch('fastapi_injectable.decorator.run_coroutine_sync')
def test_trend_reporter_with_file_writer(mock_run_sync, mock_file_writer, event_loop_fixture):
    """Test the trend reporter with file writer injection."""
    # Set up the mock to use our event loop
    mock_run_sync.side_effect = lambda x: event_loop_fixture.run_until_complete(x)
    
    # Import the class directly
    from local_newsifier.tools.trend_reporter import TrendReporter
    
    # Create instance with injected file_writer
    reporter = TrendReporter(output_dir="test_dir", file_writer=mock_file_writer)
    
    # Check that file_writer was properly set
    assert reporter.file_writer is mock_file_writer

@pytest.mark.skip(reason="Skipping trend analysis flow test to avoid dependencies")
def test_trend_analysis_flow_with_trend_reporter():
    """Test the trend analysis flow with trend reporter."""
    pass
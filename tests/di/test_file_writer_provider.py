"""Tests for file writer provider."""

import inspect
import pytest
from tests.fixtures.event_loop import event_loop_fixture

def test_get_file_writer_config(event_loop_fixture):
    """Test that the get_file_writer_config function returns the expected config."""
    # Import here to avoid early execution of injectable decorator
    from local_newsifier.di.providers import get_file_writer_config

    # Get the config
    config = get_file_writer_config()
    
    # Verify it contains the expected keys
    assert "output_dir" in config
    assert config["output_dir"] == "output"

def test_get_file_writer_tool_provider_signature(event_loop_fixture):
    """Test the signature of the file writer tool provider function."""
    # Import provider function
    from local_newsifier.di.providers import get_file_writer_tool
    
    # Get the signature of the function
    sig = inspect.signature(get_file_writer_tool)
    
    # Check that it takes the expected parameters
    assert "config" in sig.parameters
    
    # Check the function docstring
    assert "file writer tool" in get_file_writer_tool.__doc__.lower()
    assert "use_cache=false" in get_file_writer_tool.__doc__.lower()

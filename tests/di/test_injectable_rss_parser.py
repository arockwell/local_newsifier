"""Tests for the injectable version of RSSParser.

This test module checks that the RSSParser works with the fastapi-injectable dependency
injection system. Note that the actual RSSParser functionality is tested in test_rss_parser.py.
"""

import pytest
from unittest.mock import patch
import inspect

from tests.fixtures.event_loop import event_loop_fixture
from tests.ci_skip_config import ci_skip_injectable


@ci_skip_injectable
def test_get_rss_parser_config(event_loop_fixture):
    """Test that the get_rss_parser_config function returns the expected config."""
    # Import provider function
    from local_newsifier.di.providers import get_rss_parser_config

    # Get the config
    config = get_rss_parser_config()

    # Verify it contains the expected keys
    assert "cache_dir" in config
    assert "request_timeout" in config
    assert "user_agent" in config
    assert config["cache_dir"] == "cache"
    assert config["request_timeout"] == 30
    assert "Local Newsifier" in config["user_agent"]


@ci_skip_injectable
def test_get_rss_parser_provider_signature(event_loop_fixture):
    """Test the signature of the RSS parser provider function."""
    # Import provider function
    from local_newsifier.di.providers import get_rss_parser

    # Check the function docstring
    assert "rss parser tool" in get_rss_parser.__doc__.lower()
    assert "use_cache=false" in get_rss_parser.__doc__.lower()


@ci_skip_injectable
def test_rss_parser_class_can_be_instantiated(event_loop_fixture):
    """Test that RSSParser class can be instantiated with expected parameters."""
    # Import directly in test function to avoid global import issues
    from local_newsifier.tools.rss_parser import RSSParser

    # Don't rely on injectable behavior - create directly using class constructor
    parser = RSSParser(
        cache_dir="test_cache",
        request_timeout=60,
        user_agent="Test User Agent"
    )

    assert parser.request_timeout == 60
    assert parser.user_agent == "Test User Agent"

    # Verify methods exist
    assert callable(parser.parse_feed)
    assert callable(parser.get_new_urls)


@ci_skip_injectable
def test_rss_parser_provider_returns_config(event_loop_fixture):
    """Test that the get_rss_parser_config provider returns the expected configuration."""
    # Import provider function
    from local_newsifier.di.providers import get_rss_parser_config

    # Get the config
    config = get_rss_parser_config()

    # Check expected config values
    assert config["cache_dir"] == "cache"
    assert config["request_timeout"] == 30
    assert "Local Newsifier" in config["user_agent"]
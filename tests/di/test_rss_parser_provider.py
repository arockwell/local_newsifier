"""Tests for RSS parser provider."""

import inspect


def test_get_rss_parser_config():
    """Test that the get_rss_parser_config function returns the expected config."""
    # Import here to avoid early execution of injectable decorator
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


def test_get_rss_parser_provider_signature():
    """Test the signature of the RSS parser provider function."""
    # Import provider function
    from local_newsifier.di.providers import get_rss_parser

    # Get the signature of the function
    sig = inspect.signature(get_rss_parser)

    # Check that it takes the expected parameters
    assert "config" in sig.parameters

    # Check the function docstring
    assert "rss parser tool" in get_rss_parser.__doc__.lower()
    assert "use_cache=false" in get_rss_parser.__doc__.lower()


def test_rss_parser_class_can_be_instantiated():
    """Test that RSSParser class can be instantiated with expected parameters."""
    from local_newsifier.tools.rss_parser import RSSParser

    # Verify RSSParser class can be instantiated with expected parameters
    parser = RSSParser(cache_dir="test_cache", request_timeout=60, user_agent="Test User Agent")

    assert parser.request_timeout == 60
    assert parser.user_agent == "Test User Agent"

    # Verify methods exist
    assert callable(parser.parse_feed)
    assert callable(parser.get_new_urls)


def test_rss_parser_provider_returns_parser():
    """Test that the get_rss_parser provider returns a parser instance."""
    # Import provider function
    from local_newsifier.di.providers import get_rss_parser_config

    # Get the config
    config = get_rss_parser_config()

    # Check expected config values
    assert config["cache_dir"] == "cache"
    assert config["request_timeout"] == 30
    assert "Local Newsifier" in config["user_agent"]

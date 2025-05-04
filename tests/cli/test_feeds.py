"""
Tests for improved RSS feeds CLI commands using proper dependency injection.

These tests directly test the FeedsCommands class with mocked dependencies.
"""

import json
import pytest
import io
import click
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone
from contextlib import redirect_stdout

# Import our command class to inject test doubles directly
from local_newsifier.cli.commands.feeds import FeedsCommands


@pytest.fixture
def mock_feeds_commands():
    """Create a mock FeedsCommands with test doubles."""
    # Create mock services
    rss_feed_service = MagicMock()
    article_crud = MagicMock()
    news_pipeline_flow = MagicMock()
    entity_tracking_flow = MagicMock()
    session = MagicMock()
    
    # Set up session as context manager
    session.__enter__ = MagicMock(return_value=session)
    session.__exit__ = MagicMock(return_value=None)
    
    # Create a FeedsCommands instance with our test doubles
    feeds_commands = FeedsCommands(
        rss_feed_service=rss_feed_service,
        article_crud=article_crud,
        news_pipeline_flow=news_pipeline_flow,
        entity_tracking_flow=entity_tracking_flow,
        session=session
    )
    
    return feeds_commands


@pytest.fixture
def sample_feed():
    """Return a sample feed for testing."""
    return {
        "id": 1,
        "name": "Test Feed",
        "url": "https://example.com/feed.xml",
        "description": "A test feed",
        "is_active": True,
        "last_fetched_at": datetime.now(timezone.utc).isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


def test_feeds_list(mock_feeds_commands, sample_feed):
    """Test the list_feeds method directly."""
    # Setup mock
    mock_feeds_commands.rss_feed_service.list_feeds.return_value = [sample_feed]
    
    # Capture stdout
    f = io.StringIO()
    with redirect_stdout(f):
        # Call the method directly
        mock_feeds_commands.list_feeds(active_only=False, json_output=False, limit=100, skip=0)
    
    output = f.getvalue()
    
    # Verify output
    assert "Test Feed" in output
    assert "https://example.com/feed.xml" in output
    
    # Verify the mock was called with correct arguments
    mock_feeds_commands.rss_feed_service.list_feeds.assert_called_once_with(
        skip=0, limit=100, active_only=False
    )


def test_feeds_add(mock_feeds_commands, sample_feed):
    """Test the add_feed method directly."""
    # Setup mock
    mock_feeds_commands.rss_feed_service.create_feed.return_value = sample_feed
    
    # Capture stdout
    f = io.StringIO()
    with redirect_stdout(f):
        # Call the method directly
        mock_feeds_commands.add_feed(
            url="https://example.com/feed.xml",
            name="Test Feed",
            description=None
        )
    
    output = f.getvalue()
    
    # Verify output
    assert "Feed added successfully" in output
    assert str(sample_feed["id"]) in output
    
    # Verify the mock was called with correct arguments
    mock_feeds_commands.rss_feed_service.create_feed.assert_called_once_with(
        url="https://example.com/feed.xml",
        name="Test Feed",
        description=None
    )


def test_feeds_show(mock_feeds_commands, sample_feed):
    """Test the show_feed method directly."""
    # Setup mock
    mock_feeds_commands.rss_feed_service.get_feed.return_value = sample_feed
    
    # Capture stdout
    f = io.StringIO()
    with redirect_stdout(f):
        # Call the method directly
        mock_feeds_commands.show_feed(id=1, json_output=False, show_logs=False)
    
    output = f.getvalue()
    
    # Verify output
    assert "Test Feed" in output
    assert "https://example.com/feed.xml" in output
    
    # Verify the mock was called with correct arguments
    mock_feeds_commands.rss_feed_service.get_feed.assert_called_once_with(1)
    # Should not call get_feed_processing_logs when show_logs is False
    mock_feeds_commands.rss_feed_service.get_feed_processing_logs.assert_not_called()


def test_feeds_show_with_logs(mock_feeds_commands, sample_feed):
    """Test the show_feed method with logs."""
    # Setup mocks
    mock_feeds_commands.rss_feed_service.get_feed.return_value = sample_feed
    mock_feeds_commands.rss_feed_service.get_feed_processing_logs.return_value = [
        {
            "id": 1,
            "feed_id": 1,
            "status": "success",
            "articles_found": 10,
            "articles_added": 5,
            "error_message": None,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "completed_at": datetime.now(timezone.utc).isoformat(),
        }
    ]
    
    # Capture stdout
    f = io.StringIO()
    with redirect_stdout(f):
        # Call the method directly
        mock_feeds_commands.show_feed(id=1, json_output=False, show_logs=True)
    
    output = f.getvalue()
    
    # Verify output
    assert "Test Feed" in output
    assert "Recent Processing Logs" in output
    
    # Verify the mock was called with correct arguments
    mock_feeds_commands.rss_feed_service.get_feed.assert_called_once_with(1)
    mock_feeds_commands.rss_feed_service.get_feed_processing_logs.assert_called_once_with(1, limit=5)
"""Tests for the RSS feeds CLI commands."""

import json
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone
from click.testing import CliRunner

from local_newsifier.cli.main import cli


@pytest.fixture
def mock_rss_feed_service():
    """Mock the RSSFeedService for testing."""
    mock_service = MagicMock()
    
    # Patch the provider functions used in the feeds module
    with patch('local_newsifier.cli.commands.feeds.get_rss_feed_service', return_value=mock_service), \
         patch('local_newsifier.cli.commands.feeds.get_article_crud', return_value=MagicMock()), \
         patch('local_newsifier.cli.commands.feeds.get_session', return_value=MagicMock()), \
         patch('local_newsifier.cli.commands.feeds.get_news_pipeline_flow', return_value=MagicMock()), \
         patch('local_newsifier.cli.commands.feeds.get_entity_tracking_flow', return_value=MagicMock()):
        
        yield mock_service


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


def test_feeds_list(mock_rss_feed_service, sample_feed):
    """Test the feeds list command."""
    # Setup mock
    mock_rss_feed_service.list_feeds.return_value = [sample_feed]
    
    # Run command
    runner = CliRunner()
    result = runner.invoke(cli, ["feeds", "list"])
    
    # Verify
    assert result.exit_code == 0
    assert "Test Feed" in result.output
    assert "https://example.com/feed.xml" in result.output
    mock_rss_feed_service.list_feeds.assert_called_once()


def test_feeds_list_json(mock_rss_feed_service, sample_feed):
    """Test the feeds list command with JSON output."""
    # Setup mock
    mock_rss_feed_service.list_feeds.return_value = [sample_feed]
    
    # Run command
    runner = CliRunner()
    result = runner.invoke(cli, ["feeds", "list", "--json"])
    
    # Verify
    assert result.exit_code == 0
    output = json.loads(result.output)
    assert len(output) == 1
    assert output[0]["name"] == "Test Feed"
    assert output[0]["url"] == "https://example.com/feed.xml"


def test_feeds_add(mock_rss_feed_service, sample_feed):
    """Test the feeds add command."""
    # Setup mock
    mock_rss_feed_service.create_feed.return_value = sample_feed
    
    # Run command
    runner = CliRunner()
    result = runner.invoke(cli, ["feeds", "add", "https://example.com/feed.xml", "--name", "Test Feed"])
    
    # Verify
    assert result.exit_code == 0
    assert "Feed added successfully" in result.output
    mock_rss_feed_service.create_feed.assert_called_once_with(
        url="https://example.com/feed.xml",
        name="Test Feed",
        description=None
    )


def test_feeds_add_error(mock_rss_feed_service):
    """Test the feeds add command with an error."""
    # Setup mock
    from local_newsifier.errors.rss_error import RSSError
    mock_rss_feed_service.create_feed.side_effect = RSSError("Feed already exists")
    
    # Run command
    runner = CliRunner()
    result = runner.invoke(cli, ["feeds", "add", "https://example.com/feed.xml"])
    
    # Verify
    assert result.exit_code == 1  # Now exits with an error code
    assert "Error" in result.output
    assert "Feed already exists" in result.output


def test_feeds_show(mock_rss_feed_service, sample_feed):
    """Test the feeds show command."""
    # Setup mock
    mock_rss_feed_service.get_feed.return_value = sample_feed
    mock_rss_feed_service.get_feed_processing_logs.return_value = []
    
    # Run command
    runner = CliRunner()
    result = runner.invoke(cli, ["feeds", "show", "1"])
    
    # Verify
    assert result.exit_code == 0
    assert "Test Feed" in result.output
    assert "https://example.com/feed.xml" in result.output
    mock_rss_feed_service.get_feed.assert_called_once_with(1)


def test_feeds_show_with_logs(mock_rss_feed_service, sample_feed):
    """Test the feeds show command with logs."""
    # Setup mock
    mock_rss_feed_service.get_feed.return_value = sample_feed
    mock_rss_feed_service.get_feed_processing_logs.return_value = [
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
    
    # Run command
    runner = CliRunner()
    result = runner.invoke(cli, ["feeds", "show", "1", "--show-logs"])
    
    # Verify
    assert result.exit_code == 0
    assert "Test Feed" in result.output
    assert "Recent Processing Logs" in result.output
    assert "success" in result.output
    mock_rss_feed_service.get_feed.assert_called_once_with(1)
    mock_rss_feed_service.get_feed_processing_logs.assert_called_once_with(1, limit=5)


def test_feeds_show_not_found(mock_rss_feed_service):
    """Test the feeds show command with a non-existent feed."""
    # Setup mock
    from local_newsifier.errors.rss_error import RSSError
    mock_rss_feed_service.get_feed.return_value = None
    
    # Run command
    runner = CliRunner()
    result = runner.invoke(cli, ["feeds", "show", "999"])
    
    # Verify
    assert result.exit_code == 1  # CLI exits with error code when feed not found
    assert "Error" in result.output
    assert "not found" in result.output
    mock_rss_feed_service.get_feed.assert_called_once_with(999)


def test_feeds_remove(mock_rss_feed_service, sample_feed):
    """Test the feeds remove command with confirmation."""
    # Setup mock
    mock_rss_feed_service.get_feed.return_value = sample_feed
    mock_rss_feed_service.remove_feed.return_value = sample_feed
    
    # Run command (with --force to skip confirmation)
    runner = CliRunner()
    result = runner.invoke(cli, ["feeds", "remove", "1", "--force"])
    
    # Verify
    assert result.exit_code == 0
    assert "removed successfully" in result.output
    mock_rss_feed_service.get_feed.assert_called_once_with(1)
    mock_rss_feed_service.remove_feed.assert_called_once_with(1)


def test_feeds_update(mock_rss_feed_service, sample_feed):
    """Test the feeds update command."""
    # Setup mock
    mock_rss_feed_service.get_feed.return_value = sample_feed
    updated_feed = sample_feed.copy()
    updated_feed["name"] = "Updated Feed"
    mock_rss_feed_service.update_feed.return_value = updated_feed
    
    # Run command
    runner = CliRunner()
    result = runner.invoke(cli, ["feeds", "update", "1", "--name", "Updated Feed"])
    
    # Verify
    assert result.exit_code == 0
    assert "updated successfully" in result.output
    mock_rss_feed_service.get_feed.assert_called_once_with(1)
    
    # Check call arguments but allow is_active parameter
    call_args = mock_rss_feed_service.update_feed.call_args
    assert call_args[0][0] == 1  # First positional arg should be feed_id
    assert call_args[1].get("name") == "Updated Feed"  # Should have name in kwargs


def test_feeds_process(mock_rss_feed_service, sample_feed):
    """Test the feeds process command."""
    # Setup mock
    mock_rss_feed_service.get_feed.return_value = sample_feed
    mock_rss_feed_service.process_feed.return_value = {
        "feed_id": 1,
        "feed_name": "Test Feed",
        "articles_found": 10,
        "articles_added": 5,
    }
    
    # Run command
    runner = CliRunner()
    result = runner.invoke(cli, ["feeds", "process", "1"])
    
    # Verify
    assert result.exit_code == 0
    assert "Processing completed successfully" in result.output
    assert "Articles found: 10" in result.output
    assert "Articles added: 5" in result.output
    mock_rss_feed_service.get_feed.assert_called_once_with(1)
    
    # Check call arguments but allow task_queue_func parameter
    call_args = mock_rss_feed_service.process_feed.call_args
    assert call_args[0][0] == 1  # First positional arg should be feed_id
    # We don't verify the task_queue_func parameter specifically as it's an implementation detail


def test_feeds_fetch(mock_rss_feed_service, sample_feed):
    """Test the feeds fetch command."""
    # Setup mock
    mock_rss_feed_service.list_feeds.return_value = [sample_feed, sample_feed.copy()]
    mock_rss_feed_service.process_feed.return_value = {
        "feed_id": 1,
        "feed_name": "Test Feed",
        "articles_found": 5,
        "articles_added": 3,
    }
    
    # Run command
    runner = CliRunner()
    result = runner.invoke(cli, ["feeds", "fetch"])
    
    # Verify
    assert result.exit_code == 0
    assert "Processed 2 feeds: 2 successful, 0 failed" in result.output
    assert "All feeds processed successfully" in result.output
    mock_rss_feed_service.list_feeds.assert_called_once_with(active_only=True)
    assert mock_rss_feed_service.process_feed.call_count == 2


def test_feeds_fetch_with_errors(mock_rss_feed_service, sample_feed):
    """Test the feeds fetch command with a failing feed."""
    # Setup mocks
    from local_newsifier.errors.rss_error import RSSError
    
    feed1 = sample_feed
    feed2 = sample_feed.copy()
    feed2["id"] = 2
    feed2["name"] = "Test Feed 2"
    
    mock_rss_feed_service.list_feeds.return_value = [feed1, feed2]
    
    # Make the first feed succeed and the second fail with RSSError
    def process_feed_side_effect(feed_id, task_queue_func=None):
        if feed_id == 1:
            return {
                "feed_id": 1,
                "feed_name": "Test Feed",
                "articles_found": 5,
                "articles_added": 3,
            }
        else:
            raise RSSError("Failed to fetch")
    
    mock_rss_feed_service.process_feed.side_effect = process_feed_side_effect
    
    # Run command
    runner = CliRunner()
    result = runner.invoke(cli, ["feeds", "fetch"])
    
    # Verify
    assert result.exit_code == 0
    assert "Processed 2 feeds: 1 successful, 1 failed" in result.output
    assert "Partially successful" in result.output
    mock_rss_feed_service.list_feeds.assert_called_once_with(active_only=True)
    assert mock_rss_feed_service.process_feed.call_count == 2

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
    
    # We patch the container.get method in the feeds module
    with patch('local_newsifier.cli.commands.feeds.container') as mock_container:
        # Setup mock container to return our mock service for "rss_feed_service"
        def mock_get(service_name):
            if service_name == "rss_feed_service":
                return mock_service
            elif service_name == "article_crud":
                return MagicMock()
            elif service_name == "session_factory":
                return MagicMock()
            return None
            
        mock_container.get.side_effect = mock_get
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
    mock_rss_feed_service.create_feed.side_effect = ValueError("Feed already exists")
    
    # Run command
    runner = CliRunner()
    result = runner.invoke(cli, ["feeds", "add", "https://example.com/feed.xml"])
    
    # Verify - exits with error code 1 because of the @handle_rss_cli_errors decorator
    assert result.exit_code == 1
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
    mock_rss_feed_service.get_feed.return_value = None
    
    # Run command
    runner = CliRunner()
    result = runner.invoke(cli, ["feeds", "show", "999"])
    
    # Verify - The show command doesn't use @handle_rss_cli_errors so it doesn't exit with code 1
    assert result.exit_code == 0
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
        "status": "success",
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
        "status": "success",
        "feed_id": 1,
        "feed_name": "Test Feed",
        "articles_found": 10,
        "articles_added": 5,
    }
    
    # Run command
    runner = CliRunner()
    result = runner.invoke(cli, ["feeds", "fetch"])
    
    # Verify
    assert result.exit_code == 0
    assert "Processing 2 feeds" in result.output
    assert "Feeds processed: 2" in result.output
    assert "Total articles found: 20" in result.output
    assert "Total articles added: 10" in result.output
    mock_rss_feed_service.list_feeds.assert_called_once()
    assert mock_rss_feed_service.process_feed.call_count == 2


def test_feeds_fetch_with_error(mock_rss_feed_service, sample_feed):
    """Test the feeds fetch command with an error."""
    # Setup two feeds, first one will fail
    feed1 = sample_feed.copy()
    feed1["id"] = 1
    feed1["name"] = "Failed Feed"
    
    feed2 = sample_feed.copy()
    feed2["id"] = 2
    feed2["name"] = "Successful Feed"
    
    mock_rss_feed_service.list_feeds.return_value = [feed1, feed2]
    
    # Make the first feed fail, second succeed
    def process_feed_side_effect(feed_id, **kwargs):
        if feed_id == 1:
            from local_newsifier.errors.rss_error import RSSError
            raise RSSError("Feed processing failed")
        return {
            "status": "success",
            "feed_id": feed_id,
            "feed_name": "Successful Feed",
            "articles_found": 10,
            "articles_added": 5,
        }
    
    mock_rss_feed_service.process_feed.side_effect = process_feed_side_effect
    
    # Run command
    runner = CliRunner()
    result = runner.invoke(cli, ["feeds", "fetch"])
    
    # Verify
    assert result.exit_code == 0
    assert "Error processing feed 'Failed Feed'" in result.output
    assert "Feeds processed: 1" in result.output
    assert "Feeds failed: 1" in result.output
    assert "Total articles found: 10" in result.output
    assert "Total articles added: 5" in result.output
    mock_rss_feed_service.list_feeds.assert_called_once()
    assert mock_rss_feed_service.process_feed.call_count == 2


def test_feeds_fetch_no_feeds(mock_rss_feed_service):
    """Test the feeds fetch command with no feeds."""
    # Setup mock
    mock_rss_feed_service.list_feeds.return_value = []
    
    # Run command
    runner = CliRunner()
    result = runner.invoke(cli, ["feeds", "fetch"])
    
    # Verify
    assert result.exit_code == 0
    assert "No feeds found to process" in result.output
    mock_rss_feed_service.list_feeds.assert_called_once()
    mock_rss_feed_service.process_feed.assert_not_called()

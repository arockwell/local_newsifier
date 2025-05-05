"""Tests for RSS feeds CLI commands using injectable provider functions."""

import json
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone
from click.testing import CliRunner

from local_newsifier.cli.main import cli


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


def test_feeds_list_with_injectable(sample_feed):
    """Test the feeds list command using mocked injectable providers."""
    # Create mock service
    mock_rss_service = MagicMock()
    mock_rss_service.list_feeds.return_value = [sample_feed]
    
    # Patch the provider function
    with patch('local_newsifier.cli.commands.feeds.get_rss_feed_service', return_value=mock_rss_service):
        # Run command
        runner = CliRunner()
        result = runner.invoke(cli, ["feeds", "list"])
        
        # Verify
        assert result.exit_code == 0
        assert "Test Feed" in result.output
        assert "https://example.com/feed.xml" in result.output
        
        # Verify the mock was called correctly
        mock_rss_service.list_feeds.assert_called_once()


def test_feeds_add_with_injectable(sample_feed):
    """Test the feeds add command using mocked injectable providers."""
    # Create mock service
    mock_rss_service = MagicMock()
    mock_rss_service.create_feed.return_value = sample_feed
    
    # Patch the provider function
    with patch('local_newsifier.cli.commands.feeds.get_rss_feed_service', return_value=mock_rss_service):
        # Run command
        runner = CliRunner()
        result = runner.invoke(cli, ["feeds", "add", "https://example.com/feed.xml", "--name", "Test Feed"])
        
        # Verify
        assert result.exit_code == 0
        assert "Feed added successfully" in result.output
        
        # Verify the mock was called correctly
        mock_rss_service.create_feed.assert_called_once_with(
            url="https://example.com/feed.xml",
            name="Test Feed",
            description=None
        )


def test_feeds_process_with_injectable(sample_feed):
    """Test the feeds process command using mocked injectable providers."""
    # Create mock services
    mock_rss_service = MagicMock()
    mock_rss_service.get_feed.return_value = sample_feed
    mock_rss_service.process_feed.return_value = {
        "status": "success", 
        "feed_id": 1,
        "feed_name": "Test Feed",
        "articles_found": 10,
        "articles_added": 5
    }
    
    # Mock article and needed flows
    article = MagicMock()
    article.id = 1
    article.title = "Test Article"
    article.url = "https://example.com/article.html"
    
    mock_article_crud = MagicMock()
    mock_article_crud.get.return_value = article
    
    mock_news_flow = MagicMock()
    mock_entity_flow = MagicMock()
    mock_entity_flow.process_article.return_value = ["Entity1", "Entity2"]
    
    # Create all patches
    with patch('local_newsifier.cli.commands.feeds.get_rss_feed_service', return_value=mock_rss_service), \
         patch('local_newsifier.cli.commands.feeds.get_article_crud', return_value=mock_article_crud), \
         patch('local_newsifier.cli.commands.feeds.get_news_pipeline_flow', return_value=mock_news_flow), \
         patch('local_newsifier.cli.commands.feeds.get_entity_tracking_flow', return_value=mock_entity_flow), \
         patch('local_newsifier.cli.commands.feeds.get_session'):
        
        # Run command
        runner = CliRunner()
        result = runner.invoke(cli, ["feeds", "process", "1"])
        
        # Verify
        assert result.exit_code == 0
        assert "Processing completed successfully" in result.output
        assert "Articles found: 10" in result.output
        assert "Articles added: 5" in result.output
        
        # Verify the feed was retrieved and processed
        mock_rss_service.get_feed.assert_called_once_with(1)
        mock_rss_service.process_feed.assert_called_once()


def test_feeds_fetch_with_injectable(sample_feed):
    """Test the fetch command with injected dependencies."""
    # Create mock services
    mock_rss_service = MagicMock()
    
    # Set up returns for list_feeds
    feed1 = sample_feed
    feed2 = sample_feed.copy()
    feed2["id"] = 2
    feed2["name"] = "Test Feed 2"
    mock_rss_service.list_feeds.return_value = [feed1, feed2]
    
    # Set up returns for process_feed
    mock_rss_service.process_feed.return_value = {
        "status": "success",
        "feed_id": 1,
        "feed_name": "Test Feed",
        "articles_found": 5,
        "articles_added": 3,
    }
    
    # Create all patches
    with patch('local_newsifier.cli.commands.feeds.get_rss_feed_service', return_value=mock_rss_service), \
         patch('local_newsifier.cli.commands.feeds.get_article_crud', return_value=MagicMock()), \
         patch('local_newsifier.cli.commands.feeds.get_news_pipeline_flow', return_value=MagicMock()), \
         patch('local_newsifier.cli.commands.feeds.get_entity_tracking_flow', return_value=MagicMock()), \
         patch('local_newsifier.cli.commands.feeds.get_session'):
        
        # Run command
        runner = CliRunner()
        result = runner.invoke(cli, ["feeds", "fetch"])
        
        # Verify
        assert result.exit_code == 0
        assert "Processed 2 feeds: 2 successful, 0 failed" in result.output
        assert "All feeds processed successfully" in result.output
        
        # Verify service calls
        mock_rss_service.list_feeds.assert_called_once_with(active_only=True)
        assert mock_rss_service.process_feed.call_count == 2


def test_feeds_fetch_error_with_injectable(sample_feed):
    """Test the fetch command with failure cases."""
    # Create mock services
    mock_rss_service = MagicMock()
    
    # Set up returns for list_feeds
    feed1 = sample_feed
    feed2 = sample_feed.copy()
    feed2["id"] = 2
    feed2["name"] = "Test Feed 2"
    mock_rss_service.list_feeds.return_value = [feed1, feed2]
    
    # Make all feeds fail
    def process_feed_side_effect(feed_id, task_queue_func=None):
        return {
            "status": "error",
            "feed_id": feed_id,
            "feed_name": f"Test Feed {feed_id}",
            "message": "Failed to fetch feed",
            "articles_found": 0,
            "articles_added": 0,
        }
    
    mock_rss_service.process_feed.side_effect = process_feed_side_effect
    
    # Create all patches
    with patch('local_newsifier.cli.commands.feeds.get_rss_feed_service', return_value=mock_rss_service), \
         patch('local_newsifier.cli.commands.feeds.get_article_crud', return_value=MagicMock()), \
         patch('local_newsifier.cli.commands.feeds.get_news_pipeline_flow', return_value=MagicMock()), \
         patch('local_newsifier.cli.commands.feeds.get_entity_tracking_flow', return_value=MagicMock()), \
         patch('local_newsifier.cli.commands.feeds.get_session'):
        
        # Run command
        runner = CliRunner()
        result = runner.invoke(cli, ["feeds", "fetch"])
        
        # Since the mock is returning the same error for ALL feeds,
        # we should check that the output indicates all feeds failed, but in this test
        # we need to examine the output rather than exit code because we're not capturing
        # the uncaught exception properly in the click test runner
        assert "Processed 2 feeds: 0 successful, 2 failed" in result.output
        
        # Verify service calls
        mock_rss_service.list_feeds.assert_called_once_with(active_only=True)
        assert mock_rss_service.process_feed.call_count == 2
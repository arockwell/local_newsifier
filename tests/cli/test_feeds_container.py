"""Tests for RSS feeds CLI commands using injectable provider functions."""

import json
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone
from click.testing import CliRunner

from local_newsifier.cli.main import cli

# Create a sample feed for testing
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

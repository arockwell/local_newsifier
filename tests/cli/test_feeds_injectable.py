"""Tests for RSS feeds CLI commands using injectable dependency injection."""

import json
import pytest
from unittest.mock import MagicMock
from datetime import datetime, timezone
from click.testing import CliRunner

from local_newsifier.cli.main import cli
# Import the patched_injectable fixture
from tests.utils.conftest import patched_injectable

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


def test_feeds_list_with_injectable(patched_injectable, sample_feed):
    """Test the feeds list command using injectable dependency injection."""
    # Set up the mock service
    rss_service = patched_injectable["rss_feed_service"]
    rss_service.list_feeds.return_value = [sample_feed]
    
    # Run command
    runner = CliRunner()
    result = runner.invoke(cli, ["feeds", "list"])
    
    # Verify
    assert result.exit_code == 0
    assert "Test Feed" in result.output
    assert "https://example.com/feed.xml" in result.output
    
    # Verify the mock was called correctly
    rss_service.list_feeds.assert_called_once()


def test_feeds_add_with_injectable(patched_injectable, sample_feed):
    """Test the feeds add command using injectable dependency injection."""
    # Set up the mock service
    rss_service = patched_injectable["rss_feed_service"]
    rss_service.create_feed.return_value = sample_feed
    
    # Run command
    runner = CliRunner()
    result = runner.invoke(cli, ["feeds", "add", "https://example.com/feed.xml", "--name", "Test Feed"])
    
    # Verify
    assert result.exit_code == 0
    assert "Feed added successfully" in result.output
    
    # Verify the mock was called correctly
    rss_service.create_feed.assert_called_once_with(
        url="https://example.com/feed.xml",
        name="Test Feed",
        description=None
    )


def test_feeds_process_with_injectable(patched_injectable, sample_feed):
    """Test the feeds process command using injectable dependency injection."""
    # Set up mock services
    rss_service = patched_injectable["rss_feed_service"]
    article_crud = patched_injectable["article_crud"]
    news_flow = patched_injectable["news_pipeline_flow"]
    entity_flow = patched_injectable["entity_tracking_flow"]
    
    # Configure mocks
    rss_service.get_feed.return_value = sample_feed
    rss_service.process_feed.return_value = {
        "status": "success",
        "feed_id": 1,
        "feed_name": "Test Feed",
        "articles_found": 10,
        "articles_added": 5
    }
    
    # Mock article
    article = MagicMock()
    article.id = 1
    article.title = "Test Article"
    article.url = "https://example.com/article.html"
    
    article_crud.get.return_value = article
    entity_flow.process_article.return_value = ["Entity1", "Entity2"]
    
    # Run command
    runner = CliRunner()
    result = runner.invoke(cli, ["feeds", "process", "1"])
    
    # Verify
    assert result.exit_code == 0
    assert "Processing completed successfully" in result.output
    assert "Articles found: 10" in result.output
    assert "Articles added: 5" in result.output
    
    # Verify the feed was retrieved and processed
    rss_service.get_feed.assert_called_once_with(1)
    rss_service.process_feed.assert_called_once()
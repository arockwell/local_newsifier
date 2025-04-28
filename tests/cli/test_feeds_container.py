"""Tests for RSS feeds CLI commands using DI container."""

import json
import pytest
from unittest.mock import MagicMock
from datetime import datetime, timezone
from click.testing import CliRunner

from local_newsifier.cli.main import cli
from tests.utils.test_container import mock_service
# Import fixtures directly
from tests.utils.conftest import test_container, mock_session, patched_container

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


def test_feeds_list_with_container(patched_container, sample_feed):
    """Test the feeds list command using the patched container."""
    # Setup mock service with specific return value
    mock_service(patched_container, "rss_feed_service", 
                list_feeds=[sample_feed])
    
    # Run command
    runner = CliRunner()
    result = runner.invoke(cli, ["feeds", "list"])
    
    # Verify
    assert result.exit_code == 0
    assert "Test Feed" in result.output
    assert "https://example.com/feed.xml" in result.output
    
    # Verify the mock was called correctly
    rss_service = patched_container.get("rss_feed_service")
    rss_service.list_feeds.assert_called_once()


def test_feeds_add_with_container(patched_container, sample_feed):
    """Test the feeds add command using the patched container."""
    # Setup mock
    mock_service(patched_container, "rss_feed_service", 
                create_feed=sample_feed)
    
    # Run command
    runner = CliRunner()
    result = runner.invoke(cli, ["feeds", "add", "https://example.com/feed.xml", "--name", "Test Feed"])
    
    # Verify
    assert result.exit_code == 0
    assert "Feed added successfully" in result.output
    
    # Verify the mock was called correctly
    rss_service = patched_container.get("rss_feed_service")
    rss_service.create_feed.assert_called_once_with(
        url="https://example.com/feed.xml",
        name="Test Feed",
        description=None
    )


def test_feeds_process_with_container(patched_container, sample_feed, mock_session):
    """Test the feeds process command using the patched container and mocked flows."""
    # Setup mocks
    feed_service = mock_service(patched_container, "rss_feed_service", 
                              get_feed=sample_feed,
                              process_feed={
                                  "status": "success", 
                                  "feed_id": 1,
                                  "feed_name": "Test Feed",
                                  "articles_found": 10,
                                  "articles_added": 5
                              })
    
    # Mock article and needed flows
    article = MagicMock()
    article.id = 1
    article.title = "Test Article"
    article.url = "https://example.com/article.html"
    
    article_crud = mock_service(patched_container, "article_crud", 
                              get=article)
    
    news_flow = mock_service(patched_container, "news_pipeline_flow")
    entity_flow = mock_service(patched_container, "entity_tracking_flow", 
                             process_article=["Entity1", "Entity2"])
    
    # Run command
    runner = CliRunner()
    result = runner.invoke(cli, ["feeds", "process", "1"])
    
    # Verify
    assert result.exit_code == 0
    assert "Processing completed successfully" in result.output
    assert "Articles found: 10" in result.output
    assert "Articles added: 5" in result.output
    
    # Verify the feed was retrieved and processed
    feed_service.get_feed.assert_called_once_with(1)
    feed_service.process_feed.assert_called_once()

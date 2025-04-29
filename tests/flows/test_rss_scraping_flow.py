"""
Tests for the RSS scraping flow.
"""

from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

import pytest

from local_newsifier.flows.rss_scraping_flow import RSSScrapingFlow
from local_newsifier.models.state import NewsAnalysisState
from local_newsifier.tools.rss_parser import RSSItem


@pytest.fixture
def mock_rss_parser():
    """Mock RSS parser for tests."""
    parser = Mock()
    parser.parse_feed = Mock(return_value=[
        RSSItem(
            title="Test Article",
            link="https://example.com/article1",
            content="Test content",
            published_at=datetime(2025, 1, 1)
        ),
        RSSItem(
            title="Another Article",
            link="https://example.com/article2",
            content="More content",
            published_at=datetime(2025, 1, 2)
        )
    ])
    return parser


@pytest.fixture
def mock_scraper():
    """Mock web scraper for tests."""
    scraper = Mock()
    scraper.scrape_article = Mock(return_value={
        "content": "Scraped content",
        "title": "Scraped Title",
        "published_at": datetime(2025, 1, 1)
    })
    return scraper


@pytest.fixture
def mock_rss_feed_service():
    """Mock RSS feed service for tests."""
    service = Mock()
    
    # Mock feed
    mock_feed = Mock()
    mock_feed.id = 1
    mock_feed.url = "https://example.com/feed.xml"
    mock_feed.last_processed_at = datetime(2024, 12, 31)
    
    # Mock methods
    service.get_feed = Mock(return_value=mock_feed)
    service.get_active_feeds = Mock(return_value=[mock_feed])
    service.create_feed_processing_log = Mock()
    
    return service


@pytest.fixture
def mock_article_service():
    """Mock article service for tests."""
    service = Mock()
    service.get_article_by_url = Mock(return_value=None)  # No existing articles
    
    # Mock created article
    mock_article = Mock()
    mock_article.id = 123
    service.create_article_from_state = Mock(return_value=mock_article)
    service.update_article_source = Mock()
    
    return service


def test_rss_scraping_flow_init():
    """Test initializing the RSS scraping flow."""
    # Test with default parameters
    flow = RSSScrapingFlow()
    
    # Test with explicit dependencies
    mock_rss_parser = Mock()
    mock_scraper = Mock()
    mock_rss_feed_service = Mock()
    mock_article_service = Mock()
    
    flow = RSSScrapingFlow(
        rss_parser=mock_rss_parser,
        scraper=mock_scraper,
        rss_feed_service=mock_rss_feed_service,
        article_service=mock_article_service
    )
    
    assert flow.rss_parser is mock_rss_parser
    assert flow.scraper is mock_scraper
    assert flow.rss_feed_service is mock_rss_feed_service
    assert flow.article_service is mock_article_service


def test_process_feed(mock_rss_parser, mock_scraper, mock_rss_feed_service, mock_article_service):
    """Test processing a single RSS feed."""
    # Create mock session
    mock_session = Mock()
    
    # Mock session factory
    def mock_session_factory():
        class MockContextManager:
            def __enter__(self):
                return mock_session
            def __exit__(self, *args):
                pass
        return MockContextManager()
    
    # Create flow with mocked dependencies
    flow = RSSScrapingFlow(
        rss_parser=mock_rss_parser,
        scraper=mock_scraper,
        rss_feed_service=mock_rss_feed_service,
        article_service=mock_article_service,
        session_factory=mock_session_factory
    )
    
    # Process feed
    result = flow.process_feed(1)
    
    # Verify feed was retrieved
    mock_rss_feed_service.get_feed.assert_called_once_with(mock_session, 1)
    
    # Verify feed was parsed
    mock_rss_parser.parse_feed.assert_called_once()
    
    # Verify articles were created
    assert mock_article_service.create_article_from_state.call_count == 2
    
    # Verify processing log was created
    mock_rss_feed_service.create_feed_processing_log.assert_called_once()
    
    # Verify result format
    assert result["feed_id"] == 1
    assert result["status"] == "success"
    assert result["items_processed"] > 0
    assert result["items_saved"] > 0


def test_process_all_feeds(mock_rss_parser, mock_scraper, mock_rss_feed_service, mock_article_service):
    """Test processing all active RSS feeds."""
    # Create mock session
    mock_session = Mock()
    
    # Mock session factory
    def mock_session_factory():
        class MockContextManager:
            def __enter__(self):
                return mock_session
            def __exit__(self, *args):
                pass
        return MockContextManager()
    
    # Create flow with mocked dependencies
    flow = RSSScrapingFlow(
        rss_parser=mock_rss_parser,
        scraper=mock_scraper,
        rss_feed_service=mock_rss_feed_service,
        article_service=mock_article_service,
        session_factory=mock_session_factory
    )
    
    # Process all feeds
    results = flow.process_all_feeds()
    
    # Verify active feeds were retrieved
    mock_rss_feed_service.get_active_feeds.assert_called_once_with(mock_session)
    
    # Verify feeds were parsed
    mock_rss_parser.parse_feed.assert_called_once()
    
    # Verify articles were created
    assert mock_article_service.create_article_from_state.call_count == 2
    
    # Verify processing log was created
    mock_rss_feed_service.create_feed_processing_log.assert_called_once()
    
    # Verify result format
    assert len(results) == 1
    assert results[0]["feed_id"] == 1
    assert results[0]["status"] == "success"
    assert results[0]["items_processed"] > 0
    assert results[0]["items_saved"] > 0


def test_process_item(mock_rss_parser, mock_scraper, mock_rss_feed_service, mock_article_service):
    """Test processing a single RSS item."""
    # Create mock session
    mock_session = Mock()
    
    # Create flow with mocked dependencies
    flow = RSSScrapingFlow(
        rss_parser=mock_rss_parser,
        scraper=mock_scraper,
        rss_feed_service=mock_rss_feed_service,
        article_service=mock_article_service
    )
    
    # Create an RSS item
    item = RSSItem(
        title="Test Item",
        link="https://example.com/test",
        content="Test content",
        published_at=datetime(2025, 1, 1)
    )
    
    # Create a mock feed
    mock_feed = Mock()
    mock_feed.id = 1
    
    # Process item
    result = flow._process_item(mock_session, mock_feed, item)
    
    # Verify article was checked
    mock_article_service.get_article_by_url.assert_called_once_with(mock_session, item.link)
    
    # Verify article was created
    mock_article_service.create_article_from_state.assert_called_once()
    
    # Verify article source was updated
    mock_article_service.update_article_source.assert_called_once()
    
    # Verify result
    assert result is True


def test_process_item_with_existing_article(mock_rss_parser, mock_scraper, mock_rss_feed_service, mock_article_service):
    """Test processing an item that already exists as an article."""
    # Mock an existing article
    mock_article_service.get_article_by_url.return_value = Mock()
    
    # Create flow with mocked dependencies
    flow = RSSScrapingFlow(
        rss_parser=mock_rss_parser,
        scraper=mock_scraper,
        rss_feed_service=mock_rss_feed_service,
        article_service=mock_article_service
    )
    
    # Create an RSS item
    item = RSSItem(
        title="Test Item",
        link="https://example.com/test",
        content="Test content",
        published_at=datetime(2025, 1, 1)
    )
    
    # Create a mock feed
    mock_feed = Mock()
    mock_feed.id = 1
    
    # Process item
    result = flow._process_item(Mock(), mock_feed, item)
    
    # Verify article was checked
    mock_article_service.get_article_by_url.assert_called_once()
    
    # Verify article was not created
    mock_article_service.create_article_from_state.assert_not_called()
    
    # Verify result
    assert result is False


def test_process_item_without_content(mock_rss_parser, mock_scraper, mock_rss_feed_service, mock_article_service):
    """Test processing an item without content using scraper."""
    # Create flow with mocked dependencies
    flow = RSSScrapingFlow(
        rss_parser=mock_rss_parser,
        scraper=mock_scraper,
        rss_feed_service=mock_rss_feed_service,
        article_service=mock_article_service
    )
    
    # Create an RSS item without content
    item = RSSItem(
        title="Test Item",
        link="https://example.com/test",
        content=None,
        published_at=None
    )
    
    # Create a mock feed
    mock_feed = Mock()
    mock_feed.id = 1
    
    # Process item
    result = flow._process_item(Mock(), mock_feed, item)
    
    # Verify scraper was used
    mock_scraper.scrape_article.assert_called_once_with(item.link)
    
    # Verify article was created
    mock_article_service.create_article_from_state.assert_called_once()
    
    # Verify result
    assert result is True

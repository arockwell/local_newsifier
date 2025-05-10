"""
Tests for the RSS scraping flow.
"""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from local_newsifier.flows.rss_scraping_flow import RSSScrapingFlow
from local_newsifier.models.state import AnalysisStatus, NewsAnalysisState
from local_newsifier.tools.rss_parser import RSSItem
from tests.fixtures.event_loop import event_loop_fixture


@pytest.fixture
def mock_rss_parser(event_loop_fixture):
    """Mock the RSSParser with event loop handling."""
    with patch("local_newsifier.flows.rss_scraping_flow.RSSParser") as mock_class:
        parser_instance = Mock()
        mock_class.return_value = parser_instance
        yield mock_class


@pytest.fixture
def mock_web_scraper(event_loop_fixture):
    """Mock the WebScraperTool with event loop handling."""
    # First, patch the class import itself
    with patch("local_newsifier.flows.rss_scraping_flow.WebScraperTool") as mock_class:
        scraper_instance = Mock()
        mock_class.return_value = scraper_instance
        yield mock_class


@pytest.fixture
def mock_rss_feed_service():
    mock = Mock()
    return mock


@pytest.fixture
def mock_article_service():
    mock = Mock()
    return mock


class TestRSSScrapingFlow:
    def setup_method(self, event_loop_fixture):
        # Create a mock session factory
        mock_session_factory = lambda: Mock()
        # Create with default parameters
        self.flow = RSSScrapingFlow(session_factory=mock_session_factory)

    def test_init_with_cache_dir(self, tmp_path, event_loop_fixture):
        """Test initialization with cache directory."""
        # Create a mock session factory
        mock_session_factory = lambda: Mock()
        # Create flow with cache dir
        flow = RSSScrapingFlow(cache_dir=str(tmp_path), session_factory=mock_session_factory)
        assert flow.cache_dir == tmp_path
        assert flow.rss_feed_service is None
        assert flow.article_service is None
        assert isinstance(flow.rss_parser, Mock) is False
        assert isinstance(flow.web_scraper, Mock) is False

    def test_init_with_dependencies(self, mock_rss_feed_service, mock_article_service,
                                   mock_rss_parser, mock_web_scraper, event_loop_fixture):
        """Test initialization with provided dependencies."""
        parser_instance = Mock()
        scraper_instance = Mock()

        # Create a mock session factory
        mock_session_factory = lambda: Mock()

        # Create flow with all dependencies provided
        flow = RSSScrapingFlow(
            rss_feed_service=mock_rss_feed_service,
            article_service=mock_article_service,
            rss_parser=parser_instance,
            web_scraper=scraper_instance,
            cache_dir="/tmp/cache",
            session_factory=mock_session_factory
        )

        # Verify dependencies were used
        assert flow.rss_feed_service is mock_rss_feed_service
        assert flow.article_service is mock_article_service
        assert flow.rss_parser is parser_instance
        assert flow.web_scraper is scraper_instance
        assert flow.cache_dir == Path("/tmp/cache")

        # Verify RSSParser and WebScraperTool classes were not called
        mock_rss_parser.assert_not_called()
        mock_web_scraper.assert_not_called()

    def test_process_feed_no_new_articles(self, mock_rss_parser, event_loop_fixture):
        """Test processing a feed with no new articles."""
        # Setup mock
        mock_rss_parser.return_value.get_new_urls.return_value = []

        # Test
        # Create a mock session factory
        mock_session_factory = lambda: Mock()

        # Create flow with default parameters
        flow = RSSScrapingFlow(session_factory=mock_session_factory)
        results = flow.process_feed("http://example.com/feed")

        assert len(results) == 0
        mock_rss_parser.return_value.get_new_urls.assert_called_once_with(
            "http://example.com/feed"
        )

    def test_process_feed_with_new_articles(self, mock_rss_parser, mock_web_scraper, event_loop_fixture):
        """Test processing a feed with new articles."""
        # Setup mocks
        test_items = [
            RSSItem(
                title="Test Article 1",
                url="http://example.com/1",
                description="Test description 1",
            ),
            RSSItem(
                title="Test Article 2",
                url="http://example.com/2",
                description="Test description 2",
            ),
        ]
        mock_rss_parser.return_value.get_new_urls.return_value = test_items

        def mock_scrape(state):
            state.status = AnalysisStatus.SCRAPE_SUCCEEDED
            state.scraped_text = f"Scraped content for {state.target_url}"
            return state

        mock_web_scraper.return_value.scrape.side_effect = mock_scrape

        # Test
        # Create a mock session factory
        mock_session_factory = lambda: Mock()

        # Create flow with default parameters
        flow = RSSScrapingFlow(session_factory=mock_session_factory)
        results = flow.process_feed("http://example.com/feed")

        assert len(results) == 2
        assert all(isinstance(state, NewsAnalysisState) for state in results)
        assert all(state.status == AnalysisStatus.SCRAPE_SUCCEEDED for state in results)
        assert "Test Article 1" in results[0].run_logs[0]
        assert "Test Article 2" in results[1].run_logs[0]

    def test_process_feed_with_scraping_error(self, mock_rss_parser, mock_web_scraper, event_loop_fixture):
        """Test processing a feed where scraping fails."""
        # Setup mocks
        test_items = [
            RSSItem(
                title="Test Article",
                url="http://example.com/error",
                description="Test description",
            )
        ]
        mock_rss_parser.return_value.get_new_urls.return_value = test_items
        mock_web_scraper.return_value.scrape.side_effect = Exception("Failed to scrape")

        # Test
        # Create a mock session factory
        mock_session_factory = lambda: Mock()

        # Create flow with default parameters
        flow = RSSScrapingFlow(session_factory=mock_session_factory)
        results = flow.process_feed("http://example.com/feed")

        assert len(results) == 1
        assert results[0].status == AnalysisStatus.SCRAPE_FAILED_NETWORK
        assert results[0].error_details is not None
        assert "Failed to scrape" in str(results[0].error_details.message)
        assert "Failed to process article: Test Article" in results[0].run_logs[-1]

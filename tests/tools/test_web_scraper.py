"""Tests for the web scraper tool."""

import time
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from requests.exceptions import HTTPError, RequestException

from local_newsifier.models.state import AnalysisStatus, NewsAnalysisState
from local_newsifier.tools.web_scraper import WebScraperTool


@pytest.fixture
def mock_state():
    """Create a mock state for testing."""
    return NewsAnalysisState(
        target_url="https://example.com/article", 
        status=AnalysisStatus.INITIALIZED
    )


@pytest.fixture
def web_scraper():
    """Create a WebScraperTool instance for testing."""
    scraper = WebScraperTool(test_mode=True)
    # Replace the _fetch_url method to avoid retry decorator
    scraper._original_fetch = scraper._fetch_url
    scraper._fetch_url = lambda url: scraper._original_fetch.__wrapped__(scraper, url)
    return scraper


class TestWebScraper:
    """Test suite for WebScraperTool."""

    def test_extract_article(self, web_scraper):
        """Test article text extraction."""
        html = """
        <html><body><article>
            <p>John Smith visited Gainesville, Florida yesterday.</p>
            <p>He met with representatives from the University of Florida.</p>
        </article></body></html>
        """
        text = web_scraper.extract_article_text(html)
        assert "John Smith" in text
        assert "Gainesville, Florida" in text
        assert "University of Florida" in text

    def test_extract_article_with_navigation(self, web_scraper):
        """Test article text extraction with navigation elements."""
        html = """
        <html><body>
            <nav>Navigation</nav>
            <article>
                <p>Main content that is long enough to pass the length check.</p>
                <aside>Related content</aside>
                <div class="related-stories">More stories</div>
            </article>
            <footer>Footer</footer>
        </body></html>
        """
        text = web_scraper.extract_article_text(html)
        assert "Main content" in text
        assert "Navigation" not in text
        assert "Related content" not in text
        assert "More stories" not in text
        assert "Footer" not in text

    def test_extract_article_no_content(self, web_scraper):
        """Test article text extraction with no content."""
        with pytest.raises(ValueError, match="No article content found"):
            web_scraper.extract_article_text("<html><body></body></html>")

    def test_extract_article_no_text_blocks(self, web_scraper):
        """Test article text extraction with no valid text blocks."""
        html = """
        <html><body><article>
            <p>Subscribe to our newsletter</p>
            <p>Share this article</p>
        </article></body></html>
        """
        with pytest.raises(ValueError, match="No text content found in article"):
            web_scraper.extract_article_text(html)

    @patch("requests.Session.get")
    def test_fetch_url_success(self, mock_get, web_scraper):
        """Test successful URL fetching."""
        mock_response = MagicMock()
        mock_response.text = "<html><body>Test content</body></html>"
        mock_get.return_value = mock_response

        html = web_scraper._fetch_url("https://example.com")
        assert html == "<html><body>Test content</body></html>"
        mock_get.assert_called_once()

    @patch("requests.Session.get")
    def test_fetch_url_404(self, mock_get, web_scraper):
        """Test URL fetching with 404 error."""
        mock_get.side_effect = HTTPError("404 Not Found", response=MagicMock(status_code=404))
        with pytest.raises(ValueError, match="Article not found"):
            web_scraper._fetch_url("https://example.com/404")

    def test_scrape_success(self, web_scraper, mock_state):
        """Test successful scraping."""
        test_url = "https://example.com/test-article"
        test_html = "<html><body><article><p>Test content</p></article></body></html>"
        test_text = "Test content"
        
        mock_state.target_url = test_url
        
        with patch.object(web_scraper, "_fetch_url") as mock_fetch, \
             patch.object(web_scraper, "extract_article_text") as mock_extract:

            mock_fetch.return_value = test_html
            mock_extract.return_value = test_text

            result_state = web_scraper.scrape(mock_state)

            mock_fetch.assert_called_once_with(test_url)
            mock_extract.assert_called_once_with(test_html)
            
            assert result_state.status == AnalysisStatus.SCRAPE_SUCCEEDED
            assert result_state.scraped_text == test_text
            assert result_state.scraped_at is not None
            assert len(result_state.run_logs) > 0

    def test_scrape_network_error(self, web_scraper, mock_state):
        """Test scraping with network error."""
        with patch.object(web_scraper, "_fetch_url") as mock_fetch:
            mock_fetch.side_effect = RequestException("Network error")
            with pytest.raises(RequestException):
                web_scraper.scrape(mock_state)
            assert mock_state.status == AnalysisStatus.SCRAPE_FAILED_NETWORK
            assert mock_state.error_details is not None
            assert len(mock_state.run_logs) > 0

    def test_scrape_parsing_error(self, web_scraper, mock_state):
        """Test scraping with parsing error."""
        with patch.object(web_scraper, "_fetch_url") as mock_fetch:
            mock_fetch.side_effect = ValueError("Parsing error")
            with pytest.raises(ValueError):
                web_scraper.scrape(mock_state)
            assert mock_state.status == AnalysisStatus.SCRAPE_FAILED_PARSING
            assert mock_state.error_details is not None
            assert len(mock_state.run_logs) > 0

    @patch("selenium.webdriver.chrome.webdriver.WebDriver")
    @patch("selenium.webdriver.chrome.service.Service")
    @patch("webdriver_manager.chrome.ChromeDriverManager")
    def test_selenium_fallback(self, mock_manager, mock_service, mock_webdriver, web_scraper):
        """Test Selenium fallback for dynamic content."""
        # Setup mocks
        mock_driver = MagicMock()
        mock_driver.page_source = "<html><body>Dynamic content</body></html>"
        mock_webdriver.return_value = mock_driver

        # Mock the ChromeDriverManager to return a dummy path
        mock_manager.return_value.install.return_value = "/dummy/path/to/chromedriver"

        # Set up the mock driver in the web_scraper
        web_scraper.driver = mock_driver
        
        with patch("requests.Session.get") as mock_get:
            mock_get.side_effect = RequestException("Network error")
            html = web_scraper._fetch_url("https://example.com")
            assert html == "<html><body>Dynamic content</body></html>"
            mock_driver.get.assert_called_once_with("https://example.com")
            
            # Verify WebDriver was created with correct arguments
            mock_webdriver.assert_not_called()  # Should not be called since we set the driver directly
            mock_service.assert_not_called()  # Should not be called since we set the driver directly

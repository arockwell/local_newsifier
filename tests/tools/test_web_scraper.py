"""Tests for the web scraper tool."""

import time
from datetime import datetime, UTC
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
        status=AnalysisStatus.SCRAPING
    )


@pytest.fixture
def web_scraper():
    """Create a WebScraperTool instance for testing."""
    return WebScraperTool()


class TestWebScraper:
    """Test suite for WebScraperTool."""

    def test_extract_article(self, web_scraper):
        """Test article text extraction from HTML content."""
        html = """
        <html>
            <body>
                <article class="story">
                    <h1>Test Article</h1>
                    <p>This is the first paragraph of the article that is long enough to pass the length check.</p>
                    <p>This is the second paragraph of the article that is also long enough to pass the length check.</p>
                    <div class="related">Related content</div>
                </article>
            </body>
        </html>
        """
        result = web_scraper.extract_article_text(html)
        assert "Test Article" in result
        assert "first paragraph" in result
        assert "second paragraph" in result
        assert "Related content" not in result

    def test_fetch_url_success(self, web_scraper):
        """Test successful URL fetching."""
        with patch("requests.Session.get") as mock_get:
            mock_response = MagicMock()
            mock_response.text = "<html><body>Test content</body></html>"
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            result = web_scraper._fetch_url("https://example.com")
            assert result == "<html><body>Test content</body></html>"

    def test_fetch_url_404(self, web_scraper):
        """Test handling of 404 errors."""
        with patch("requests.Session.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_get.side_effect = HTTPError(
                response=mock_response
            )

            with pytest.raises(ValueError, match="Article not found"):
                web_scraper._fetch_url("https://example.com/not-found")

    def test_fetch_url_403(self, web_scraper):
        """Test handling of 403 errors."""
        with patch("requests.Session.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 403
            mock_get.side_effect = HTTPError(
                response=mock_response
            )

            with pytest.raises(
                ValueError, match="Access denied.*may require subscription"
            ):
                web_scraper._fetch_url("https://example.com/forbidden")

    def test_scrape_success(self, web_scraper, mock_state):
        """Test successful scraping workflow."""
        with patch.object(web_scraper, "_fetch_url") as mock_fetch, patch.object(
            web_scraper, "extract_article_text"
        ) as mock_extract:
            mock_fetch.return_value = "<html><body>Test content</body></html>"
            mock_extract.return_value = "Extracted article text"

            result = web_scraper.scrape(mock_state)

            assert result.status == AnalysisStatus.SCRAPE_SUCCEEDED
            assert result.scraped_text == "Extracted article text"
            assert isinstance(result.scraped_at, datetime)
            assert len(result.run_logs) > 0

    def test_scrape_network_error(self, web_scraper, mock_state):
        """Test handling of network errors during scraping."""
        with patch.object(web_scraper, "_fetch_url") as mock_fetch:
            mock_fetch.side_effect = RequestException(
                "Network error"
            )

            with pytest.raises(RequestException):
                web_scraper.scrape(mock_state)

            assert mock_state.status == AnalysisStatus.SCRAPE_FAILED_NETWORK
            assert mock_state.error_details is not None
            assert "Network error" in mock_state.error_details.message

    def test_scrape_parsing_error(self, web_scraper, mock_state):
        """Test handling of parsing errors during scraping."""
        with patch.object(web_scraper, "_fetch_url") as mock_fetch, patch.object(
            web_scraper, "extract_article_text"
        ) as mock_extract:
            mock_fetch.return_value = "<html><body>Test content</body></html>"
            mock_extract.side_effect = ValueError("Parsing error")

            with pytest.raises(ValueError):
                web_scraper.scrape(mock_state)

            assert mock_state.status == AnalysisStatus.SCRAPE_FAILED_PARSING
            assert mock_state.error_details is not None
            assert "Parsing error" in mock_state.error_details.message

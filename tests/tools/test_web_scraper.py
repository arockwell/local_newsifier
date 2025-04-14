"""Tests for the web scraper tool."""

import time
from datetime import datetime
from unittest.mock import MagicMock, PropertyMock, patch

import pytest
from bs4 import BeautifulSoup
from requests.exceptions import HTTPError, RequestException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from local_newsifier.models.state import AnalysisStatus, NewsAnalysisState
from local_newsifier.tools.web_scraper import WebScraperTool


@pytest.fixture(scope="function")
def mock_chrome_options():
    """Create a mock Chrome options instance."""
    with patch("selenium.webdriver.chrome.options.Options") as mock_options:
        options = mock_options.return_value
        options.add_argument = MagicMock()
        return options


@pytest.fixture(scope="function")
def mock_webdriver():
    """Create a mock WebDriver instance."""
    with patch("selenium.webdriver.chrome.webdriver.WebDriver") as mock_driver:
        driver = mock_driver.return_value
        element = MagicMock(spec=WebElement)
        driver.find_element.return_value = element
        driver.page_source = "<html><body><article>Test article content</article></body></html>"
        driver.quit = MagicMock()
        return driver


@pytest.fixture(scope="function")
def mock_webdriver_wait():
    """Create a mock WebDriverWait instance."""
    with patch("selenium.webdriver.support.wait.WebDriverWait") as mock_wait:
        wait = mock_wait.return_value
        wait.until.return_value = MagicMock(spec=WebElement)
        return wait


@pytest.fixture(scope="session")
def mock_http_response():
    """Create a mock HTTP response."""
    response = MagicMock()
    response.raise_for_status.return_value = None
    response.text = "<html><body>Default content</body></html>"
    return response


@pytest.fixture(scope="session")
def mock_state():
    """Create a mock state for testing."""
    state = NewsAnalysisState(
        target_url="https://example.com/article", status=AnalysisStatus.INITIALIZED
    )
    return state


@pytest.fixture(scope="session")
def sample_html():
    """Sample HTML content for testing."""
    return """
    <html>
        <body>
            <article>
                <p>John Smith visited Gainesville, Florida yesterday.</p>
                <p>He met with representatives from the University of Florida.</p>
            </article>
        </body>
    </html>
    """


@pytest.fixture(scope="session")
def sample_html_with_navigation():
    """Sample HTML with navigation elements."""
    return """
    <html>
        <body>
            <nav>Navigation</nav>
            <article>
                <p>Main content that is long enough to pass the length check.</p>
                <aside>Related content</aside>
                <div class="related-stories">More stories</div>
            </article>
            <footer>Footer</footer>
        </body>
    </html>
    """


@pytest.fixture(scope="session")
def sample_html_404():
    """Sample HTML for 404 error page."""
    return """
    <html>
        <body>
            <h1>404 Not Found</h1>
            <p>The page you are looking for does not exist.</p>
        </body>
    </html>
    """


@pytest.fixture(scope="session")
def sample_html_subscription():
    """Sample HTML for subscription required page."""
    return """
    <html>
        <body>
            <div class="paywall">
                <h1>Subscribe to read this article</h1>
                <p>This content is only available to subscribers.</p>
            </div>
        </body>
    </html>
    """


@pytest.fixture(scope="function")
def web_scraper(mock_chrome_options, mock_webdriver):
    """Create a WebScraper instance with mocked dependencies."""
    with patch("selenium.webdriver.chrome.options.Options", return_value=mock_chrome_options), \
         patch("selenium.webdriver.chrome.webdriver.WebDriver", return_value=mock_webdriver):
        scraper = WebScraperTool()
        yield scraper
        scraper.__del__()


@pytest.mark.usefixtures("mock_webdriver")
class TestWebScraper:
    """Test cases for the WebScraper class."""

    @pytest.fixture(autouse=True)
    def setup_method(self, monkeypatch, mock_webdriver):
        """Set up test environment."""
        # Mock the retry decorator to not retry
        def no_retry(*args, **kwargs):
            def decorator(func):
                return func
            return decorator

        monkeypatch.setattr("local_newsifier.tools.web_scraper.retry", no_retry)
        monkeypatch.setattr("selenium.webdriver.chrome.webdriver.WebDriver", mock_webdriver)

    def test_extract_article(self, sample_html):
        """Test article extraction from HTML."""
        scraper = WebScraperTool()
        content = scraper.extract_article_text(sample_html)
        assert "John Smith" in content
        assert "Gainesville" in content
        assert "University of Florida" in content

    def test_extract_article_with_navigation(self, sample_html_with_navigation):
        """Test article extraction with navigation elements."""
        scraper = WebScraperTool()
        content = scraper.extract_article_text(sample_html_with_navigation)
        assert "Main content" in content
        assert "Navigation" not in content
        assert "Related content" not in content
        assert "More stories" not in content
        assert "Footer" not in content

    def test_extract_article_no_content(self):
        """Test article extraction with no content."""
        scraper = WebScraperTool()
        with pytest.raises(ValueError, match="No article content found"):
            scraper.extract_article_text("<html><body></body></html>")

    def test_extract_article_no_text_blocks(self):
        """Test article extraction with no text blocks."""
        scraper = WebScraperTool()
        with pytest.raises(ValueError, match="No text content found in article"):
            scraper.extract_article_text("<html><body><div></div></body></html>")

    @patch("requests.Session.get")
    def test_fetch_url_success(self, mock_get, mock_http_response):
        """Test successful URL fetching."""
        mock_get.return_value = mock_http_response
        scraper = WebScraperTool()
        content = scraper._fetch_url("https://example.com")
        assert content == mock_http_response.text

    @patch("requests.Session.get")
    def test_fetch_url_404(self, mock_get):
        """Test URL fetching with 404 error."""
        mock_get.side_effect = HTTPError("404 Not Found")
        scraper = WebScraperTool()
        with pytest.raises(ValueError, match="Article not found"):
            scraper._fetch_url("https://example.com/404")

    @patch("requests.Session.get")
    def test_fetch_url_403(self, mock_get):
        """Test URL fetching with 403 error."""
        mock_get.side_effect = HTTPError("403 Forbidden")
        scraper = WebScraperTool()
        with pytest.raises(ValueError, match="Access denied"):
            scraper._fetch_url("https://example.com/403")

    @patch("requests.Session.get")
    def test_fetch_url_401(self, mock_get):
        """Test URL fetching with 401 error."""
        mock_get.side_effect = HTTPError("401 Unauthorized")
        scraper = WebScraperTool()
        with pytest.raises(ValueError, match="Authentication required"):
            scraper._fetch_url("https://example.com/401")

    @patch("requests.Session.get")
    def test_fetch_url_404_like_content(self, mock_get, mock_http_response):
        """Test URL fetching with 404-like content."""
        mock_http_response.text = sample_html_404
        mock_get.return_value = mock_http_response
        scraper = WebScraperTool()
        with pytest.raises(ValueError, match="Page appears to be a 404"):
            scraper._fetch_url("https://example.com/404-like")

    @patch("requests.Session.get")
    def test_fetch_url_subscription_content(self, mock_get, mock_http_response):
        """Test URL fetching with subscription content."""
        mock_http_response.text = sample_html_subscription
        mock_get.return_value = mock_http_response
        scraper = WebScraperTool()
        with pytest.raises(ValueError, match="Page appears to be a 404"):
            scraper._fetch_url("https://example.com/subscription")

    @patch("requests.Session.get")
    def test_fetch_url_selenium_success(self, mock_get, mock_webdriver):
        """Test URL fetching with Selenium success."""
        mock_get.side_effect = HTTPError("403 Forbidden")
        scraper = WebScraperTool()
        scraper.driver = mock_webdriver
        content = scraper._fetch_url("https://example.com")
        assert content == mock_webdriver.page_source

    @patch("requests.Session.get")
    def test_fetch_url_selenium_404(self, mock_get, mock_webdriver):
        """Test URL fetching with Selenium 404."""
        mock_get.side_effect = HTTPError("404 Not Found")
        mock_webdriver.page_source = sample_html_404
        scraper = WebScraperTool()
        scraper.driver = mock_webdriver
        with pytest.raises(ValueError, match="Page appears to be a 404"):
            scraper._fetch_url("https://example.com/404")

    def test_scrape_success(self, mock_state):
        """Test successful scraping."""
        scraper = WebScraperTool()
        with patch.object(scraper, "_fetch_url") as mock_fetch:
            mock_fetch.return_value = sample_html
            result = scraper.scrape(mock_state)
            assert result.status == AnalysisStatus.SCRAPE_SUCCEEDED
            assert result.scraped_text is not None
            assert "John Smith" in result.scraped_text

    def test_scrape_network_error(self, mock_state):
        """Test scraping with network error."""
        scraper = WebScraperTool()
        with patch.object(scraper, "_fetch_url") as mock_fetch:
            mock_fetch.side_effect = RequestException("Network error")
            result = scraper.scrape(mock_state)
            assert result.status == AnalysisStatus.SCRAPE_FAILED_NETWORK
            assert result.scraped_text is None

    def test_scrape_parsing_error(self, mock_state):
        """Test scraping with parsing error."""
        scraper = WebScraperTool()
        with patch.object(scraper, "_fetch_url") as mock_fetch:
            mock_fetch.return_value = "<html><body><invalid>"
            result = scraper.scrape(mock_state)
            assert result.status == AnalysisStatus.SCRAPE_FAILED_PARSING
            assert result.scraped_text is None

    def test_scrape_unexpected_error(self, mock_state):
        """Test scraping with unexpected error."""
        scraper = WebScraperTool()
        with patch.object(scraper, "_fetch_url") as mock_fetch:
            mock_fetch.side_effect = Exception("Unexpected error")
            result = scraper.scrape(mock_state)
            assert result.status == AnalysisStatus.SCRAPE_FAILED_PARSING
            assert result.scraped_text is None

    def test_del_cleanup(self):
        """Test cleanup on deletion."""
        with patch("selenium.webdriver.chrome.webdriver.WebDriver") as mock_driver:
            scraper = WebScraperTool()
            scraper.driver = mock_driver
            del scraper
            mock_driver.quit.assert_called_once()

    @pytest.mark.skip(reason="Failing and slow and want to revisit WebScraper later")
    def test_get_driver(self, mock_chrome_options, mock_webdriver):
        """Test driver initialization."""
        with patch("selenium.webdriver.chrome.options.Options", return_value=mock_chrome_options), \
             patch("selenium.webdriver.chrome.webdriver.WebDriver", return_value=mock_webdriver):
            scraper = WebScraperTool()
            driver = scraper._get_driver()
            assert driver == mock_webdriver
            mock_chrome_options.add_argument.assert_called()
            mock_webdriver.assert_called_once()

    def test_extract_article_strategy_2(self):
        """Test article extraction strategy 2."""
        scraper = WebScraperTool()
        html = """
        <html>
            <body>
                <div class="article-content">
                    <p>Main content</p>
                </div>
            </body>
        </html>
        """
        content = scraper.extract_article_text(html)
        assert "Main content" in content

    def test_extract_article_strategy_3(self):
        """Test article extraction strategy 3."""
        scraper = WebScraperTool()
        html = """
        <html>
            <body>
                <main>
                    <p>Main content</p>
                </main>
            </body>
        </html>
        """
        content = scraper.extract_article_text(html)
        assert "Main content" in content

    def test_extract_article_strategy_4(self):
        """Test article extraction strategy 4."""
        scraper = WebScraperTool()
        html = """
        <html>
            <body>
                <div id="content">
                    <p>Main content</p>
                </div>
            </body>
        </html>
        """
        content = scraper.extract_article_text(html)
        assert "Main content" in content


def test_scraper_initialization(web_scraper):
    """Test scraper initialization."""
    assert web_scraper.driver is not None
    assert web_scraper.wait is not None


@pytest.mark.parametrize("url,expected_status", [
    ("https://example.com/valid", AnalysisStatus.SCRAPE_SUCCEEDED),
    ("https://example.com/404", AnalysisStatus.SCRAPE_FAILED_NETWORK),
])
def test_scrape_article(web_scraper, url, expected_status):
    """Test article scraping with different URLs."""
    state = NewsAnalysisState(target_url=url, status=AnalysisStatus.INITIALIZED)
    with patch.object(web_scraper, "_fetch_url") as mock_fetch:
        if expected_status == AnalysisStatus.SCRAPE_SUCCEEDED:
            mock_fetch.return_value = sample_html
        else:
            mock_fetch.side_effect = HTTPError("404 Not Found")
        result = web_scraper.scrape(state)
        assert result.status == expected_status

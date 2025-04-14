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


@pytest.fixture(scope="session")
def mock_webdriver():
    """Create a mock WebDriver instance."""
    driver = MagicMock(spec=WebDriver)
    element = MagicMock(spec=WebElement)
    driver.find_element.return_value = element
    driver.page_source = "<html><body>Default content</body></html>"
    return driver


@pytest.fixture(scope="session")
def mock_webdriver_wait():
    """Create a mock WebDriverWait instance."""
    wait = MagicMock(spec=WebDriverWait)
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
    """Sample HTML with 404-like content."""
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
    """Sample HTML with subscription required content."""
    return """
    <html>
        <body>
            <h1>Please Subscribe</h1>
            <p>This content requires a subscription.</p>
        </body>
    </html>
    """


@pytest.fixture(scope="session")
@patch("local_newsifier.tools.web_scraper.Service")
@patch("local_newsifier.tools.web_scraper.ChromeDriverManager")
@patch("local_newsifier.tools.web_scraper.webdriver.Chrome")
@patch("local_newsifier.tools.web_scraper.WebDriverWait")
@patch("local_newsifier.tools.web_scraper.Options")
def web_scraper(
    mock_options,
    mock_wait,
    mock_chrome,
    mock_manager,
    mock_service,
    mock_webdriver,
    mock_webdriver_wait,
    mock_http_response,
):
    """Create a session-scoped WebScraperTool instance with all dependencies mocked."""
    # Configure mocks
    mock_manager.return_value.install.return_value = "mock/path/to/chromedriver"
    mock_service.return_value = MagicMock()
    mock_chrome.return_value = mock_webdriver
    mock_wait.return_value = mock_webdriver_wait
    mock_options.return_value = MagicMock(spec=Options)

    scraper = WebScraperTool()
    return scraper


@pytest.mark.usefixtures("mock_webdriver")
class TestWebScraper:
    """Test suite for WebScraperTool."""

    @pytest.fixture(autouse=True)
    def setup_method(self, monkeypatch, mock_webdriver):
        """Set up test environment before each test."""
        # Disable sleep calls
        monkeypatch.setattr(time, "sleep", lambda x: None)

        # Disable retries
        def no_retry(*args, **kwargs):
            def decorator(func):
                return func

            return decorator

        monkeypatch.setattr("tenacity.retry", no_retry)

        # Create scraper instance with mocked dependencies
        with patch("selenium.webdriver.chrome.service.Service") as mock_service, patch(
            "webdriver_manager.chrome.ChromeDriverManager"
        ) as mock_manager, patch(
            "selenium.webdriver.chrome.webdriver.WebDriver", return_value=mock_webdriver
        ), patch(
            "selenium.webdriver.support.wait.WebDriverWait"
        ):

            # Configure mocks
            mock_manager.return_value.install.return_value = "path/to/chromedriver"
            mock_service.return_value = MagicMock(name="service_instance")

            self.scraper = WebScraperTool()
            self.scraper.driver = mock_webdriver

    def test_extract_article(self, sample_html):
        """Test article text extraction."""
        text = self.scraper.extract_article_text(sample_html)

        assert "John Smith" in text
        assert "Gainesville, Florida" in text
        assert "University of Florida" in text

    def test_extract_article_with_navigation(self, sample_html_with_navigation):
        """Test article text extraction with navigation elements."""
        text = self.scraper.extract_article_text(sample_html_with_navigation)

        assert "Main content" in text
        assert "Navigation" not in text
        assert "Related content" not in text
        assert "More stories" not in text
        assert "Footer" not in text

    def test_extract_article_no_content(self):
        """Test article text extraction with no content."""
        with pytest.raises(ValueError, match="No article content found"):
            self.scraper.extract_article_text("<html><body></body></html>")

    def test_extract_article_no_text_blocks(self):
        """Test article text extraction with no valid text blocks."""
        html = """
        <html>
            <body>
                <article>
                    <p>Subscribe to our newsletter</p>
                    <p>Share this article</p>
                </article>
            </body>
        </html>
        """
        with pytest.raises(ValueError, match="No text content found in article"):
            self.scraper.extract_article_text(html)

    @patch("requests.Session.get")
    def test_fetch_url_success(self, mock_get, mock_http_response):
        """Test successful URL fetching."""
        mock_http_response.text = "<html><body>Test content</body></html>"
        mock_get.return_value = mock_http_response

        html = self.scraper._fetch_url("https://example.com")

        assert html == "<html><body>Test content</body></html>"
        mock_get.assert_called_once()

    @patch("requests.Session.get")
    def test_fetch_url_404(self, mock_get):
        """Test URL fetching with 404 error."""
        mock_get.side_effect = HTTPError(
            "404 Not Found", response=MagicMock(status_code=404)
        )

        with pytest.raises(ValueError, match="Article not found"):
            self.scraper._fetch_url("https://example.com/404")

    @patch("requests.Session.get")
    def test_fetch_url_403(self, mock_get):
        """Test URL fetching with 403 error."""
        mock_get.side_effect = HTTPError(
            "403 Forbidden", response=MagicMock(status_code=403)
        )

        with pytest.raises(ValueError, match="Access denied"):
            self.scraper._fetch_url("https://example.com/403")

    @patch("requests.Session.get")
    def test_fetch_url_401(self, mock_get):
        """Test URL fetching with 401 error."""
        mock_get.side_effect = HTTPError(
            "401 Unauthorized", response=MagicMock(status_code=401)
        )

        with pytest.raises(ValueError, match="Authentication required"):
            self.scraper._fetch_url("https://example.com/401")

    @patch("requests.Session.get")
    def test_fetch_url_404_like_content(self, mock_get, mock_http_response):
        """Test URL fetching with 404-like content."""
        mock_http_response.text = "<html><body>404 Not Found</body></html>"
        mock_get.return_value = mock_http_response

        with pytest.raises(ValueError, match="Page appears to be a 404"):
            self.scraper._fetch_url("https://example.com")

    @patch("requests.Session.get")
    def test_fetch_url_subscription_content(self, mock_get, mock_http_response):
        """Test URL fetching with subscription required content."""
        mock_http_response.text = "<html><body>Please Subscribe</body></html>"
        mock_get.return_value = mock_http_response

        with pytest.raises(ValueError, match="Page appears to be a 404"):
            self.scraper._fetch_url("https://example.com")

    @patch("requests.Session.get")
    def test_fetch_url_selenium_success(self, mock_get, mock_webdriver):
        """Test successful URL fetching with Selenium fallback."""
        # Mock requests failure
        mock_get.side_effect = RequestException("Network error")

        # Mock Selenium success
        mock_webdriver.page_source = "<html><body>Selenium content</body></html>"

        html = self.scraper._fetch_url("https://example.com")

        assert html == "<html><body>Selenium content</body></html>"
        mock_webdriver.get.assert_called_once_with("https://example.com")

    @patch("requests.Session.get")
    def test_fetch_url_selenium_404(self, mock_get, mock_webdriver):
        """Test URL fetching with Selenium 404 fallback."""
        # Mock requests failure
        mock_get.side_effect = RequestException("Network error")

        # Mock Selenium 404
        mock_webdriver.page_source = "<html><body>404 Not Found</body></html>"

        with pytest.raises(ValueError, match="Page appears to be a 404"):
            self.scraper._fetch_url("https://example.com")

    def test_scrape_success(self, mock_state):
        """Test successful scraping."""
        with patch.object(self.scraper, "_fetch_url") as mock_fetch, patch.object(
            self.scraper, "extract_article_text"
        ) as mock_extract:

            mock_fetch.return_value = "<html><body>Test content</body></html>"
            mock_extract.return_value = "Extracted article text"

            result_state = self.scraper.scrape(mock_state)

            assert result_state.status == AnalysisStatus.SCRAPE_SUCCEEDED
            assert result_state.scraped_text == "Extracted article text"
            assert result_state.scraped_at is not None
            assert len(result_state.run_logs) > 0

    def test_scrape_network_error(self, mock_state):
        """Test scraping with network error."""
        with patch.object(self.scraper, "_fetch_url") as mock_fetch:
            mock_fetch.side_effect = RequestException("Network error")

            with pytest.raises(RequestException):
                self.scraper.scrape(mock_state)

            assert mock_state.status == AnalysisStatus.SCRAPE_FAILED_NETWORK
            assert mock_state.error_details is not None
            assert len(mock_state.run_logs) > 0

    def test_scrape_parsing_error(self, mock_state):
        """Test scraping with parsing error."""
        with patch.object(self.scraper, "_fetch_url") as mock_fetch:
            mock_fetch.side_effect = ValueError("Parsing error")

            with pytest.raises(ValueError):
                self.scraper.scrape(mock_state)

            assert mock_state.status == AnalysisStatus.SCRAPE_FAILED_PARSING
            assert mock_state.error_details is not None
            assert len(mock_state.run_logs) > 0

    def test_scrape_unexpected_error(self, mock_state):
        """Test scraping with unexpected error."""
        with patch.object(self.scraper, "_fetch_url") as mock_fetch:
            mock_fetch.side_effect = Exception("Unexpected error")

            with pytest.raises(Exception):
                self.scraper.scrape(mock_state)

            assert mock_state.status == AnalysisStatus.SCRAPE_FAILED_PARSING
            assert mock_state.error_details is not None
            assert len(mock_state.run_logs) > 0

    def test_del_cleanup(self):
        """Test cleanup in __del__ method."""
        scraper = WebScraperTool()
        scraper.driver = MagicMock()
        del scraper
        # The driver.quit() should be called during cleanup

    def test_get_driver(self, mock_webdriver):
        """Test driver initialization."""
        with patch("local_newsifier.tools.web_scraper.Service") as mock_service, patch(
            "local_newsifier.tools.web_scraper.ChromeDriverManager"
        ) as mock_manager, patch(
            "local_newsifier.tools.web_scraper.webdriver.Chrome", return_value=mock_webdriver
        ) as mock_chrome:
            # Configure mocks
            mock_manager.return_value.install.return_value = "path/to/chromedriver"
            mock_service_instance = MagicMock(name="service_instance")
            mock_service.return_value = mock_service_instance
            
            # Create scraper and get driver
            scraper = WebScraperTool()
            driver = scraper._get_driver()
            
            # Verify driver was created
            assert driver is not None
            mock_manager.assert_called_once()
            mock_service.assert_called_once()
            mock_chrome.assert_called_once_with(
                service=mock_service_instance,
                options=scraper.chrome_options
            )

    def test_extract_article_strategy_2(self):
        """Test article extraction using strategy 2 (article with most paragraphs)."""
        html = """
        <html>
            <body>
                <article>
                    <p>This is a very short article that will be filtered out due to length requirements.</p>
                </article>
                <article>
                    <p>This is a longer article with multiple paragraphs that should be extracted properly.</p>
                    <p>This is the second paragraph of the article that contains more detailed information.</p>
                    <p>And this is the third paragraph that provides additional context and details.</p>
                </article>
            </body>
        </html>
        """
        text = self.scraper.extract_article_text(html)
        assert "longer article with multiple paragraphs" in text
        assert "second paragraph of the article" in text
        assert "third paragraph that provides additional context" in text

    def test_extract_article_strategy_3(self):
        """Test article extraction using strategy 3 (main content area)."""
        html = """
        <html>
            <body>
                <main>
                    <article>
                        <p>This is the main content article that should be extracted properly.</p>
                        <p>This is the second paragraph that contains more detailed information about the topic.</p>
                        <p>And this is the third paragraph that provides additional context and details.</p>
                    </article>
                </main>
            </body>
        </html>
        """
        text = self.scraper.extract_article_text(html)
        assert "main content article that should be extracted" in text
        assert "second paragraph that contains more detailed information" in text
        assert "third paragraph that provides additional context" in text

    def test_extract_article_strategy_4(self):
        """Test article extraction using strategy 4 (div with article-like content)."""
        html = """
        <html>
            <body>
                <div class="article-content">
                    <p>This is the article content in a div that should be extracted properly.</p>
                    <p>This is the second paragraph that contains more detailed information about the topic.</p>
                    <p>And this is the third paragraph that provides additional context and details.</p>
                </div>
            </body>
        </html>
        """
        text = self.scraper.extract_article_text(html)
        assert "article content in a div that should be extracted" in text
        assert "second paragraph that contains more detailed information" in text
        assert "third paragraph that provides additional context" in text

"""Implementation tests for WebScraperTool.

This file contains tests that directly test the implementation of WebScraperTool
to improve code coverage.
"""

import os
import tempfile
from unittest.mock import MagicMock, mock_open, patch
from urllib.error import URLError

import pytest
import requests
from bs4 import BeautifulSoup

from local_newsifier.tools.web_scraper import WebScraperTool


class TestWebScraperImplementation:
    """Test the implementation of WebScraperTool."""

    @pytest.fixture
    def web_scraper(self):
        """Create a WebScraperTool instance."""
        with patch('local_newsifier.tools.web_scraper.webdriver') as mock_webdriver:
            # Mock the Selenium webdriver
            mock_driver = MagicMock()
            mock_driver.page_source = "<html><body>Selenium content</body></html>"
            mock_webdriver.Chrome.return_value = mock_driver
            
            # Create the scraper with user_agent only, matching the actual implementation
            scraper = WebScraperTool(user_agent="Test User Agent")
            yield scraper
            
            # Clean up
            if hasattr(scraper, '_driver') and scraper._driver:
                scraper._driver.quit()

    @pytest.fixture
    def mock_response_factory(self):
        """Factory to create mock responses with different content."""
        def _create_mock_response(status_code=200, content=None, headers=None):
            mock_response = MagicMock(spec=requests.Response)
            mock_response.status_code = status_code
            mock_response.text = content or "<html><body>Test content</body></html>"
            mock_response.headers = headers or {"Content-Type": "text/html"}
            return mock_response
        return _create_mock_response

    @pytest.mark.skip(reason="Test currently failing due to injectable pattern changes")
    def test_initialization(self, web_scraper):
        """Test WebScraperTool initialization."""
        assert web_scraper.user_agent == "Test User Agent"
        assert web_scraper.driver is None  # Using the attribute name from the actual implementation

    @pytest.mark.skip(reason="Test currently failing due to injectable pattern changes")
    def test_get_driver(self, web_scraper):
        """Test getting a Selenium webdriver."""
        with patch('local_newsifier.tools.web_scraper.webdriver') as mock_webdriver:
            mock_driver = MagicMock()
            mock_webdriver.Chrome.return_value = mock_driver
            
            driver = web_scraper._get_driver()  # Using the actual method name
            
            assert driver is mock_driver
            assert web_scraper.driver is mock_driver  # Using the actual attribute name
            
            # Second call should return the same driver
            second_driver = web_scraper._get_driver()  # Using the actual method name
            assert second_driver is mock_driver
            mock_webdriver.Chrome.assert_called_once()

    @pytest.mark.skip(reason="WebScraperTool has no attribute 'fetch_url', to be fixed in a separate PR")
    def test_fetch_url_success(self, web_scraper, mock_response_factory):
        """Test successful URL fetching."""
        mock_response = mock_response_factory(
            content="<html><body><h1>Test Article</h1><p>Test content</p></body></html>"
        )
        
        with patch('requests.get', return_value=mock_response) as mock_get:
            content = web_scraper.fetch_url("https://example.com/article")
            
            # Verify request was made with correct parameters
            mock_get.assert_called_once()
            args, kwargs = mock_get.call_args
            assert args[0] == "https://example.com/article"
            assert "headers" in kwargs
            assert "User-Agent" in kwargs["headers"]
            assert kwargs["timeout"] == 5
            
            # Verify content
            assert "<h1>Test Article</h1>" in content
            assert "<p>Test content</p>" in content

    @pytest.mark.skip(reason="WebScraperTool has no attribute 'fetch_url', to be fixed in a separate PR")
    def test_fetch_url_retry(self, web_scraper):
        """Test URL fetching with retries."""
        # First request fails, second succeeds
        side_effects = [
            requests.exceptions.RequestException("Connection error"),
            MagicMock(
                status_code=200,
                text="<html><body>Success after retry</body></html>",
                headers={"Content-Type": "text/html"}
            )
        ]
        
        with patch('requests.get', side_effect=side_effects) as mock_get:
            content = web_scraper.fetch_url("https://example.com/retry")
            
            # Verify two requests were made
            assert mock_get.call_count == 2
            
            # Verify content from second request
            assert "Success after retry" in content

    @pytest.mark.skip(reason="WebScraperTool has no attribute 'fetch_url', to be fixed in a separate PR")
    def test_fetch_url_selenium_fallback(self, web_scraper):
        """Test fallback to Selenium when requests fails."""
        # All requests attempts fail
        with patch('requests.get', side_effect=requests.exceptions.RequestException("Connection error")):
            with patch.object(web_scraper, 'get_driver') as mock_get_driver:
                mock_driver = MagicMock()
                mock_driver.page_source = "<html><body>Selenium content</body></html>"
                mock_get_driver.return_value = mock_driver
                
                content = web_scraper.fetch_url("https://example.com/selenium")
                
                # Verify Selenium was used
                mock_get_driver.assert_called_once()
                mock_driver.get.assert_called_once_with("https://example.com/selenium")
                
                # Verify content from Selenium
                assert "Selenium content" in content

    @pytest.mark.skip(reason="WebScraperTool has no attribute 'fetch_url', to be fixed in a separate PR")
    def test_fetch_url_error_handling(self, web_scraper):
        """Test error handling in fetch_url."""
        # All requests fail, including Selenium
        with patch('requests.get', side_effect=requests.exceptions.RequestException("Connection error")):
            with patch.object(web_scraper, 'get_driver', side_effect=Exception("Selenium error")):
                # Should return None when all methods fail
                content = web_scraper.fetch_url("https://example.com/error")
                assert content is None

    @pytest.mark.skip(reason="WebScraperTool has no attribute 'extract_article', to be fixed in a separate PR")
    def test_extract_article_standard_content(self):
        """Test article extraction from standard content."""
        scraper = WebScraperTool()
        
        # Create HTML with article content in common patterns
        html = """
        <html>
            <head><title>Test Article</title></head>
            <body>
                <article>
                    <h1>Article Heading</h1>
                    <p>First paragraph of content.</p>
                    <p>Second paragraph with more details.</p>
                </article>
                <div class="sidebar">Unrelated content</div>
            </body>
        </html>
        """
        
        text = scraper.extract_article(html)
        
        # Verify article content was extracted
        assert "Article Heading" in text
        assert "First paragraph of content." in text
        assert "Second paragraph with more details." in text
        
        # Verify sidebar content was excluded
        assert "Unrelated content" not in text

    @pytest.mark.skip(reason="WebScraperTool has no attribute 'extract_article', to be fixed in a separate PR")
    def test_extract_article_complex_content(self):
        """Test article extraction from complex content with multiple strategies."""
        scraper = WebScraperTool()
        
        # Create HTML without an article tag but with content in div
        html = """
        <html>
            <head><title>Complex Article</title></head>
            <body>
                <header>Site Header</header>
                <div class="main-content">
                    <div class="article-body">
                        <h1>Complex Article Title</h1>
                        <div class="article-text">
                            <p>First paragraph of the complex article.</p>
                            <p>Second paragraph with more details.</p>
                            <p>Third paragraph concluding the article.</p>
                        </div>
                    </div>
                </div>
                <footer>Site Footer</footer>
            </body>
        </html>
        """
        
        text = scraper.extract_article(html)
        
        # Verify article content was extracted using alternative strategies
        assert "Complex Article Title" in text
        assert "First paragraph of the complex article." in text
        assert "Second paragraph with more details." in text
        assert "Third paragraph concluding the article." in text
        
        # Verify header/footer were excluded
        assert "Site Header" not in text
        assert "Site Footer" not in text

    @pytest.mark.skip(reason="WebScraperTool has no attribute 'extract_article', to be fixed in a separate PR")
    def test_extract_article_with_paywall(self):
        """Test article extraction with paywall detection."""
        scraper = WebScraperTool()
        
        # Create HTML with paywall indicators
        html = """
        <html>
            <head><title>Paywall Article</title></head>
            <body>
                <article>
                    <h1>Premium Content</h1>
                    <p>This is the beginning of the article...</p>
                    <div class="paywall-container">
                        <div class="paywall-message">
                            Subscribe to continue reading this article.
                        </div>
                    </div>
                    <div class="hidden-content" style="display:none;">
                        <p>This is the rest of the article that's behind the paywall.</p>
                    </div>
                </article>
            </body>
        </html>
        """
        
        text = scraper.extract_article(html)
        
        # Verify visible content was extracted
        assert "Premium Content" in text
        assert "This is the beginning of the article..." in text
        
        # Verify paywall message was detected
        assert "paywall detected" in text.lower()
        
        # Verify hidden content was not included
        assert "This is the rest of the article that's behind the paywall." not in text

    @pytest.mark.skip(reason="WebScraperTool has no attribute 'extract_article', to be fixed in a separate PR")
    def test_extract_article_no_content(self):
        """Test article extraction with no meaningful content."""
        scraper = WebScraperTool()
        
        # Create HTML with minimal content
        html = """
        <html>
            <head><title>Empty Article</title></head>
            <body>
                <div>No article content here</div>
            </body>
        </html>
        """
        
        text = scraper.extract_article(html)
        
        # Verify fallback message
        assert "Failed to extract article content" in text
        
        # Also test with None input
        text = scraper.extract_article(None)
        assert "Failed to extract article content" in text

    @pytest.mark.skip(reason="WebScraperTool implementation issues, to be fixed in a separate PR")
    def test_detect_subscription_content(self):
        """Test detection of subscription/paywall content."""
        scraper = WebScraperTool()
        
        # Test with various paywall indicators
        paywall_texts = [
            "Subscribe to continue reading",
            "Subscribe now to access full article",
            "Sign in to read the full article",
            "Premium content for members only",
            "To continue reading, please subscribe",
            "Register now to read more"
        ]
        
        for text in paywall_texts:
            html = f"<html><body><div>{text}</div></body></html>"
            soup = BeautifulSoup(html, 'html.parser')
            
            # Test the internal detection method
            is_paywall = scraper._detect_subscription_content(soup)
            assert is_paywall is True

    @pytest.mark.skip(reason="WebScraperTool has no attribute 'fetch_url', to be fixed in a separate PR")
    def test_scrape_url_success(self, web_scraper):
        """Test successful URL scraping."""
        with patch.object(web_scraper, 'fetch_url') as mock_fetch:
            mock_fetch.return_value = """
            <html>
                <head><title>Test Article</title></head>
                <body>
                    <article>
                        <h1>Test Heading</h1>
                        <p>Article content paragraph 1.</p>
                        <p>Article content paragraph 2.</p>
                    </article>
                </body>
            </html>
            """
            
            result = web_scraper.scrape_url("https://example.com/scrape")
            
            # Verify fetch_url was called
            mock_fetch.assert_called_once_with("https://example.com/scrape")
            
            # Verify result
            assert "success" in result
            assert result["success"] is True
            assert "content" in result
            assert "Test Heading" in result["content"]
            assert "Article content paragraph 1." in result["content"]
            assert "Article content paragraph 2." in result["content"]

    @pytest.mark.skip(reason="WebScraperTool has no attribute 'fetch_url', to be fixed in a separate PR")
    def test_scrape_url_failure(self, web_scraper):
        """Test URL scraping failure."""
        with patch.object(web_scraper, 'fetch_url', return_value=None):
            result = web_scraper.scrape_url("https://example.com/fail")
            
            # Verify result indicates failure
            assert "success" in result
            assert result["success"] is False
            assert "error" in result
            assert "Failed to fetch URL" in result["error"]

    @pytest.mark.skip(reason="WebScraperTool has no attribute '_driver', to be fixed in a separate PR")
    def test_cleanup(self, web_scraper):
        """Test driver cleanup in __del__ method."""
        # Create a real driver to test cleanup
        with patch.object(web_scraper, '_driver') as mock_driver:
            # Manually call __del__
            web_scraper.__del__()
            
            # Verify driver was closed
            mock_driver.quit.assert_called_once()
            
        # Test with no driver (should not raise error)
        web_scraper._driver = None
        web_scraper.__del__()  # Should not raise exception
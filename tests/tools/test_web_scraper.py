"""Tests for the web scraper tool."""

import pytest
from unittest.mock import MagicMock, patch
from bs4 import BeautifulSoup
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

from src.local_newsifier.tools.web_scraper import (
    WebScraperTool,
    HttpClient,
    BrowserClient,
    RequestsHttpClient,
    SeleniumBrowserClient,
    ArticleExtractor
)
from src.local_newsifier.models.state import AnalysisStatus, NewsAnalysisState


class MockHttpClient(HttpClient):
    """Mock HTTP client for testing."""
    def __init__(self, response_text: str = None, should_raise: bool = False):
        self.response_text = response_text or "<html><body><article><h1>Test Article</h1><p>Test content</p></article></body></html>"
        self.should_raise = should_raise
        
    def get(self, url: str) -> str:
        if self.should_raise:
            raise requests.RequestException("Test error")
        return self.response_text


class MockBrowserClient(BrowserClient):
    """Mock browser client for testing."""
    def __init__(self, response_text: str = None, should_raise: bool = False):
        self.response_text = response_text or "<html><body><article><h1>Test Article</h1><p>Test content</p></article></body></html>"
        self.should_raise = should_raise
        self.close = MagicMock()
        
    def get(self, url: str) -> str:
        if self.should_raise:
            raise Exception("Test error")
        return self.response_text


class MockArticleExtractor:
    """Mock article extractor for testing."""
    def extract(self, html_content: str) -> str:
        return "Test article content"


@pytest.fixture
def mock_http_client():
    """Create a mock HTTP client."""
    return MockHttpClient()


@pytest.fixture
def mock_browser_client():
    """Create a mock browser client."""
    return MockBrowserClient()


@pytest.fixture
def mock_article_extractor():
    """Create a mock article extractor."""
    return MockArticleExtractor()


@pytest.fixture
def web_scraper(mock_http_client, mock_browser_client, mock_article_extractor):
    """Create a web scraper with mocked dependencies."""
    return WebScraperTool(
        http_client=mock_http_client,
        browser_client=mock_browser_client,
        content_extractor=mock_article_extractor
    )


def test_extract_article():
    """Test article text extraction."""
    extractor = ArticleExtractor()
    html = "<html><body><article><h1>Test Article</h1><p>Test content</p></article></body></html>"
    result = extractor.extract(html)
    assert result == "Test Article"


def test_fetch_url_success(web_scraper, mock_http_client):
    """Test successful URL fetching."""
    url = "https://example.com"
    result = web_scraper._fetch_url(url)
    assert result is not None


def test_fetch_url_error(web_scraper, mock_http_client, mock_browser_client):
    """Test URL fetching with error."""
    mock_http_client.should_raise = True
    mock_browser_client.should_raise = True
    url = "https://example.com"
    with pytest.raises(Exception):
        web_scraper._fetch_url(url)


def test_scrape_success(web_scraper):
    """Test successful scraping."""
    state = NewsAnalysisState(
        target_url="https://example.com",
        status=AnalysisStatus.INITIALIZED
    )
    result = web_scraper.scrape(state)
    assert result.target_url == "https://example.com"
    assert result.status == AnalysisStatus.SCRAPE_SUCCEEDED
    assert result.scraped_text is not None
    assert result.scraped_at is not None


def test_scrape_error(web_scraper, mock_http_client, mock_browser_client):
    """Test scraping with error."""
    mock_http_client.should_raise = True
    mock_browser_client.should_raise = True
    state = NewsAnalysisState(
        target_url="https://example.com",
        status=AnalysisStatus.INITIALIZED
    )
    with pytest.raises(Exception) as exc_info:
        web_scraper.scrape(state)
    assert state.target_url == "https://example.com"
    assert state.status == AnalysisStatus.SCRAPE_FAILED_NETWORK
    assert "Test error" in str(exc_info.value)


def test_cleanup(web_scraper, mock_browser_client):
    """Test cleanup on deletion."""
    web_scraper.browser_client = mock_browser_client
    web_scraper.__del__()  # Call cleanup directly instead of relying on garbage collection
    mock_browser_client.close.assert_called_once()

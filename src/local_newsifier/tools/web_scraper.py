"""Tool for scraping web content with robust error handling."""

import time
from datetime import UTC, datetime
from typing import Optional, Protocol

import requests
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.support.wait import WebDriverWait
    from webdriver_manager.chrome import ChromeDriverManager
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

from ..models.state import AnalysisStatus, NewsAnalysisState


class HttpClient(Protocol):
    """Protocol for HTTP clients."""
    def get(self, url: str) -> str:
        """Get content from URL."""
        pass


class BrowserClient(Protocol):
    """Protocol for browser clients."""
    def get(self, url: str) -> str:
        """Get content from URL using browser."""
        pass


class RequestsHttpClient:
    """Concrete implementation of HttpClient using requests."""
    
    def __init__(self, user_agent: str):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": user_agent})
        
    def get(self, url: str) -> str:
        response = self.session.get(url, timeout=30)
        response.raise_for_status()
        return response.text


class SeleniumBrowserClient:
    """Concrete implementation of BrowserClient using Selenium."""
    
    def __init__(self, user_agent: str):
        self.user_agent = user_agent
        self._driver = None
        
    def get(self, url: str) -> str:
        driver = self._get_driver()
        driver.get(url)
        
        # Wait for content to load
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "article"))
                or EC.presence_of_element_located((By.TAG_NAME, "main"))
                or EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
        except Exception:
            # If waiting fails, just get what we have
            pass
            
        time.sleep(2)  # Give JS a chance to finish
        return driver.page_source
        
    def _get_driver(self):
        if self._driver is None:
            if not SELENIUM_AVAILABLE:
                raise ValueError("Selenium is not available")
                
            options = Options()
            options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument(f"user-agent={self.user_agent}")
            
            service = Service(ChromeDriverManager().install())
            self._driver = webdriver.Chrome(service=service, options=options)
        return self._driver
        
    def close(self):
        if self._driver:
            self._driver.quit()


class ArticleExtractor:
    """Extracts article content from HTML."""
    
    def extract(self, html_content: str) -> str:
        """Extract main article text from HTML content."""
        print("Starting content extraction...")
        soup = BeautifulSoup(html_content, "html.parser")

        # Try to find the main article content
        content = None

        # Strategy 1: Look for article tag with story class or data attribute
        print("Trying strategy 1: article tag with story class...")
        content = soup.find(
            "article", class_=lambda x: x and "story" in x.lower()
        ) or soup.find("article", attrs={"data-testid": "story"})

        # Strategy 2: Look for article tag with most paragraphs
        if not content:
            print("Trying strategy 2: article tag with most paragraphs...")
            articles = soup.find_all("article")
            if articles:
                content = max(articles, key=lambda x: len(x.find_all("p")))

        # Strategy 3: Look for main content area with article
        if not content:
            print("Trying strategy 3: main content area...")
            main = soup.find("main")
            if main:
                content = main.find("article") or main

        # Strategy 4: Look for div with article-like content
        if not content:
            print("Trying strategy 4: div with article-like content...")
            for div in soup.find_all("div", class_=True):
                if any(
                    term in " ".join(div.get("class", [])).lower()
                    for term in ["article", "story", "content"]
                ):
                    content = div
                    break

        if not content:
            print("No article content found")
            raise ValueError("No article content found")

        print("Found content container, cleaning up...")
        # Remove navigation, related articles, and other non-content elements
        for element in content.find_all(["nav", "aside", "footer"]):
            element.decompose()

        for element in content.find_all(
            class_=lambda x: x
            and any(
                term in x.lower()
                for term in [
                    "related",
                    "recommended",
                    "navigation",
                    "footer",
                    "header",
                    "sidebar",
                    "newsletter",
                    "subscription",
                    "ad",
                    "promo",
                    "social",
                    "share",
                    "menu",
                ]
            )
        ):
            element.decompose()

        # Get all text blocks that look like article content
        print("Extracting text blocks...")
        text_blocks = []
        for p in content.find_all(["p", "h1", "h2", "h3"], recursive=True):
            text = p.get_text().strip()
            # Only include substantial paragraphs that don't look like navigation
            # Don't apply length check to headlines
            if (
                (p.name in ["h1", "h2", "h3"] or len(text) > 30)
                and not any(  # Reduced minimum length to catch headlines
                    term in text.lower()
                    for term in [
                        "subscribe",
                        "sign up",
                        "newsletter",
                        "advertisement",
                        "read more",
                        "click here",
                        "follow us",
                        "share this",
                        "related stories",
                        "recommended for you",
                        "trending now",
                        "latest news",
                        "breaking news",
                        "top stories",
                        "cookie",
                        "privacy policy",
                        "terms of service",
                        "contact us",
                    ]
                )
                and not text.endswith("news")
                and not text.endswith("sports")  # Filter out category labels
                and not text.endswith("entertainment")
            ):
                text_blocks.append(text)

        if not text_blocks:
            print("No text blocks found after filtering")
            raise ValueError("No text content found in article")

        print(f"Found {len(text_blocks)} text blocks")
        return "\n\n".join(text_blocks)


class WebScraperTool:
    """Tool for scraping web content with robust error handling."""

    DEFAULT_USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    )

    def __init__(
        self,
        http_client: Optional[HttpClient] = None,
        browser_client: Optional[BrowserClient] = None,
        content_extractor: Optional[ArticleExtractor] = None,
        user_agent: Optional[str] = None,
    ):
        """
        Initialize the scraper.

        Args:
            http_client: Optional HTTP client implementation (for testing)
            browser_client: Optional browser client implementation (for testing)
            content_extractor: Optional content extractor implementation (for testing)
            user_agent: Optional custom user agent
        """
        self.user_agent = user_agent or self.DEFAULT_USER_AGENT
        
        # Use provided implementations or create default ones
        self.http_client = http_client or RequestsHttpClient(self.user_agent)
        self.browser_client = browser_client or SeleniumBrowserClient(self.user_agent)
        self.content_extractor = content_extractor or ArticleExtractor()

    def __del__(self):
        """Clean up browser client if it exists."""
        if hasattr(self.browser_client, 'close'):
            self.browser_client.close()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.1, min=0, max=0.2),
        reraise=True,
    )
    def _fetch_url(self, url: str) -> str:
        """Fetch URL content with retries and error handling."""
        print(f"Attempting to fetch URL: {url}")
        try:
            # First try with HTTP client
            html_content = self.http_client.get(url)

            # Check if we got a 404-like page
            if any(
                term in html_content.lower()
                for term in [
                    "404 not found",
                    "page not found",
                    "article not found",
                    "content no longer available",
                    "article has expired",
                    "subscription required",
                    "please subscribe",
                ]
            ):
                print("Found 404-like content in response")
                print("Trying with browser client...")
                return self.browser_client.get(url)

            print("Successfully fetched with HTTP client")
            return html_content
            
        except requests.exceptions.RequestException as e:
            print(f"Request exception: {str(e)}")
            print("Trying with browser client...")
            try:
                return self.browser_client.get(url)
            except Exception as browser_e:
                # If both clients fail, it's a network error
                raise requests.exceptions.RequestException(str(browser_e))

    def scrape(self, state: NewsAnalysisState) -> NewsAnalysisState:
        """
        Scrape article content and update state.

        Args:
            state: Current pipeline state

        Returns:
            Updated state
        """
        try:
            state.status = AnalysisStatus.SCRAPING
            state.add_log(f"Starting scrape of URL: {state.target_url}")

            try:
                html_content = self._fetch_url(state.target_url)
                state.scraped_text = self.content_extractor.extract(html_content)
                state.scraped_at = datetime.now(UTC)
                state.status = AnalysisStatus.SCRAPE_SUCCEEDED
                state.add_log("Successfully scraped article content")
            except requests.exceptions.RequestException as e:
                state.status = AnalysisStatus.SCRAPE_FAILED_NETWORK
                state.set_error("scraping", e)
                state.add_log(f"Network error during scraping: {str(e)}")
                raise
            except Exception as e:
                state.status = AnalysisStatus.SCRAPE_FAILED_PARSING
                state.set_error("scraping", e)
                state.add_log(f"Error during scraping: {str(e)}")
                raise

        except Exception:
            # Re-raise the exception after setting the state
            raise

        return state

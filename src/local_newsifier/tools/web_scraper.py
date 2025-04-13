"""Tool for scraping web content with robust error handling."""

import time
from datetime import UTC, datetime
from typing import Optional
from unittest.mock import MagicMock

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


class WebScraperTool:
    """Tool for scraping web content with robust error handling."""

    def __init__(
        self, 
        user_agent: Optional[str] = None,
        use_selenium: bool = False,
        test_mode: bool = False
    ):
        """
        Initialize the scraper.

        Args:
            user_agent: Optional custom user agent
            use_selenium: Whether to use Selenium for fetching
            test_mode: Whether to run in test mode
        """
        self.user_agent = user_agent or (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": self.user_agent})
        
        self.use_selenium = use_selenium and SELENIUM_AVAILABLE
        self.driver = None
        
        if test_mode:
            # In test mode, don't actually set up Selenium
            if self.use_selenium:
                self.driver = MagicMock()
        elif self.use_selenium:
            self._setup_selenium()

    def _setup_selenium(self):
        """Set up Selenium WebDriver if not already done."""
        if not SELENIUM_AVAILABLE:
            print("Selenium not available - falling back to requests")
            return
            
        if self.driver is None:
            options = Options()
            options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument(f"user-agent={self.user_agent}")
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)

    def __del__(self):
        """Clean up Selenium driver if it exists."""
        if self.driver is not None:
            try:
                self.driver.quit()
            except Exception:
                pass

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.1, min=0, max=0.2),
        reraise=True,
    )
    def _fetch_url(self, url: str) -> str:
        """Fetch URL content with retries and error handling."""
        print(f"Attempting to fetch URL: {url}")
        try:
            # First try with requests
            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            # Check if we got a 404-like page
            if any(
                term in response.text.lower()
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
                if not self.use_selenium:
                    raise requests.exceptions.HTTPError(
                        "Page appears to be a 404 or requires subscription"
                    )
                print("Trying with Selenium...")
                return self._fetch_with_selenium(url)

            print("Successfully fetched with requests")
            return response.text
            
        except requests.exceptions.RequestException as e:
            print(f"Request exception: {str(e)}")
            if self.use_selenium:
                print("Trying with Selenium...")
                return self._fetch_with_selenium(url)
            if isinstance(e, requests.exceptions.HTTPError):
                if e.response is not None:
                    if e.response.status_code == 404:
                        raise ValueError(f"Article not found (404): {url}")
                    elif e.response.status_code == 403:
                        raise ValueError(
                            f"Access denied (403) - may require subscription: {url}"
                        )
                    elif e.response.status_code == 401:
                        raise ValueError(f"Authentication required (401): {url}")
            raise ValueError(f"Failed to fetch URL: {str(e)}")

    def _fetch_with_selenium(self, url: str) -> str:
        """Fetch URL using Selenium for JavaScript-heavy pages."""
        if not SELENIUM_AVAILABLE:
            raise ValueError("Selenium is not available")
            
        if self.driver is None:
            self._setup_selenium()
            
        if self.driver is None:
            raise ValueError("Failed to initialize Selenium WebDriver")
            
        print("Fetching with Selenium...")
        self.driver.get(url)
        
        # Wait for content to load
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "article"))
                or EC.presence_of_element_located((By.TAG_NAME, "main"))
                or EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
        except Exception:
            # If waiting fails, just get what we have
            pass
            
        time.sleep(2)  # Give JS a chance to finish
        return self.driver.page_source

    def extract_article_text(self, html_content: str) -> str:
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

            html_content = self._fetch_url(state.target_url)
            state.scraped_text = self.extract_article_text(html_content)
            state.scraped_at = datetime.now(UTC)
            state.status = AnalysisStatus.SCRAPE_SUCCEEDED
            state.add_log("Successfully scraped article content")

        except Exception as e:
            if isinstance(e, requests.exceptions.RequestException):
                state.status = AnalysisStatus.SCRAPE_FAILED_NETWORK
            elif isinstance(e, ValueError) and "404" in str(e):
                state.status = AnalysisStatus.SCRAPE_FAILED_NETWORK
            else:
                state.status = AnalysisStatus.SCRAPE_FAILED_PARSING

            state.set_error("scraping", e)
            state.add_log(f"Error during scraping: {str(e)}")
            raise

        return state

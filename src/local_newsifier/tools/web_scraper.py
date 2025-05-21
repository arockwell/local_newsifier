import time
from datetime import UTC, datetime
from typing import Dict, Optional, Any

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from tenacity import retry, stop_after_attempt, wait_exponential
from webdriver_manager.chrome import ChromeDriverManager
from fastapi import Depends
from fastapi_injectable import injectable

# Common phrases indicating that an article was not found or is behind a paywall
NOT_FOUND_PHRASES = [
    "404 not found",
    "page not found",
    "article not found",
    "content no longer available",
    "article has expired",
    "subscription required",
    "please subscribe",
]

from ..models.state import AnalysisStatus, NewsAnalysisState


@injectable(use_cache=False)
class WebScraperTool:
    """Tool for scraping web content with robust error handling."""

    def __init__(
        self,
        session: Any = None,
        web_driver: Any = None,
        user_agent: Optional[str] = None
    ):
        """Initialize the scraper with injectable dependencies.

        Args:
            session: Optional HTTP session for making requests (injected)
            web_driver: Optional Selenium WebDriver (injected)
            user_agent: Optional custom user agent string
        """
        self.user_agent = user_agent or (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )

        # Use injected session or create a new one for backward compatibility
        self.session = session
        if self.session is None:
            self.session = requests.Session()
            self.session.headers.update({"User-Agent": self.user_agent})

        # Set up Chrome options
        self.chrome_options = Options()
        self.chrome_options.add_argument("--headless")  # Run in headless mode
        self.chrome_options.add_argument("--no-sandbox")
        self.chrome_options.add_argument("--disable-dev-shm-usage")
        self.chrome_options.add_argument(f"user-agent={self.user_agent}")

        # Use injected driver or initialize as None
        self.driver = web_driver

    def __del__(self):
        """Cleanup method to ensure WebDriver is properly closed."""
        if self.driver is not None:
            self.driver.quit()

    def _get_driver(self):
        """Get or create a WebDriver instance.

        Returns injected driver if available, otherwise creates a new one.
        This provides backward compatibility with code that doesn't use dependency injection.
        """
        if self.driver is None:
            try:
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=self.chrome_options)
            except Exception as e:
                print(f"Error initializing WebDriver: {str(e)}")
                raise RuntimeError(f"Failed to initialize WebDriver: {str(e)}")
        return self.driver

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True,
    )
    def _fetch_url(self, url: str) -> str:
        """Fetch URL content with retries and error handling."""
        print(f"Attempting to fetch URL: {url}")
        try:
            # First try with requests
            print("Trying with requests...")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            # Check if we got a 404-like page
            if any(term in response.text.lower() for term in NOT_FOUND_PHRASES):
                print("Found 404-like content in response")
                raise requests.exceptions.HTTPError(
                    "Page appears to be a 404 or requires subscription"
                )

            print("Successfully fetched with requests")
            return response.text
        except requests.exceptions.HTTPError as e:
            print(f"HTTP error: {str(e)}")
            if e.response is not None and e.response.status_code == 404:
                raise ValueError(f"Article not found (404): {url}")
            elif e.response is not None and e.response.status_code == 403:
                raise ValueError(
                    f"Access denied (403) - may require subscription: {url}"
                )
            elif e.response is not None and e.response.status_code == 401:
                raise ValueError(f"Authentication required (401): {url}")
            raise ValueError(f"HTTP error occurred: {str(e)}")
        except requests.exceptions.RequestException as e:
            print(f"Request exception: {str(e)}")
            print("Trying with Selenium...")
            # If requests fails, try with Selenium
            driver = self._get_driver()
            try:
                driver.get(url)

                # Wait for article content to load
                wait = WebDriverWait(driver, 10)
                article = wait.until(
                    EC.presence_of_element_located((By.TAG_NAME, "article"))
                )

                # Wait a bit more for dynamic content
                time.sleep(2)

                # Check for 404-like content
                page_text = driver.page_source.lower()
                if any(term in page_text for term in NOT_FOUND_PHRASES):
                    print("Found 404-like content in Selenium response")
                    raise ValueError(
                        "Page appears to be a 404 or requires subscription"
                    )

                print("Successfully fetched with Selenium")
                return driver.page_source
            except Exception as selenium_error:
                print(f"Selenium error: {str(selenium_error)}")
                raise ValueError(
                    f"Failed to fetch URL with both methods: {str(e)} and {str(selenium_error)}"
                )

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
            if (
                len(text) > 30
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

    def scrape_url(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Scrape article content from a URL.
        
        Args:
            url: URL to scrape
            
        Returns:
            Dictionary with scraped content or None if scraping failed
        """
        try:
            print(f"Starting scrape of URL: {url}")
            
            html_content = self._fetch_url(url)
            article_text = self.extract_article_text(html_content)
            
            # Extract title from HTML
            soup = BeautifulSoup(html_content, "html.parser")
            title = soup.title.string if soup.title else "Untitled Article"
            
            # Clean up title
            title = title.replace(" | Latest News", "").replace(" - Breaking News", "")
            
            return {
                "title": title,
                "content": article_text,
                "published_at": datetime.now(UTC),
                "url": url
            }
            
        except Exception as e:
            print(f"Error scraping URL {url}: {str(e)}")
            return None
    
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
            article_text = self.extract_article_text(html_content)

            state.scraped_text = article_text
            state.scraped_at = datetime.now(UTC)
            state.status = AnalysisStatus.SCRAPE_SUCCEEDED
            state.add_log("Successfully scraped article content")

        except requests.exceptions.RequestException as e:
            state.status = AnalysisStatus.SCRAPE_FAILED_NETWORK
            state.set_error("scraping", e)
            state.add_log(f"Network error during scraping: {str(e)}")
            raise

        except (ValueError, AttributeError) as e:
            state.status = AnalysisStatus.SCRAPE_FAILED_PARSING
            state.set_error("scraping", e)
            state.add_log(f"Parsing error during scraping: {str(e)}")
            raise

        except Exception as e:
            state.status = AnalysisStatus.SCRAPE_FAILED_PARSING
            state.set_error("scraping", e)
            state.add_log(f"Unexpected error during scraping: {str(e)}")
            raise

        return state

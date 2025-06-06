"""
RSS Parser Tool for extracting URLs and titles from RSS feeds.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from xml.etree import ElementTree

import requests
from dateutil import parser as date_parser
from fastapi_injectable import injectable
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class RSSItem(BaseModel):
    """Model for RSS feed items."""

    title: str
    url: str
    published: Optional[datetime] = None
    description: Optional[str] = None


@injectable(use_cache=False)
class RSSParser:
    """Tool for parsing RSS feeds and extracting content."""

    def __init__(
        self,
        cache_file: Optional[str] = None,
        cache_dir: Optional[str] = None,
        request_timeout: int = 30,
        user_agent: Optional[str] = None,
    ):
        """
        Initialize the RSS parser.

        Args:
            cache_file: Optional path to a JSON file to cache processed URLs
            cache_dir: Optional directory for storing cache files (used if cache_file is None)
            request_timeout: Timeout in seconds for HTTP requests
            user_agent: Custom user agent for HTTP requests
        """
        # If cache_file is not specified but cache_dir is, create a default cache file path
        if cache_file is None and cache_dir is not None:
            cache_path = Path(cache_dir)
            cache_path.mkdir(exist_ok=True, parents=True)
            cache_file = str(cache_path / "rss_urls.json")

        self.cache_file = cache_file
        self.request_timeout = request_timeout
        self.user_agent = user_agent or "Local Newsifier RSS Parser"
        self.processed_urls = self._load_cache() if cache_file else set()

    def _load_cache(self) -> set:
        """Load processed URLs from cache file."""
        if not self.cache_file:
            return set()

        cache_path = Path(self.cache_file)
        if not cache_path.exists():
            return set()

        try:
            with open(cache_path, "r") as f:
                return set(json.load(f))
        except Exception as e:
            logger.error(f"Error loading cache file: {e}")
            return set()

    def _save_cache(self):
        """Save processed URLs to cache file."""
        if not self.cache_file:
            return

        try:
            with open(self.cache_file, "w") as f:
                json.dump(list(self.processed_urls), f)
        except Exception as e:
            logger.error(f"Error saving cache file: {e}")

    def _get_element_text(self, entry: ElementTree.Element, *names: str) -> Optional[str]:
        """Get text from the first matching element."""
        for name in names:
            elem = entry.find(name)
            if elem is not None and elem.text:
                return elem.text
        return None

    def parse_feed(self, feed_url: str) -> List[RSSItem]:
        """
        Parse an RSS feed and extract items.

        Args:
            feed_url: URL of the RSS feed to parse

        Returns:
            List of RSSItem objects containing the feed content
        """
        try:
            # Fetch the feed with timeout and user-agent
            headers = {"User-Agent": self.user_agent}
            response = requests.get(feed_url, headers=headers, timeout=self.request_timeout)
            response.raise_for_status()

            # Parse the XML
            root = ElementTree.fromstring(response.content)

            # Handle both RSS and Atom feeds
            if root.tag.endswith("rss"):
                entries = root.findall(".//item")
            elif root.tag.endswith("feed"):  # Atom feed
                entries = root.findall(".//{http://www.w3.org/2005/Atom}entry")
            else:
                entries = []

            if not entries:
                logger.error(f"No entries found in feed: {feed_url}")
                return []

            items = []
            for entry in entries:
                try:
                    # Extract title
                    title = (
                        self._get_element_text(entry, "title", "{http://www.w3.org/2005/Atom}title")
                        or "No title"
                    )

                    # Extract URL
                    url = None
                    if root.tag.endswith("rss"):
                        url = self._get_element_text(entry, "link")
                    else:  # Atom feed
                        link_elem = entry.find("{http://www.w3.org/2005/Atom}link")
                        if link_elem is not None:
                            url = link_elem.get("href")

                    if not url:
                        continue

                    # Extract published date
                    published = None
                    date_text = self._get_element_text(
                        entry,
                        "pubDate",
                        "published",
                        "{http://www.w3.org/2005/Atom}published",
                    )
                    if date_text:
                        try:
                            published = date_parser.parse(date_text)
                        except Exception as e:
                            logger.warning(f"Could not parse date: {e}")

                    # Extract description
                    description = self._get_element_text(
                        entry,
                        "description",
                        "summary",
                        "{http://www.w3.org/2005/Atom}summary",
                    )

                    item = RSSItem(
                        title=title,
                        url=url,
                        published=published,
                        description=description,
                    )

                    items.append(item)

                except Exception as e:
                    logger.error(f"Error parsing entry in feed {feed_url}: {e}")
                    continue

            return items
        except Exception as e:
            logger.error(f"Error parsing feed {feed_url}: {e}")
            return []

    def get_new_urls(self, feed_url: str) -> List[RSSItem]:
        """
        Get only new URLs from a feed that haven't been processed before.

        Args:
            feed_url: URL of the RSS feed to parse

        Returns:
            List of RSSItem objects containing only new content
        """
        items = self.parse_feed(feed_url)
        new_items = [item for item in items if item.url not in self.processed_urls]

        # Update cache with new URLs
        self.processed_urls.update(item.url for item in new_items)
        if self.cache_file:
            self._save_cache()

        return new_items


def get_parser_instance() -> RSSParser:
    """
    Get an RSSParser instance safely.

    This function handles both production and test environments:
    - In production, gets the parser from the fastapi-injectable provider
    - In tests, creates a new parser instance if the provider is not available

    Returns:
        An RSSParser instance
    """
    try:
        # Try to get the parser from the injectable provider
        from local_newsifier.di.providers import get_rss_parser as get_injectable_parser

        return get_injectable_parser()
    except (ImportError, RuntimeError):
        # Fall back to creating a new instance in test environments
        return RSSParser()


def parse_rss_feed(feed_url: str) -> Dict[str, Any]:
    """
    Parse an RSS feed and return the content in a dictionary format.

    Args:
        feed_url: URL of the RSS feed to parse

    Returns:
        Dictionary containing feed title and entries
    """
    logger.info(f"Parsing RSS feed: {feed_url}")

    try:
        # Get parser instance in a test-friendly way
        parser = get_parser_instance()

        # Use the parser to get items
        items = parser.parse_feed(feed_url)

        # Extract feed title (use first item's title as fallback for feed title)
        feed_title = "Unknown Feed"
        if items:
            feed_title = f"Feed containing {items[0].title}"

        # Convert items to dictionary format expected by tasks
        entries = []
        for item in items:
            entry = {
                "title": item.title,
                "link": item.url,
                "description": item.description or "",
                "published": item.published.isoformat() if item.published else None,
            }
            entries.append(entry)

        return {
            "title": feed_title,
            "feed_url": feed_url,
            "entries": entries,
        }
    except Exception as e:
        logger.error(f"Error parsing RSS feed {feed_url}: {str(e)}")
        return {"title": "Error parsing feed", "feed_url": feed_url, "entries": [], "error": str(e)}

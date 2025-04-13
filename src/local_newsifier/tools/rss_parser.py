"""
RSS Parser Tool for extracting URLs and titles from RSS feeds.
"""

import logging
from datetime import datetime
from typing import List, Optional
from xml.etree import ElementTree

import requests
from dateutil import parser as date_parser
from pydantic import BaseModel

from ..repositories.rss_cache_repository import RSSCacheRepository

logger = logging.getLogger(__name__)


class RSSItem(BaseModel):
    """Model for RSS feed items."""

    title: str
    url: str
    published: Optional[datetime] = None
    description: Optional[str] = None


class RSSParser:
    """Tool for parsing RSS feeds and extracting content."""

    def __init__(self, cache_repository: RSSCacheRepository):
        """
        Initialize the RSS parser.

        Args:
            cache_repository: Repository for managing processed URLs
        """
        self.cache_repository = cache_repository

    def _get_element_text(
        self, entry: ElementTree.Element, *names: str
    ) -> Optional[str]:
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
            # Fetch the feed
            response = requests.get(feed_url)
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
                        self._get_element_text(
                            entry, "title", "{http://www.w3.org/2005/Atom}title"
                        )
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
        urls = [item.url for item in items]
        new_urls = self.cache_repository.get_new_urls(urls, feed_url)
        
        # Filter items to only include new URLs
        new_items = [item for item in items if item.url in new_urls]
        
        # Update cache with new URLs
        for url in new_urls:
            self.cache_repository.add_processed_url(url, feed_url)

        return new_items

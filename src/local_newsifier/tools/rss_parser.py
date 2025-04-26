"""
RSS Parser Tool for extracting URLs and titles from RSS feeds.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
from xml.etree import ElementTree

import requests
from dateutil import parser as date_parser
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class RSSItem(BaseModel):
    """Model for RSS feed items."""

    title: str
    url: str
    published: Optional[datetime] = None
    description: Optional[str] = None


class RSSParser:
    """Tool for parsing RSS feeds and extracting content."""

    def __init__(self, cache_file: Optional[str] = None):
        """
        Initialize the RSS parser.

        Args:
            cache_file: Optional path to a JSON file to cache processed URLs
        """
        self.cache_file = cache_file
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
            logger.debug(f"Fetching RSS feed from URL: {feed_url}")
            response = requests.get(feed_url)
            response.raise_for_status()
            logger.debug(f"Successfully fetched feed. Status code: {response.status_code}")
            
            # Parse the XML
            logger.debug("Parsing XML response")
            root = ElementTree.fromstring(response.content)
            logger.debug(f"Root tag: {root.tag}")
            
            # Log feed namespaces for debugging
            namespaces = root.attrib
            logger.debug(f"Feed namespaces: {namespaces}")

            # Handle both RSS and Atom feeds
            entries = []
            if root.tag.endswith("rss"):
                logger.debug("Detected RSS format feed")
                entries = root.findall(".//item")
                logger.debug(f"Found {len(entries)} items using .//item")
                
                # Try alternative path if no entries found
                if not entries:
                    logger.debug("Trying alternative XPath for RSS items")
                    entries = root.findall("./channel/item")
                    logger.debug(f"Found {len(entries)} items using ./channel/item")
            elif root.tag.endswith("feed"):  # Atom feed
                logger.debug("Detected Atom format feed")
                entries = root.findall(".//{http://www.w3.org/2005/Atom}entry")
                logger.debug(f"Found {len(entries)} entries")
            else:
                logger.debug(f"Unknown feed format with root tag: {root.tag}")
                entries = []

            if not entries:
                logger.error(f"No entries found in feed: {feed_url}")
                # Log a sample of the XML for debugging
                xml_sample = response.content[:500].decode('utf-8', errors='replace')
                logger.debug(f"Sample of XML content: {xml_sample}...")
                return []

            items = []
            for i, entry in enumerate(entries):
                try:
                    logger.debug(f"Processing entry {i+1}/{len(entries)}")
                    # Extract title
                    title = (
                        self._get_element_text(
                            entry, "title", "{http://www.w3.org/2005/Atom}title"
                        )
                        or "No title"
                    )
                    logger.debug(f"Extracted title: {title}")

                    # Extract URL
                    url = None
                    if root.tag.endswith("rss"):
                        url = self._get_element_text(entry, "link")
                        logger.debug(f"RSS link extraction result: {url}")
                    else:  # Atom feed
                        link_elem = entry.find("{http://www.w3.org/2005/Atom}link")
                        if link_elem is not None:
                            url = link_elem.get("href")
                            logger.debug(f"Atom link extraction result: {url}")

                    if not url:
                        logger.warning(f"No URL found for entry with title: {title}, skipping")
                        continue

                    # Extract published date
                    published = None
                    date_text = self._get_element_text(
                        entry,
                        "pubDate",
                        "published",
                        "{http://www.w3.org/2005/Atom}published",
                    )
                    logger.debug(f"Date text extracted: {date_text}")
                    if date_text:
                        try:
                            published = date_parser.parse(date_text)
                            logger.debug(f"Parsed date: {published}")
                        except Exception as e:
                            logger.warning(f"Could not parse date: {e}")

                    # Extract description
                    description = self._get_element_text(
                        entry,
                        "description",
                        "summary",
                        "{http://www.w3.org/2005/Atom}summary",
                    )
                    logger.debug(f"Description extracted: {description[:50]}..." if description and len(description) > 50 else description)

                    item = RSSItem(
                        title=title,
                        url=url,
                        published=published,
                        description=description,
                    )
                    logger.debug(f"Created RSSItem: {item}")

                    items.append(item)

                except Exception as e:
                    logger.error(f"Error parsing entry in feed {feed_url}: {e}")
                    logger.debug(f"Entry that caused the error: {ElementTree.tostring(entry)[:200]}")
                    continue

            logger.info(f"Successfully parsed {len(items)} items from feed: {feed_url}")
            return items
        except Exception as e:
            logger.error(f"Error parsing feed {feed_url}: {e}")
            import traceback
            logger.debug(f"Traceback: {traceback.format_exc()}")
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


# Global parser instance
_parser = RSSParser()


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
        # Use the parser to get items
        items = _parser.parse_feed(feed_url)
        logger.debug(f"Received {len(items)} items from RSSParser.parse_feed")
        
        # Extract feed title (use first item's title as fallback for feed title)
        feed_title = "Unknown Feed"
        if items:
            feed_title = f"Feed containing {items[0].title}"
            logger.debug(f"Set feed title to: {feed_title}")
            
        # Convert items to dictionary format expected by tasks
        entries = []
        for i, item in enumerate(items):
            entry = {
                "title": item.title,
                "link": item.url,
                "description": item.description or "",
                "published": item.published.isoformat() if item.published else None,
            }
            logger.debug(f"Converted item {i+1} to dictionary format")
            entries.append(entry)
            
        result = {
            "title": feed_title,
            "feed_url": feed_url,
            "entries": entries,
        }
        logger.info(f"Returning parsed feed with {len(entries)} entries")
        return result
    except Exception as e:
        logger.error(f"Error parsing RSS feed {feed_url}: {str(e)}")
        import traceback
        logger.debug(f"Traceback: {traceback.format_exc()}")
        return {
            "title": "Error parsing feed",
            "feed_url": feed_url,
            "entries": [],
            "error": str(e)
        }

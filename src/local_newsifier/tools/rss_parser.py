"""
RSS Parser Tool for extracting URLs and titles from RSS feeds.
"""

import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
from xml.etree import ElementTree
from xml.etree.ElementTree import ParseError

import requests
from dateutil import parser as date_parser
from pydantic import BaseModel
from requests.exceptions import RequestException, Timeout, HTTPError, ConnectionError

logger = logging.getLogger(__name__)


class RSSParsingError(Exception):
    """Exception raised for RSS parsing errors."""
    
    def __init__(self, message: str, feed_url: str, error_type: str, original_error: Optional[Exception] = None):
        """
        Initialize with error context.
        
        Args:
            message: Error message
            feed_url: URL of the RSS feed that failed
            error_type: Type of error (network, parsing, etc.)
            original_error: Original exception that caused this error
        """
        self.feed_url = feed_url
        self.error_type = error_type
        self.original_error = original_error
        self.timestamp = datetime.now()
        super().__init__(message)


class RSSItem(BaseModel):
    """Model for RSS feed items."""

    title: str
    url: str
    published: Optional[datetime] = None
    description: Optional[str] = None


class RSSParser:
    """Tool for parsing RSS feeds and extracting content."""

    def __init__(self, cache_file: Optional[str] = None, max_retries: int = 3):
        """
        Initialize the RSS parser.

        Args:
            cache_file: Optional path to a JSON file to cache processed URLs
            max_retries: Maximum number of retry attempts for network errors
        """
        self.cache_file = cache_file
        self.max_retries = max_retries
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

    def _fetch_feed_with_retry(self, feed_url: str) -> Tuple[bytes, bool]:
        """
        Fetch the feed with retry logic for transient errors.
        
        Args:
            feed_url: URL of the feed to fetch
            
        Returns:
            Tuple of (content, success_flag)
            
        Raises:
            RSSParsingError: If the feed couldn't be fetched after retries
        """
        for attempt in range(1, self.max_retries + 1):
            try:
                response = requests.get(feed_url, timeout=30)
                response.raise_for_status()
                return response.content, True
            except Timeout as e:
                logger.warning(f"Timeout fetching feed {feed_url} (attempt {attempt}/{self.max_retries}): {e}")
                if attempt < self.max_retries:
                    # Exponential backoff
                    wait_time = 2 ** attempt
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    raise RSSParsingError(
                        f"Timeout fetching feed after {self.max_retries} attempts", 
                        feed_url=feed_url,
                        error_type="network_timeout",
                        original_error=e
                    )
            except HTTPError as e:
                status_code = e.response.status_code if hasattr(e, 'response') else "unknown"
                # Don't retry client errors (4xx) except for 429 (Too Many Requests)
                if 400 <= status_code < 500 and status_code != 429:
                    raise RSSParsingError(
                        f"HTTP error {status_code} fetching feed", 
                        feed_url=feed_url,
                        error_type=f"http_{status_code}",
                        original_error=e
                    )
                logger.warning(f"HTTP error fetching feed {feed_url} (attempt {attempt}/{self.max_retries}): {e}")
                if attempt < self.max_retries:
                    wait_time = 2 ** attempt
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    raise RSSParsingError(
                        f"HTTP error fetching feed after {self.max_retries} attempts", 
                        feed_url=feed_url,
                        error_type="network_http_error",
                        original_error=e
                    )
            except ConnectionError as e:
                logger.warning(f"Connection error fetching feed {feed_url} (attempt {attempt}/{self.max_retries}): {e}")
                if attempt < self.max_retries:
                    wait_time = 2 ** attempt
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    raise RSSParsingError(
                        f"Connection error fetching feed after {self.max_retries} attempts", 
                        feed_url=feed_url,
                        error_type="network_connection_error",
                        original_error=e
                    )
            except RequestException as e:
                logger.warning(f"Request error fetching feed {feed_url} (attempt {attempt}/{self.max_retries}): {e}")
                if attempt < self.max_retries:
                    wait_time = 2 ** attempt
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    raise RSSParsingError(
                        f"Request error fetching feed after {self.max_retries} attempts", 
                        feed_url=feed_url,
                        error_type="network_request_error",
                        original_error=e
                    )
        
        # Should never reach here due to the raises above, but just in case
        raise RSSParsingError(
            f"Failed to fetch feed after {self.max_retries} attempts for unknown reason", 
            feed_url=feed_url,
            error_type="network_unknown_error"
        )

    def parse_feed(self, feed_url: str) -> List[RSSItem]:
        """
        Parse an RSS feed and extract items.

        Args:
            feed_url: URL of the RSS feed to parse

        Returns:
            List of RSSItem objects containing the feed content
            
        Raises:
            RSSParsingError: If the feed couldn't be parsed
        """
        try:
            # Fetch the feed with retry logic
            content, success = self._fetch_feed_with_retry(feed_url)
            if not success:
                return []

            try:
                # Parse the XML
                root = ElementTree.fromstring(content)
            except ParseError as e:
                logger.error(f"XML parsing error in feed {feed_url}: {e}")
                raise RSSParsingError(
                    f"XML parsing error: {str(e)}", 
                    feed_url=feed_url,
                    error_type="xml_parse_error",
                    original_error=e
                )

            # Handle both RSS and Atom feeds
            if root.tag.endswith("rss"):
                entries = root.findall(".//item")
            elif root.tag.endswith("feed"):  # Atom feed
                entries = root.findall(".//{http://www.w3.org/2005/Atom}entry")
            else:
                entries = []

            if not entries:
                logger.error(f"No entries found in feed: {feed_url}")
                raise RSSParsingError(
                    "No entries found in feed", 
                    feed_url=feed_url,
                    error_type="empty_feed"
                )

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
                        logger.debug(f"Skipping entry without URL in feed {feed_url}")
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
                            logger.warning(f"Could not parse date '{date_text}': {e}")

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

            if not items:
                logger.warning(f"No valid items found in feed: {feed_url}")
                
            return items
            
        except RSSParsingError:
            # Re-raise RSSParsingError exceptions
            raise
        except Exception as e:
            logger.error(f"Unexpected error parsing feed {feed_url}: {e}")
            raise RSSParsingError(
                f"Unexpected error: {str(e)}", 
                feed_url=feed_url,
                error_type="unexpected_error",
                original_error=e
            )

    def get_new_urls(self, feed_url: str) -> List[RSSItem]:
        """
        Get only new URLs from a feed that haven't been processed before.

        Args:
            feed_url: URL of the RSS feed to parse

        Returns:
            List of RSSItem objects containing only new content
        """
        try:
            items = self.parse_feed(feed_url)
            new_items = [item for item in items if item.url not in self.processed_urls]

            # Update cache with new URLs
            self.processed_urls.update(item.url for item in new_items)
            if self.cache_file:
                self._save_cache()

            return new_items
        except RSSParsingError as e:
            logger.error(f"Failed to get new URLs from feed {feed_url}: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error getting new URLs from feed {feed_url}: {e}")
            return []


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
    except RSSParsingError as e:
        # Structured error response for RSS parsing errors
        logger.error(f"RSS parsing error for {feed_url}: {str(e)}")
        return {
            "title": "Error parsing feed",
            "feed_url": feed_url,
            "entries": [],
            "error": {
                "message": str(e),
                "type": e.error_type,
                "timestamp": e.timestamp.isoformat(),
                "feed_url": e.feed_url
            }
        }
    except Exception as e:
        # Generic error fallback
        logger.error(f"Error parsing RSS feed {feed_url}: {str(e)}")
        return {
            "title": "Error parsing feed",
            "feed_url": feed_url,
            "entries": [],
            "error": {
                "message": str(e),
                "type": "unknown_error",
                "timestamp": datetime.now().isoformat(),
                "feed_url": feed_url
            }
        }

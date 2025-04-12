"""
RSS Parser Tool for extracting URLs and titles from RSS feeds.
"""
import feedparser
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
from pathlib import Path
import json
import logging

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
            with open(cache_path, 'r') as f:
                return set(json.load(f))
        except Exception as e:
            logger.error(f"Error loading cache file: {e}")
            return set()
    
    def _save_cache(self):
        """Save processed URLs to cache file."""
        if not self.cache_file:
            return
        
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(list(self.processed_urls), f)
        except Exception as e:
            logger.error(f"Error saving cache file: {e}")
    
    def parse_feed(self, feed_url: str) -> List[RSSItem]:
        """
        Parse an RSS feed and extract items.
        
        Args:
            feed_url: URL of the RSS feed to parse
            
        Returns:
            List of RSSItem objects containing the feed content
        """
        try:
            feed = feedparser.parse(feed_url)
            
            # Check for feed errors
            if getattr(feed, 'bozo', 0) and feed.get('bozo_exception'):
                logger.error(f"Feed error for {feed_url}: {feed.get('bozo_exception')}")
                return []
            
            entries = feed.get('entries', [])
            if not entries:
                logger.error(f"No entries found in feed: {feed_url}")
                return []
            
            items = []
            for entry in entries:
                try:
                    # Extract published date if available
                    published = None
                    if entry.get('published_parsed'):
                        # feedparser returns a time.struct_time, convert to datetime
                        published = datetime(*entry['published_parsed'][:6])
                    
                    item = RSSItem(
                        title=entry.get('title', 'No title'),
                        url=entry.get('link', ''),
                        published=published,
                        description=entry.get('description', None)
                    )
                    
                    # Only add items with valid URLs
                    if item.url:
                        items.append(item)
                    else:
                        logger.warning(f"Skipping entry without URL in feed {feed_url}")
                        
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
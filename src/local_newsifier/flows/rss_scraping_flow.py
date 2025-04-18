"""
Flow for orchestrating RSS feed parsing and web scraping.
"""

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from local_newsifier.models.state import AnalysisStatus, NewsAnalysisState
from local_newsifier.tools.rss_parser import RSSItem, RSSParser
from local_newsifier.tools.web_scraper import WebScraperTool

logger = logging.getLogger(__name__)


class RSSScrapingFlow:
    """Flow for processing RSS feeds and scraping their content."""

    def __init__(self, cache_dir: Optional[str] = None):
        """
        Initialize the RSS scraping flow.

        Args:
            cache_dir: Optional directory to store cache files
        """
        self.cache_dir = Path(cache_dir) if cache_dir else None

        # Initialize tools
        cache_file = self.cache_dir / "rss_urls.json" if self.cache_dir else None
        self.rss_parser = RSSParser(cache_file=str(cache_file) if cache_file else None)
        self.web_scraper = WebScraperTool()

    def process_feed(self, feed_url: str) -> List[NewsAnalysisState]:
        """
        Process an RSS feed by:
        1. Parsing the feed for new URLs
        2. Creating analysis states for new articles
        3. Scraping content for each new article

        Args:
            feed_url: URL of the RSS feed to process

        Returns:
            List of NewsAnalysisState objects for each processed article
        """
        logger.info(f"Processing feed: {feed_url}")

        # Get new articles from feed
        new_items = self.rss_parser.get_new_urls(feed_url)
        if not new_items:
            logger.info("No new articles found in feed")
            return []

        logger.info(f"Found {len(new_items)} new articles")
        results = []

        # Process each new article
        for item in new_items:
            try:
                # Create initial state
                state = NewsAnalysisState(
                    target_url=item.url,
                    status=AnalysisStatus.INITIALIZED,
                    created_at=datetime.now(timezone.utc),
                    last_updated=datetime.now(timezone.utc),
                )
                state.add_log(f"Processing article: {item.title}")

                # Scrape the article
                state = self.web_scraper.scrape(state)
                results.append(state)

            except Exception as e:
                logger.error(f"Error processing article {item.url}: {e}")
                # Create failed state
                state = NewsAnalysisState(
                    target_url=item.url,
                    status=AnalysisStatus.SCRAPE_FAILED_NETWORK,
                    created_at=datetime.now(timezone.utc),
                    last_updated=datetime.now(timezone.utc),
                )
                state.set_error("scraping", e)
                state.add_log(f"Failed to process article: {item.title}")
                results.append(state)

        return results

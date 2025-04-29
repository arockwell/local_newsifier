"""
Flow for orchestrating RSS feed parsing and web scraping.
"""

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Dict

from local_newsifier.models.state import AnalysisStatus, NewsAnalysisState
from local_newsifier.tools.rss_parser import RSSItem, RSSParser
from local_newsifier.tools.web_scraper import WebScraperTool
from local_newsifier.services.article_service import ArticleService
from local_newsifier.services.rss_feed_service import RSSFeedService

# Check if crewai is available
try:
    from crewai import Flow
    has_crewai = True
except ImportError:
    has_crewai = False
    Flow = object  # Use object as base class if crewai is not available

logger = logging.getLogger(__name__)


class RSSScrapingFlow(Flow):
    """Flow for processing RSS feeds and scraping their content."""

    def __init__(
        self,
        rss_feed_service: Optional[RSSFeedService] = None,
        article_service: Optional[ArticleService] = None,
        rss_parser: Optional[RSSParser] = None,
        web_scraper: Optional[WebScraperTool] = None,
        cache_dir: Optional[str] = None
    ):
        """
        Initialize the RSS scraping flow.

        Args:
            rss_feed_service: Service for RSS feed operations
            article_service: Service for article operations
            rss_parser: Tool for parsing RSS feeds
            web_scraper: Tool for scraping web content
            cache_dir: Optional directory to store cache files
        """
        super().__init__()
        self.cache_dir = Path(cache_dir) if cache_dir else None
        
        # Import container here to avoid circular imports
        from local_newsifier.container import container
        
        # Get services from container if not provided
        self.rss_feed_service = rss_feed_service or container.get("rss_feed_service")
        self.article_service = article_service or container.get("article_service")
        
        # Get or create tools from container
        cache_file = self.cache_dir / "rss_urls.json" if self.cache_dir else None
        
        # Get RSSParser from container or create one
        if rss_parser:
            self.rss_parser = rss_parser
        else:
            # Try to get from container first
            parser_tool = container.get("rss_parser_tool")
            if parser_tool is not None:
                self.rss_parser = parser_tool
            else:
                # Fall back to direct creation
                self.rss_parser = RSSParser(
                    cache_file=str(cache_file) if cache_file else None
                )
        
        # Get WebScraperTool from container or use provided one
        self.web_scraper = web_scraper or container.get("web_scraper_tool") or WebScraperTool()

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

"""
Flow for orchestrating RSS feed parsing and web scraping.
"""

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Dict, Callable

from crewai import Flow

from local_newsifier.models.state import AnalysisStatus, NewsAnalysisState
from local_newsifier.tools.rss_parser import RSSItem, RSSParser
from local_newsifier.tools.web_scraper import WebScraperTool
from local_newsifier.services.article_service import ArticleService
from local_newsifier.services.rss_feed_service import RSSFeedService

logger = logging.getLogger(__name__)


class RSSScrapingFlow(Flow):
    """Flow for processing RSS feeds and scraping their content."""

    def __init__(
        self, 
        rss_feed_service: Optional[RSSFeedService] = None,
        article_service: Optional[ArticleService] = None,
        rss_parser: Optional[RSSParser] = None,
        web_scraper: Optional[WebScraperTool] = None,
        cache_dir: Optional[str] = None,
        session_factory: Optional[Callable] = None
    ):
        """
        Initialize the RSS scraping flow.

        Args:
            rss_feed_service: Service for RSS feed operations
            article_service: Service for article operations
            rss_parser: Tool for parsing RSS feeds
            web_scraper: Tool for scraping web content
            cache_dir: Optional directory to store cache files
            session_factory: Function to create database sessions
        """
        super().__init__()
        self.cache_dir = Path(cache_dir) if cache_dir else None
        self.rss_feed_service = rss_feed_service
        self.article_service = article_service
        self.session_factory = session_factory

        # Initialize or use provided tools
        # Backward compatibility for cache_dir parameter
        self.rss_parser = rss_parser
        if self.rss_parser is None:
            cache_file = self.cache_dir / "rss_urls.json" if self.cache_dir else None
            self.rss_parser = RSSParser(
                cache_file=str(cache_file) if cache_file else None,
                cache_dir=str(self.cache_dir) if self.cache_dir else None
            )

        self.web_scraper = web_scraper or WebScraperTool()

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
        
    @classmethod
    def from_container(cls):
        """Legacy factory method for container-based instantiation."""
        from local_newsifier.container import container
        
        return cls(
            rss_feed_service=container.get("rss_feed_service"),
            article_service=container.get("article_service"),
            rss_parser=container.get("rss_parser"),
            web_scraper=container.get("web_scraper_tool"),
            session_factory=container.get("session_factory")
        )
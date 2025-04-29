"""Flow for orchestrating RSS feed parsing and web scraping."""

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Dict, Any

from sqlmodel import Session

from local_newsifier.flows.flow_base import FlowBase
from local_newsifier.di.descriptors import Dependency
from local_newsifier.models.state import NewsAnalysisState
from local_newsifier.tools.rss_parser import RSSItem
from local_newsifier.database.engine import SessionManager

logger = logging.getLogger(__name__)


class RSSScrapingFlow(FlowBase):
    """Flow for processing RSS feeds and scraping their content.
    
    This implementation uses the simplified DI pattern with descriptors
    for cleaner dependency declaration and resolution.
    """
    
    # Define dependencies using descriptors - these will be lazy-loaded when needed
    rss_parser = Dependency()
    scraper = Dependency()
    rss_feed_service = Dependency()
    article_service = Dependency()
    session_factory = Dependency(fallback=SessionManager)
    
    def __init__(
        self,
        container=None,
        session: Optional[Session] = None,
        **explicit_deps
    ):
        """Initialize the RSS scraping flow.
        
        Args:
            container: Optional DI container for resolving dependencies
            session: Optional database session (for direct use)
            **explicit_deps: Explicit dependencies (overrides container)
        """
        # Initialize the FlowBase
        super().__init__(container, **explicit_deps)
            
        self.session = session
    
    def ensure_dependencies(self) -> None:
        """Ensure all required dependencies are available."""
        # Access dependencies to trigger lazy loading
        assert self.rss_feed_service is not None, "RSSFeedService is required"
        assert self.article_service is not None, "ArticleService is required"
        # Other dependencies will be loaded when needed
    
    def process_feed(self, feed_id: int, force_refresh: bool = False) -> Dict[str, Any]:
        """Process a single RSS feed by ID.
        
        Args:
            feed_id: ID of the RSS feed to process
            force_refresh: Whether to process all items regardless of publication date
            
        Returns:
            Dictionary with processing results
        """
        with self.session_factory() as session:
            # Get feed
            feed = self.rss_feed_service.get_feed(session, feed_id)
            
            if not feed:
                raise ValueError(f"RSS feed with ID {feed_id} not found")
            
            # Process feed
            return self._process_feed_internal(session, feed, force_refresh)
    
    def process_all_feeds(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """Process all active RSS feeds.
        
        Args:
            force_refresh: Whether to process all items regardless of publication date
            
        Returns:
            List of dictionaries with processing results for each feed
        """
        results = []
        
        with self.session_factory() as session:
            # Get all active feeds
            feeds = self.rss_feed_service.get_active_feeds(session)
            
            # Process each feed
            for feed in feeds:
                try:
                    result = self._process_feed_internal(session, feed, force_refresh)
                    results.append(result)
                except Exception as e:
                    logger.error(f"Error processing feed {feed.id}: {str(e)}")
                    results.append({
                        "feed_id": feed.id,
                        "feed_url": feed.url,
                        "status": "error",
                        "error": str(e),
                        "items_processed": 0,
                        "items_saved": 0
                    })
        
        return results
    
    def _process_feed_internal(self, session: Session, feed: Any, force_refresh: bool) -> Dict[str, Any]:
        """Internal method to process a feed.
        
        Args:
            session: Database session
            feed: RSS feed object to process
            force_refresh: Whether to process all items regardless of publication date
            
        Returns:
            Dictionary with processing results
        """
        if not self.rss_parser:
            raise ValueError("RSS parser is required")
        
        # Parse feed
        logger.info(f"Processing feed: {feed.url}")
        items = self.rss_parser.parse_feed(feed.url)
        
        if not items:
            logger.warning(f"No items found in feed: {feed.url}")
            return {
                "feed_id": feed.id,
                "feed_url": feed.url,
                "status": "success",
                "items_processed": 0,
                "items_saved": 0,
                "message": "No items found in feed"
            }
        
        # Get last processed date
        last_processed = feed.last_processed_at
        items_saved = 0
        items_processed = 0
        
        # Process items
        for item in items:
            items_processed += 1
            
            # Skip if already processed and not forcing refresh
            if not force_refresh and last_processed and item.published_at and item.published_at <= last_processed:
                logger.debug(f"Skipping already processed item: {item.title}")
                continue
            
            # Skip if missing required fields
            if not item.title or not item.link:
                logger.warning(f"Skipping item missing required fields: {item}")
                continue
            
            try:
                # Process item
                saved = self._process_item(session, feed, item)
                if saved:
                    items_saved += 1
            except Exception as e:
                logger.error(f"Error processing item {item.title}: {str(e)}")
        
        # Update feed processing log
        self.rss_feed_service.create_feed_processing_log(
            session,
            feed_id=feed.id,
            items_processed=items_processed,
            items_saved=items_saved,
            status="success"
        )
        
        # Return results
        return {
            "feed_id": feed.id,
            "feed_url": feed.url,
            "status": "success",
            "items_processed": items_processed,
            "items_saved": items_saved
        }
    
    def _process_item(self, session: Session, feed: Any, item: RSSItem) -> bool:
        """Process a single RSS item.
        
        Args:
            session: Database session
            feed: RSS feed object
            item: RSS item to process
            
        Returns:
            Boolean indicating whether the item was saved
        """
        # Check if article already exists
        existing = self.article_service.get_article_by_url(session, item.link)
        if existing:
            logger.debug(f"Article already exists: {item.title}")
            return False
        
        # Scrape content if needed
        content = item.content
        if not content and self.scraper:
            try:
                scraped_data = self.scraper.scrape_article(item.link)
                if scraped_data and scraped_data.get("content"):
                    content = scraped_data.get("content")
                    
                    # Update publication date if not set
                    if not item.published_at and scraped_data.get("published_at"):
                        item.published_at = scraped_data.get("published_at")
            except Exception as e:
                logger.error(f"Error scraping content for {item.link}: {str(e)}")
        
        # Create article if content available
        if content:
            # Create state
            state = NewsAnalysisState(
                content=content,
                title=item.title,
                url=item.link,
                published_at=item.published_at or datetime.now(timezone.utc)
            )
            
            # Create article
            article = self.article_service.create_article_from_state(session, state)
            
            # Update article source
            self.article_service.update_article_source(
                session,
                article_id=article.id,
                source_id=feed.id,
                source_type="rss"
            )
            
            return True
        
        return False

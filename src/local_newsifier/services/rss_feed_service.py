"""
Service for managing RSS feeds.
This module provides functionality for RSS feed management, including
adding, updating, and processing feeds.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Callable

from sqlmodel import Session

from local_newsifier.crud.rss_feed import rss_feed
from local_newsifier.crud.feed_processing_log import feed_processing_log
from local_newsifier.models.rss_feed import RSSFeed, RSSFeedProcessingLog
from local_newsifier.tools.rss_parser import parse_rss_feed
from local_newsifier.services.article_service import ArticleService

# This will be set later to avoid circular imports
_process_article_task = None

def register_process_article_task(task_func):
    """Register the process_article task function to avoid circular imports.
    
    This function will be called from tasks.py after all imports are complete.
    """
    global _process_article_task
    _process_article_task = task_func

logger = logging.getLogger(__name__)


class RSSFeedService:
    """Service for RSS feed management."""

    def __init__(
        self,
        rss_feed_crud=None,
        feed_processing_log_crud=None,
        article_service=None,
        session_factory=None,
    ):
        """Initialize with dependencies.

        Args:
            rss_feed_crud: CRUD for RSS feeds
            feed_processing_log_crud: CRUD for feed processing logs
            article_service: Service for article management
            session_factory: Factory for database sessions
        """
        self.rss_feed_crud = rss_feed_crud or rss_feed
        self.feed_processing_log_crud = feed_processing_log_crud or feed_processing_log
        self.article_service = article_service
        self.session_factory = session_factory

    def _get_session(self) -> Session:
        """Get a database session."""
        if self.session_factory:
            return self.session_factory()
        from local_newsifier.database.engine import get_session
        return next(get_session())

    def get_feed(self, feed_id: int) -> Optional[Dict[str, Any]]:
        """Get a feed by ID.

        Args:
            feed_id: Feed ID

        Returns:
            Feed data as dict if found, None otherwise
        """
        session = self._get_session()
        feed = self.rss_feed_crud.get(session, id=feed_id)
        if not feed:
            return None
        return self._format_feed_dict(feed)

    def get_feed_by_url(self, url: str) -> Optional[Dict[str, Any]]:
        """Get a feed by URL.

        Args:
            url: Feed URL

        Returns:
            Feed data as dict if found, None otherwise
        """
        session = self._get_session()
        feed = self.rss_feed_crud.get_by_url(session, url=url)
        if not feed:
            return None
        return self._format_feed_dict(feed)

    def list_feeds(
        self, skip: int = 0, limit: int = 100, active_only: bool = False
    ) -> List[Dict[str, Any]]:
        """List feeds with pagination.

        Args:
            skip: Number of items to skip
            limit: Maximum number of items to return
            active_only: Whether to return only active feeds

        Returns:
            List of feed data as dicts
        """
        session = self._get_session()
        if active_only:
            feeds = self.rss_feed_crud.get_active_feeds(session, skip=skip, limit=limit)
        else:
            feeds = self.rss_feed_crud.get_multi(session, skip=skip, limit=limit)
        return [self._format_feed_dict(feed) for feed in feeds]

    def create_feed(self, url: str, name: str, description: Optional[str] = None) -> Dict[str, Any]:
        """Create a new feed.

        Args:
            url: Feed URL
            name: Feed name
            description: Feed description

        Returns:
            Created feed data as dict

        Raises:
            ValueError: If feed with the URL already exists
        """
        session = self._get_session()
        
        # Check if feed already exists
        existing = self.rss_feed_crud.get_by_url(session, url=url)
        if existing:
            raise ValueError(f"Feed with URL '{url}' already exists")
        
        # Create new feed
        new_feed = self.rss_feed_crud.create(
            session,
            obj_in={
                "url": url,
                "name": name,
                "description": description,
                "is_active": True,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
            },
        )
        
        return self._format_feed_dict(new_feed)

    def update_feed(
        self,
        feed_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> Optional[Dict[str, Any]]:
        """Update a feed.

        Args:
            feed_id: Feed ID
            name: New name (optional)
            description: New description (optional)
            is_active: New active status (optional)

        Returns:
            Updated feed data as dict if found, None otherwise
        """
        session = self._get_session()
        
        # Get feed
        feed = self.rss_feed_crud.get(session, id=feed_id)
        if not feed:
            return None
        
        # Prepare update data
        update_data = {"updated_at": datetime.now(timezone.utc)}
        if name is not None:
            update_data["name"] = name
        if description is not None:
            update_data["description"] = description
        if is_active is not None:
            update_data["is_active"] = is_active
        
        # Update feed
        updated = self.rss_feed_crud.update(session, db_obj=feed, obj_in=update_data)
        return self._format_feed_dict(updated)

    def remove_feed(self, feed_id: int) -> Optional[Dict[str, Any]]:
        """Remove a feed.

        Args:
            feed_id: Feed ID

        Returns:
            Removed feed data as dict if found, None otherwise
        """
        session = self._get_session()
        
        # Get feed
        feed = self.rss_feed_crud.get(session, id=feed_id)
        if not feed:
            return None
        
        # Remove feed
        removed = self.rss_feed_crud.remove(session, id=feed_id)
        if not removed:
            return None
        
        return self._format_feed_dict(removed)

    def process_feed(
        self, feed_id: int, task_queue_func: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """Process a feed.

        Args:
            feed_id: Feed ID
            task_queue_func: Function to queue article processing tasks (optional)

        Returns:
            Result information including processed feed and article counts
        """
        session = self._get_session()
        
        # Get feed
        feed = self.rss_feed_crud.get(session, id=feed_id)
        if not feed:
            return {"status": "error", "message": f"Feed with ID {feed_id} not found"}
        
        # Create processing log
        log = self.feed_processing_log_crud.create_processing_started(
            session, feed_id=feed_id
        )
        
        # Parse the RSS feed
        try:
            feed_data = parse_rss_feed(feed.url)
            
            articles_found = len(feed_data.get("entries", []))
            articles_added = 0
            
            # Process each article in the feed
            for entry in feed_data.get("entries", []):
                try:
                    # Create article
                    if self.article_service:
                        # Use injected article service
                        article_id = self.article_service.create_article_from_rss_entry(entry)
                    else:
                        # Create a new instance for direct CLI usage if no service is injected
                        from local_newsifier.services.article_service import ArticleService
                        from local_newsifier.crud.article import article as article_crud
                        from local_newsifier.crud.analysis_result import analysis_result as analysis_result_crud
                        from local_newsifier.database.engine import SessionManager
                        
                        temp_article_service = ArticleService(
                            article_crud=article_crud,
                            analysis_result_crud=analysis_result_crud,
                            entity_service=None,  # Not needed for creating articles from RSS
                            session_factory=lambda: SessionManager()
                        )
                        article_id = temp_article_service.create_article_from_rss_entry(entry)
                    
                    if article_id:
                        # Queue article processing
                        if task_queue_func:
                            task_queue_func(article_id)
                        elif _process_article_task:
                            _process_article_task.delay(article_id)
                        else:
                            logger.warning(f"No task function available to process article {article_id}")
                        articles_added += 1
                except Exception as e:
                    logger.error(f"Error processing article {entry.get('link', 'unknown')}: {str(e)}")
            
            # Update feed last fetched timestamp
            self.rss_feed_crud.update_last_fetched(session, id=feed_id)
            
            # Update processing log
            self.feed_processing_log_crud.update_processing_completed(
                session,
                log_id=log.id,
                status="success",
                articles_found=articles_found,
                articles_added=articles_added,
            )
            
            return {
                "status": "success",
                "feed_id": feed_id,
                "feed_name": feed.name,
                "articles_found": articles_found,
                "articles_added": articles_added,
            }
            
        except Exception as e:
            logger.exception(f"Error processing feed {feed_id}: {str(e)}")
            
            # Update processing log with error
            self.feed_processing_log_crud.update_processing_completed(
                session,
                log_id=log.id,
                status="error",
                error_message=str(e),
            )
            
            return {
                "status": "error",
                "feed_id": feed_id,
                "feed_name": feed.name,
                "message": str(e),
            }

    def get_feed_processing_logs(
        self, feed_id: int, skip: int = 0, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get processing logs for a feed.

        Args:
            feed_id: Feed ID
            skip: Number of items to skip
            limit: Maximum number of items to return

        Returns:
            List of processing logs as dicts
        """
        session = self._get_session()
        
        # Get logs
        logs = self.feed_processing_log_crud.get_by_feed_id(
            session, feed_id=feed_id, skip=skip, limit=limit
        )
        
        return [self._format_log_dict(log) for log in logs]

    def _format_feed_dict(self, feed: RSSFeed) -> Dict[str, Any]:
        """Format feed as a dict.

        Args:
            feed: Feed model instance

        Returns:
            Feed data as dict
        """
        return {
            "id": feed.id,
            "url": feed.url,
            "name": feed.name,
            "description": feed.description,
            "is_active": feed.is_active,
            "last_fetched_at": feed.last_fetched_at.isoformat() if feed.last_fetched_at else None,
            "created_at": feed.created_at.isoformat(),
            "updated_at": feed.updated_at.isoformat(),
        }

    def _format_log_dict(self, log: RSSFeedProcessingLog) -> Dict[str, Any]:
        """Format processing log as a dict.

        Args:
            log: Processing log model instance

        Returns:
            Processing log data as dict
        """
        return {
            "id": log.id,
            "feed_id": log.feed_id,
            "status": log.status,
            "articles_found": log.articles_found,
            "articles_added": log.articles_added,
            "error_message": log.error_message,
            "started_at": log.started_at.isoformat(),
            "completed_at": log.completed_at.isoformat() if log.completed_at else None,
        }


# Create a singleton instance
rss_feed_service = RSSFeedService()

def register_article_service(article_svc):
    """Register the article service to avoid circular imports.
    
    This function will be called from tasks.py after all imports are complete
    and the article_service is properly initialized.
    
    Args:
        article_svc: The initialized article service
    """
    global rss_feed_service
    rss_feed_service.article_service = article_svc

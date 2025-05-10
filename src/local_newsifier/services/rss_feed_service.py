"""
Service for managing RSS feeds.
This module provides functionality for RSS feed management, including
adding, updating, and processing feeds.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Callable

from sqlmodel import Session
from fastapi_injectable import injectable
from typing import Annotated
from fastapi import Depends

from local_newsifier.crud.rss_feed import rss_feed
from local_newsifier.crud.feed_processing_log import feed_processing_log
from local_newsifier.errors import handle_database, handle_rss
from local_newsifier.models.rss_feed import RSSFeed, RSSFeedProcessingLog
from local_newsifier.tools.rss_parser import parse_rss_feed

logger = logging.getLogger(__name__)


@injectable(use_cache=False)
class RSSFeedService:
    """Service for RSS feed management."""

    def __init__(
        self,
        rss_feed_crud,
        feed_processing_log_crud,
        article_service,
        session_factory: Callable,
    ):
        """Initialize with dependencies.

        Args:
            rss_feed_crud: CRUD for RSS feeds
            feed_processing_log_crud: CRUD for feed processing logs
            article_service: Service for article management
            session_factory: Factory for database sessions
        """
        self.rss_feed_crud = rss_feed_crud
        self.feed_processing_log_crud = feed_processing_log_crud
        self.article_service = article_service
        self.session_factory = session_factory



    @handle_database
    def get_feed(self, feed_id: int) -> Optional[Dict[str, Any]]:
        """Get a feed by ID.

        Args:
            feed_id: Feed ID

        Returns:
            Feed data as dict if found, None otherwise
        """
        with self.session_factory() as session:
            feed = self.rss_feed_crud.get(session, id=feed_id)
            if not feed:
                return None
            return self._format_feed_dict(feed)

    @handle_database
    def get_feed_by_url(self, url: str) -> Optional[Dict[str, Any]]:
        """Get a feed by URL.

        Args:
            url: Feed URL

        Returns:
            Feed data as dict if found, None otherwise
        """
        with self.session_factory() as session:
            feed = self.rss_feed_crud.get_by_url(session, url=url)
            if not feed:
                return None
            return self._format_feed_dict(feed)

    @handle_database
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
        with self.session_factory() as session:
            if active_only:
                feeds = self.rss_feed_crud.get_active_feeds(session, skip=skip, limit=limit)
            else:
                feeds = self.rss_feed_crud.get_multi(session, skip=skip, limit=limit)
            return [self._format_feed_dict(feed) for feed in feeds]

    @handle_database
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
        with self.session_factory() as session:
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

    @handle_database
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
        with self.session_factory() as session:
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

    @handle_database
    def remove_feed(self, feed_id: int) -> Optional[Dict[str, Any]]:
        """Remove a feed.

        Args:
            feed_id: Feed ID

        Returns:
            Removed feed data as dict if found, None otherwise
        """
        with self.session_factory() as session:
            # Get feed
            feed = self.rss_feed_crud.get(session, id=feed_id)
            if not feed:
                return None
            
            # Remove feed
            removed = self.rss_feed_crud.remove(session, id=feed_id)
            if not removed:
                return None
            
            return self._format_feed_dict(removed)


    @handle_rss
    @handle_database
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
        with self.session_factory() as session:
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
                        # Create article using the article_service
                        article_id = self.article_service.create_article_from_rss_entry(entry)
                        
                        if article_id:
                            # Queue article processing if task function provided
                            if task_queue_func:
                                task_queue_func(article_id)
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

    @handle_database
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
            
        Raises:
            ServiceError: On database errors with appropriate classification
        """
        with self.session_factory() as session:
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


# For backwards compatibility during transition
# Will be removed once all code is updated to use the container
def register_article_service(article_svc):
    """Register the article service to avoid circular imports.
    
    This function will be called from tasks.py after all imports are complete.
    TEMPORARY: Will be removed once all code is updated to use the container.
    
    Args:
        article_svc: The initialized article service
    """
    # Import at runtime to avoid circular imports
    from local_newsifier.container import container
    rss_feed_service = container.get("rss_feed_service")
    if rss_feed_service:
        rss_feed_service.article_service = article_svc

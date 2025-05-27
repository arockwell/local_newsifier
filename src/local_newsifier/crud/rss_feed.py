"""CRUD operations for RSS feeds."""

from datetime import datetime, timezone
from typing import List, Optional

from sqlmodel import Session, select

from local_newsifier.crud.base import CRUDBase
from local_newsifier.models.rss_feed import RSSFeed


class CRUDRSSFeed(CRUDBase[RSSFeed]):
    """CRUD operations for RSS feeds."""

    def get_by_url(self, db: Session, *, url: str) -> Optional[RSSFeed]:
        """Get a feed by URL.

        Args:
            db: Database session
            url: Feed URL

        Returns:
            The feed if found, None otherwise
        """
        return db.exec(select(RSSFeed).where(RSSFeed.url == url)).first()

    def get_active_feeds(self, db: Session, *, skip: int = 0, limit: int = 100) -> List[RSSFeed]:
        """Get active feeds with pagination.

        Args:
            db: Database session
            skip: Number of items to skip
            limit: Maximum number of items to return

        Returns:
            List of active feeds
        """
        return db.exec(select(RSSFeed).where(RSSFeed.is_active).offset(skip).limit(limit)).all()

    def update_last_fetched(self, db: Session, *, id: int) -> Optional[RSSFeed]:
        """Update the last_fetched_at timestamp for a feed.

        Args:
            db: Database session
            id: Feed ID

        Returns:
            Updated feed if found, None otherwise
        """
        feed = self.get(db, id=id)
        if feed:
            feed.last_fetched_at = datetime.now(timezone.utc)
            feed.updated_at = datetime.now(timezone.utc)
            db.add(feed)
            db.commit()
            db.refresh(feed)
            return feed
        return None


# Create a singleton instance
rss_feed = CRUDRSSFeed(RSSFeed)

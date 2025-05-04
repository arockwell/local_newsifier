"""Error-handled CRUD operations for RSS feeds."""

from typing import List

from sqlmodel import Session, select

from local_newsifier.crud.error_handled_base import (EntityNotFoundError,
                                                     ErrorHandledCRUD,
                                                     handle_crud_error)
from local_newsifier.models.rss_feed import RSSFeed


class ErrorHandledCRUDRSSFeed(ErrorHandledCRUD[RSSFeed]):
    """CRUD operations for RSS feeds with standardized error handling."""

    @handle_crud_error
    def get_by_url(self, db: Session, *, url: str) -> RSSFeed:
        """Get a feed by URL with error handling.

        Args:
            db: Database session
            url: Feed URL

        Returns:
            The feed if found

        Raises:
            EntityNotFoundError: If the feed with the given URL does not exist
            DatabaseConnectionError: If there's a connection issue
            TransactionError: If there's a database transaction error
        """
        statement = select(RSSFeed).where(RSSFeed.url == url)
        result = db.exec(statement).first()

        if result is None:
            raise EntityNotFoundError(
                f"RSS feed with URL '{url}' not found",
                context={"url": url, "model": self.model.__name__},
            )

        return result

    @handle_crud_error
    def get_active_feeds(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[RSSFeed]:
        """Get active feeds with pagination and error handling.

        Args:
            db: Database session
            skip: Number of items to skip
            limit: Maximum number of items to return

        Returns:
            List of active feeds

        Raises:
            DatabaseConnectionError: If there's a connection issue
            TransactionError: If there's a database transaction error
        """
        return db.exec(
            select(RSSFeed).where(RSSFeed.is_active).offset(skip).limit(limit)
        ).all()

    @handle_crud_error
    def update_last_fetched(self, db: Session, *, id: int) -> RSSFeed:
        """Update the last_fetched_at timestamp for a feed with error handling.

        Args:
            db: Database session
            id: Feed ID

        Returns:
            Updated feed

        Raises:
            EntityNotFoundError: If the feed with the given ID does not exist
            DatabaseConnectionError: If there's a connection issue
            TransactionError: If there's a database transaction error
        """
        from datetime import datetime, timezone

        feed = self.get(db, id=id)
        # Note: self.get() already raises EntityNotFoundError if feed not found

        feed.last_fetched_at = datetime.now(timezone.utc)
        feed.updated_at = datetime.now(timezone.utc)
        db.add(feed)
        db.commit()
        db.refresh(feed)
        return feed


# Create a singleton instance of the error handled rss feed CRUD
error_handled_rss_feed = ErrorHandledCRUDRSSFeed(RSSFeed)

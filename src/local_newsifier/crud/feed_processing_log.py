"""CRUD operations for feed processing logs."""

from datetime import datetime, timezone
from typing import List, Optional

from sqlmodel import Session, select

from local_newsifier.crud.base import CRUDBase
from local_newsifier.models.rss_feed import FeedProcessingLog


class CRUDFeedProcessingLog(CRUDBase[FeedProcessingLog]):
    """CRUD operations for feed processing logs."""

    def get_by_feed_id(
        self, db: Session, *, feed_id: int, skip: int = 0, limit: int = 100
    ) -> List[FeedProcessingLog]:
        """Get processing logs for a specific feed with pagination.

        Args:
            db: Database session
            feed_id: Feed ID
            skip: Number of items to skip
            limit: Maximum number of items to return

        Returns:
            List of processing logs for the feed
        """
        return db.exec(
            select(FeedProcessingLog)
            .where(FeedProcessingLog.feed_id == feed_id)
            .order_by(FeedProcessingLog.started_at.desc())
            .offset(skip)
            .limit(limit)
        ).all()

    def get_latest_by_feed_id(self, db: Session, *, feed_id: int) -> Optional[FeedProcessingLog]:
        """Get the most recent processing log for a feed.

        Args:
            db: Database session
            feed_id: Feed ID

        Returns:
            The most recent processing log if found, None otherwise
        """
        return db.exec(
            select(FeedProcessingLog)
            .where(FeedProcessingLog.feed_id == feed_id)
            .order_by(FeedProcessingLog.started_at.desc())
            .limit(1)
        ).first()

    def get_by_status(
        self, db: Session, *, status: str, skip: int = 0, limit: int = 100
    ) -> List[FeedProcessingLog]:
        """Get processing logs with a specific status.

        Args:
            db: Database session
            status: Status to filter by
            skip: Number of items to skip
            limit: Maximum number of items to return

        Returns:
            List of processing logs with the specified status
        """
        return db.exec(
            select(FeedProcessingLog)
            .where(FeedProcessingLog.status == status)
            .order_by(FeedProcessingLog.started_at.desc())
            .offset(skip)
            .limit(limit)
        ).all()

    def create_processing_started(
        self, db: Session, *, feed_id: int
    ) -> FeedProcessingLog:
        """Create a new processing log with 'started' status.

        Args:
            db: Database session
            feed_id: Feed ID

        Returns:
            Created processing log
        """
        log = FeedProcessingLog(
            feed_id=feed_id,
            status="started",
            started_at=datetime.now(timezone.utc),
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        return log

    def update_processing_completed(
        self,
        db: Session,
        *,
        log_id: int,
        status: str,
        articles_found: int = 0,
        articles_added: int = 0,
        error_message: Optional[str] = None,
    ) -> Optional[FeedProcessingLog]:
        """Update a processing log when processing is completed.

        Args:
            db: Database session
            log_id: Log ID
            status: Final status (success, error, etc.)
            articles_found: Number of articles found
            articles_added: Number of articles added
            error_message: Error message if processing failed

        Returns:
            Updated processing log if found, None otherwise
        """
        log = self.get(db, id=log_id)
        if log:
            log.status = status
            log.articles_found = articles_found
            log.articles_added = articles_added
            log.error_message = error_message
            log.completed_at = datetime.now(timezone.utc)
            db.add(log)
            db.commit()
            db.refresh(log)
            return log
        return None


# Create a singleton instance
feed_processing_log = CRUDFeedProcessingLog(FeedProcessingLog)

"""Error-handled CRUD operations for feed processing logs."""

from datetime import datetime, timezone
from typing import List, Optional

from sqlmodel import Session, select

from local_newsifier.crud.error_handled_base import (EntityNotFoundError,
                                                     ErrorHandledCRUD,
                                                     handle_crud_error)
from local_newsifier.models.rss_feed import RSSFeedProcessingLog


class ErrorHandledCRUDFeedProcessingLog(ErrorHandledCRUD[RSSFeedProcessingLog]):
    """CRUD operations for feed processing logs with standardized error handling."""

    @handle_crud_error
    def get_by_feed_id(
        self, db: Session, *, feed_id: int, skip: int = 0, limit: int = 100
    ) -> List[RSSFeedProcessingLog]:
        """Get processing logs for a specific feed with pagination and error handling.

        Args:
            db: Database session
            feed_id: Feed ID
            skip: Number of items to skip
            limit: Maximum number of items to return

        Returns:
            List of processing logs for the feed

        Raises:
            DatabaseConnectionError: If there's a connection issue
            TransactionError: If there's a database transaction error
        """
        return db.exec(
            select(RSSFeedProcessingLog)
            .where(RSSFeedProcessingLog.feed_id == feed_id)
            .order_by(RSSFeedProcessingLog.started_at.desc())
            .offset(skip)
            .limit(limit)
        ).all()

    @handle_crud_error
    def get_latest_by_feed_id(
        self, db: Session, *, feed_id: int
    ) -> RSSFeedProcessingLog:
        """Get the most recent processing log for a feed with error handling.

        Args:
            db: Database session
            feed_id: Feed ID

        Returns:
            The most recent processing log

        Raises:
            EntityNotFoundError: If no processing logs exist for the given feed ID
            DatabaseConnectionError: If there's a connection issue
            TransactionError: If there's a database transaction error
        """
        result = db.exec(
            select(RSSFeedProcessingLog)
            .where(RSSFeedProcessingLog.feed_id == feed_id)
            .order_by(RSSFeedProcessingLog.started_at.desc())
            .limit(1)
        ).first()

        if result is None:
            raise EntityNotFoundError(
                f"No processing logs found for feed ID {feed_id}",
                context={"feed_id": feed_id, "model": self.model.__name__},
            )

        return result

    @handle_crud_error
    def get_by_status(
        self, db: Session, *, status: str, skip: int = 0, limit: int = 100
    ) -> List[RSSFeedProcessingLog]:
        """Get processing logs with a specific status with error handling.

        Args:
            db: Database session
            status: Status to filter by
            skip: Number of items to skip
            limit: Maximum number of items to return

        Returns:
            List of processing logs with the specified status

        Raises:
            DatabaseConnectionError: If there's a connection issue
            TransactionError: If there's a database transaction error
        """
        return db.exec(
            select(RSSFeedProcessingLog)
            .where(RSSFeedProcessingLog.status == status)
            .order_by(RSSFeedProcessingLog.started_at.desc())
            .offset(skip)
            .limit(limit)
        ).all()

    @handle_crud_error
    def create_processing_started(
        self, db: Session, *, feed_id: int
    ) -> RSSFeedProcessingLog:
        """Create a new processing log with 'started' status and error handling.

        Args:
            db: Database session
            feed_id: Feed ID

        Returns:
            Created processing log

        Raises:
            ValidationError: If the feed_id is invalid
            DatabaseConnectionError: If there's a connection issue
            TransactionError: If there's a database transaction error
        """
        log = RSSFeedProcessingLog(
            feed_id=feed_id,
            status="started",
            started_at=datetime.now(timezone.utc),
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        return log

    @handle_crud_error
    def update_processing_completed(
        self,
        db: Session,
        *,
        log_id: int,
        status: str,
        articles_found: int = 0,
        articles_added: int = 0,
        error_message: Optional[str] = None,
    ) -> RSSFeedProcessingLog:
        """Update a processing log when processing is completed with error handling.

        Args:
            db: Database session
            log_id: Log ID
            status: Final status (success, error, etc.)
            articles_found: Number of articles found
            articles_added: Number of articles added
            error_message: Error message if processing failed

        Returns:
            Updated processing log

        Raises:
            EntityNotFoundError: If the processing log with the given ID does not exist
            ValidationError: If the status is invalid
            DatabaseConnectionError: If there's a connection issue
            TransactionError: If there's a database transaction error
        """
        log = self.get(db, id=log_id)
        # Note: self.get() already raises EntityNotFoundError if log not found

        log.status = status
        log.articles_found = articles_found
        log.articles_added = articles_added
        log.error_message = error_message
        log.completed_at = datetime.now(timezone.utc)
        db.add(log)
        db.commit()
        db.refresh(log)
        return log


# Create a singleton instance of the error handled feed processing log CRUD
error_handled_feed_processing_log = ErrorHandledCRUDFeedProcessingLog(
    RSSFeedProcessingLog
)

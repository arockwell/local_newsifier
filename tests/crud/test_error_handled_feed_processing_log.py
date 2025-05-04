"""Tests for the error-handled feed processing log CRUD module."""

from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest
from sqlalchemy.exc import IntegrityError
from sqlmodel import select

from local_newsifier.crud.error_handled_base import (EntityNotFoundError,
                                                     ValidationError)
from local_newsifier.crud.error_handled_feed_processing_log import (
    ErrorHandledCRUDFeedProcessingLog, error_handled_feed_processing_log)
from local_newsifier.models.rss_feed import RSSFeed, RSSFeedProcessingLog


class TestErrorHandledFeedProcessingLogCRUD:
    """Tests for ErrorHandledCRUDFeedProcessingLog class."""

    def test_create(self, db_session):
        """Test creating a new processing log."""
        # Create a feed first to use as foreign key
        feed = RSSFeed(
            url="https://example.com/feed.xml",
            name="Test Feed",
            description="A test feed",
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db_session.add(feed)
        db_session.commit()

        # Test data for a new processing log
        log_data = {
            "feed_id": feed.id,
            "status": "success",
            "articles_found": 10,
            "articles_added": 5,
            "started_at": datetime.now(timezone.utc),
            "completed_at": datetime.now(timezone.utc) + timedelta(minutes=5),
        }

        # Create the processing log
        log = error_handled_feed_processing_log.create(db_session, obj_in=log_data)

        # Verify it was created correctly
        assert log is not None
        assert log.id is not None
        assert log.feed_id == feed.id
        assert log.status == "success"
        assert log.articles_found == 10
        assert log.articles_added == 5

        # Verify it was saved to the database
        statement = select(RSSFeedProcessingLog).where(
            RSSFeedProcessingLog.id == log.id
        )
        result = db_session.exec(statement).first()
        assert result is not None
        assert result.feed_id == feed.id
        assert result.status == "success"

    def test_create_invalid_feed_id(self, db_session):
        """Test creating a processing log with an invalid feed ID."""
        # Test data with non-existent feed_id
        log_data = {
            "feed_id": 999,  # Non-existent feed ID
            "status": "success",
            "articles_found": 10,
            "articles_added": 5,
            "started_at": datetime.now(timezone.utc),
        }

        # Mock the database error that would occur
        with patch.object(db_session, "commit") as mock_commit:
            # Simulate an IntegrityError for foreign key violation
            mock_commit.side_effect = IntegrityError(
                "FOREIGN KEY constraint failed", params=None, orig=None
            )

            with pytest.raises(ValidationError) as excinfo:
                error_handled_feed_processing_log.create(db_session, obj_in=log_data)

            assert "constraint violation" in str(excinfo.value).lower()
            assert excinfo.value.error_type == "validation"

    def test_get_by_feed_id(self, db_session):
        """Test getting logs by feed ID with error handling."""
        # Create a feed
        feed = RSSFeed(
            url="https://example.com/feed.xml",
            name="Test Feed",
            description="A test feed",
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db_session.add(feed)
        db_session.commit()

        # Create several logs for this feed
        time_now = datetime.now(timezone.utc)
        logs = []
        for i in range(3):
            log = RSSFeedProcessingLog(
                feed_id=feed.id,
                status="success",
                started_at=time_now - timedelta(days=i),
                completed_at=(time_now - timedelta(days=i) + timedelta(minutes=5)),
                articles_found=10 - i,
                articles_added=5 - i,
            )
            logs.append(log)
            db_session.add(log)
        db_session.commit()

        # Test getting logs by feed ID
        retrieved_logs = error_handled_feed_processing_log.get_by_feed_id(
            db_session, feed_id=feed.id
        )

        # Verify we got the right logs
        assert len(retrieved_logs) == 3

        # Verify they're ordered by started_at desc
        assert retrieved_logs[0].started_at > retrieved_logs[1].started_at
        assert retrieved_logs[1].started_at > retrieved_logs[2].started_at

    def test_get_latest_by_feed_id(self, db_session):
        """Test getting the latest log for a feed with error handling."""
        # Create a feed
        feed = RSSFeed(
            url="https://example.com/feed.xml",
            name="Test Feed",
            description="A test feed",
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db_session.add(feed)
        db_session.commit()

        # Create several logs with different timestamps
        now = datetime.now(timezone.utc)
        logs = [
            RSSFeedProcessingLog(
                feed_id=feed.id,
                status="success",
                started_at=now - timedelta(days=2),
                completed_at=now - timedelta(days=2) + timedelta(minutes=5),
                articles_found=8,
                articles_added=4,
            ),
            RSSFeedProcessingLog(
                feed_id=feed.id,
                status="error",
                started_at=now - timedelta(days=1),
                completed_at=now - timedelta(days=1) + timedelta(minutes=5),
                articles_found=0,
                articles_added=0,
                error_message="Test error",
            ),
            RSSFeedProcessingLog(
                feed_id=feed.id,
                status="success",
                started_at=now,
                completed_at=now + timedelta(minutes=5),
                articles_found=10,
                articles_added=5,
            ),
        ]

        for log in logs:
            db_session.add(log)
        db_session.commit()

        # Test getting the latest log
        latest_log = error_handled_feed_processing_log.get_latest_by_feed_id(
            db_session, feed_id=feed.id
        )

        # Verify it's the most recent one
        assert latest_log is not None
        assert latest_log.started_at == now  # Most recent log

    def test_get_latest_by_feed_id_not_found(self, db_session):
        """Test getting the latest log for a non-existent feed."""
        with pytest.raises(EntityNotFoundError) as excinfo:
            error_handled_feed_processing_log.get_latest_by_feed_id(
                db_session, feed_id=999
            )

        assert "No processing logs found for feed ID 999" in str(excinfo.value)
        assert excinfo.value.error_type == "not_found"
        assert excinfo.value.context["feed_id"] == 999

    def test_get_by_status(self, db_session):
        """Test getting logs by status with error handling."""
        # Create a feed
        feed = RSSFeed(
            url="https://example.com/feed.xml",
            name="Test Feed",
            description="A test feed",
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db_session.add(feed)
        db_session.commit()

        # Create logs with different statuses
        time_now = datetime.now(timezone.utc)
        success_logs = []
        for i in range(2):
            log = RSSFeedProcessingLog(
                feed_id=feed.id,
                status="success",
                started_at=time_now - timedelta(days=i),
                completed_at=(time_now - timedelta(days=i) + timedelta(minutes=5)),
                articles_found=10,
                articles_added=5,
            )
            success_logs.append(log)
            db_session.add(log)

        error_logs = []
        for i in range(2):
            log = RSSFeedProcessingLog(
                feed_id=feed.id,
                status="error",
                started_at=time_now - timedelta(days=i + 2),
                completed_at=(time_now - timedelta(days=i + 2) + timedelta(minutes=5)),
                error_message=f"Error {i}",
            )
            error_logs.append(log)
            db_session.add(log)

        db_session.commit()

        # Test getting logs by status
        success_results = error_handled_feed_processing_log.get_by_status(
            db_session, status="success"
        )
        error_results = error_handled_feed_processing_log.get_by_status(
            db_session, status="error"
        )

        # Verify we got the right logs
        assert len(success_results) == 2
        assert len(error_results) == 2

        # Verify all have the correct status
        for log in success_results:
            assert log.status == "success"

        for log in error_results:
            assert log.status == "error"

    def test_create_processing_started(self, db_session):
        """Test creating a new processing log with 'started' status and error handling."""
        # Create a feed
        feed = RSSFeed(
            url="https://example.com/feed.xml",
            name="Test Feed",
            description="A test feed",
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db_session.add(feed)
        db_session.commit()

        # Test creating a processing log
        before_create = datetime.now(timezone.utc)
        log = error_handled_feed_processing_log.create_processing_started(
            db_session, feed_id=feed.id
        )
        after_create = datetime.now(timezone.utc)

        # Verify the log was created with correct values
        assert log is not None
        assert log.feed_id == feed.id
        assert log.status == "started"

        # Handle timezone awareness
        started_at = log.started_at
        if started_at.tzinfo is None:
            started_at = started_at.replace(tzinfo=timezone.utc)

        assert before_create <= started_at <= after_create
        assert log.completed_at is None
        assert log.articles_found == 0
        assert log.articles_added == 0
        assert log.error_message is None

    def test_create_processing_started_invalid_feed(self, db_session):
        """Test creating a processing log for an invalid feed."""
        # Mock the database error
        with patch.object(db_session, "commit") as mock_commit:
            # Simulate an IntegrityError for foreign key violation
            mock_commit.side_effect = IntegrityError(
                "FOREIGN KEY constraint failed", params=None, orig=None
            )

            with pytest.raises(ValidationError) as excinfo:
                error_handled_feed_processing_log.create_processing_started(
                    db_session, feed_id=999  # Non-existent feed ID
                )

            assert "constraint violation" in str(excinfo.value).lower()
            assert excinfo.value.error_type == "validation"

    def test_update_processing_completed(self, db_session):
        """Test updating a processing log with error handling."""
        # Create a feed
        feed = RSSFeed(
            url="https://example.com/feed.xml",
            name="Test Feed",
            description="A test feed",
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db_session.add(feed)
        db_session.commit()

        # Create a processing log
        log = RSSFeedProcessingLog(
            feed_id=feed.id,
            status="started",
            started_at=datetime.now(timezone.utc) - timedelta(minutes=10),
        )
        db_session.add(log)
        db_session.commit()

        # Update the log
        before_update = datetime.now(timezone.utc)
        updated_log = error_handled_feed_processing_log.update_processing_completed(
            db_session,
            log_id=log.id,
            status="success",
            articles_found=15,
            articles_added=7,
        )
        after_update = datetime.now(timezone.utc)

        # Verify the update
        assert updated_log is not None
        assert updated_log.id == log.id
        assert updated_log.feed_id == feed.id
        assert updated_log.status == "success"
        assert updated_log.articles_found == 15
        assert updated_log.articles_added == 7
        assert updated_log.error_message is None

        # Handle timezone awareness
        completed_at = updated_log.completed_at
        if completed_at.tzinfo is None:
            completed_at = completed_at.replace(tzinfo=timezone.utc)

        assert before_update <= completed_at <= after_update

    def test_update_processing_completed_not_found(self, db_session):
        """Test updating a non-existent processing log."""
        with pytest.raises(EntityNotFoundError) as excinfo:
            error_handled_feed_processing_log.update_processing_completed(
                db_session,
                log_id=999,
                status="success",
                articles_found=10,
                articles_added=5,
            )

        assert "RSSFeedProcessingLog with id 999 not found" in str(excinfo.value)
        assert excinfo.value.error_type == "not_found"
        assert excinfo.value.context["id"] == 999

    def test_singleton_instance(self):
        """Test singleton instance behavior."""
        assert isinstance(
            error_handled_feed_processing_log, ErrorHandledCRUDFeedProcessingLog
        )
        assert error_handled_feed_processing_log.model == RSSFeedProcessingLog

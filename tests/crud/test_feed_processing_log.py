"""Tests for the feed processing log CRUD module."""

from datetime import datetime, timedelta, timezone

import pytest
from sqlmodel import Session, select

from local_newsifier.crud.feed_processing_log import CRUDFeedProcessingLog, feed_processing_log
from local_newsifier.models.rss_feed import RSSFeed, RSSFeedProcessingLog


def test_get_by_feed_id(db_session):
    """Test getting logs by feed ID."""
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
    logs = [
        RSSFeedProcessingLog(
            feed_id=feed.id,
            status="success",
            started_at=datetime.now(timezone.utc) - timedelta(days=i),
            completed_at=datetime.now(timezone.utc) - timedelta(days=i) + timedelta(minutes=5),
            articles_found=10 - i,
            articles_added=5 - i,
        )
        for i in range(3)
    ]

    for log in logs:
        db_session.add(log)
    db_session.commit()

    # Test getting logs by feed ID
    retrieved_logs = feed_processing_log.get_by_feed_id(db_session, feed_id=feed.id)
    assert len(retrieved_logs) == 3

    # Verify they're ordered by started_at desc
    assert retrieved_logs[0].started_at > retrieved_logs[1].started_at
    assert retrieved_logs[1].started_at > retrieved_logs[2].started_at

    # Test pagination
    paginated_logs = feed_processing_log.get_by_feed_id(
        db_session, feed_id=feed.id, skip=1, limit=1
    )
    assert len(paginated_logs) == 1
    assert paginated_logs[0].started_at == retrieved_logs[1].started_at


def test_get_latest_by_feed_id(db_session):
    """Test getting the latest log for a feed."""
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
    older_log = RSSFeedProcessingLog(
        feed_id=feed.id,
        status="success",
        started_at=now - timedelta(days=2),
        completed_at=now - timedelta(days=2) + timedelta(minutes=5),
        articles_found=8,
        articles_added=4,
    )

    middle_log = RSSFeedProcessingLog(
        feed_id=feed.id,
        status="error",
        started_at=now - timedelta(days=1),
        completed_at=now - timedelta(days=1) + timedelta(minutes=5),
        articles_found=0,
        articles_added=0,
        error_message="Test error",
    )

    newest_log = RSSFeedProcessingLog(
        feed_id=feed.id,
        status="success",
        started_at=now,
        completed_at=now + timedelta(minutes=5),
        articles_found=10,
        articles_added=5,
    )

    db_session.add(older_log)
    db_session.add(middle_log)
    db_session.add(newest_log)
    db_session.commit()

    # Test getting the latest log
    latest_log = feed_processing_log.get_latest_by_feed_id(db_session, feed_id=feed.id)
    assert latest_log is not None
    assert latest_log.id == newest_log.id
    assert latest_log.started_at == newest_log.started_at

    # Test with non-existent feed ID
    non_existent = feed_processing_log.get_latest_by_feed_id(db_session, feed_id=999)
    assert non_existent is None


def test_get_by_status(db_session):
    """Test getting logs by status."""
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
    success_logs = [
        RSSFeedProcessingLog(
            feed_id=feed.id,
            status="success",
            started_at=datetime.now(timezone.utc) - timedelta(days=i),
            completed_at=datetime.now(timezone.utc) - timedelta(days=i) + timedelta(minutes=5),
            articles_found=10,
            articles_added=5,
        )
        for i in range(2)
    ]

    error_logs = [
        RSSFeedProcessingLog(
            feed_id=feed.id,
            status="error",
            started_at=datetime.now(timezone.utc) - timedelta(days=i),
            completed_at=datetime.now(timezone.utc) - timedelta(days=i) + timedelta(minutes=5),
            error_message=f"Error {i}",
        )
        for i in range(2, 4)
    ]

    for log in success_logs + error_logs:
        db_session.add(log)
    db_session.commit()

    # Test getting logs by status
    success_results = feed_processing_log.get_by_status(db_session, status="success")
    error_results = feed_processing_log.get_by_status(db_session, status="error")

    assert len(success_results) == 2
    assert len(error_results) == 2

    # Verify all have the correct status
    for log in success_results:
        assert log.status == "success"

    for log in error_results:
        assert log.status == "error"

    # Test pagination
    paginated_success = feed_processing_log.get_by_status(
        db_session, status="success", skip=1, limit=1
    )
    assert len(paginated_success) == 1
    assert paginated_success[0].status == "success"


def test_create_processing_started(db_session):
    """Test creating a new processing log with 'started' status."""
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
    log = feed_processing_log.create_processing_started(db_session, feed_id=feed.id)
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
    # SQLModel might initialize these to 0 instead of None
    assert log.articles_found == 0 or log.articles_found is None
    assert log.articles_added == 0 or log.articles_added is None
    assert log.error_message is None

    # Verify it's in the database
    db_log = db_session.get(RSSFeedProcessingLog, log.id)
    assert db_log is not None
    assert db_log.status == "started"


def test_update_processing_completed_success(db_session):
    """Test updating a processing log with success status."""
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
    updated_log = feed_processing_log.update_processing_completed(
        db_session, log_id=log.id, status="success", articles_found=15, articles_added=7
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

    # Verify it's updated in the database
    db_log = db_session.get(RSSFeedProcessingLog, log.id)
    assert db_log.status == "success"
    assert db_log.articles_found == 15
    assert db_log.articles_added == 7
    assert db_log.completed_at is not None


def test_update_processing_completed_error(db_session):
    """Test updating a processing log with error status."""
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

    # Update the log with error status
    updated_log = feed_processing_log.update_processing_completed(
        db_session,
        log_id=log.id,
        status="error",
        error_message="Failed to parse feed: Connection error",
    )

    # Verify the update
    assert updated_log is not None
    assert updated_log.status == "error"
    assert updated_log.articles_found == 0  # Default value
    assert updated_log.articles_added == 0  # Default value
    assert updated_log.error_message == "Failed to parse feed: Connection error"

    # Verify it's updated in the database
    db_log = db_session.get(RSSFeedProcessingLog, log.id)
    assert db_log.status == "error"
    assert db_log.error_message == "Failed to parse feed: Connection error"


def test_update_processing_completed_nonexistent(db_session):
    """Test updating a non-existent processing log."""
    result = feed_processing_log.update_processing_completed(
        db_session, log_id=999, status="success", articles_found=10, articles_added=5
    )
    assert result is None


def test_singleton_instance():
    """Test singleton instance behavior."""
    assert isinstance(feed_processing_log, CRUDFeedProcessingLog)

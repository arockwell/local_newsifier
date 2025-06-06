"""Tests for the feed processing log CRUD module."""

from datetime import datetime, timedelta, timezone

import pytest
from sqlmodel import select

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


@pytest.mark.parametrize(
    "custom_params",
    [
        {},  # Default case
        {"started_at": datetime.now(timezone.utc) - timedelta(hours=2)},  # Custom started_at
    ],
)
def test_create_processing_started(db_session, custom_params):
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

    if custom_params:
        # Create with custom parameters
        log_data = RSSFeedProcessingLog(
            feed_id=feed.id,
            status="started",
            articles_found=0,
            articles_added=0,
            **custom_params,
        )
        db_session.add(log_data)
        db_session.commit()
        log = feed_processing_log.get(db_session, id=log_data.id)
    else:
        # Use the CRUD method
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

    if custom_params.get("started_at"):
        assert started_at == custom_params["started_at"]
    else:
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


@pytest.mark.parametrize(
    "update_params,expected_status",
    [
        (
            {"status": "success", "articles_found": 15, "articles_added": 7},
            "success",
        ),
        (
            {"status": "error", "error_message": "Failed to parse feed: Connection error"},
            "error",
        ),
        (
            {"status": "invalid_status", "articles_found": 0, "articles_added": 0},
            "invalid_status",  # Test that system doesn't enforce validation at CRUD level
        ),
    ],
)
def test_update_processing_completed(db_session, update_params, expected_status):
    """Test updating a processing log with different statuses."""
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
        db_session, log_id=log.id, **update_params
    )
    after_update = datetime.now(timezone.utc)

    # Verify the update
    assert updated_log is not None
    assert updated_log.id == log.id
    assert updated_log.feed_id == feed.id
    assert updated_log.status == expected_status

    if expected_status == "success":
        assert updated_log.articles_found == 15
        assert updated_log.articles_added == 7
        assert updated_log.error_message is None
    elif expected_status == "error":
        assert updated_log.articles_found == 0  # Default value
        assert updated_log.articles_added == 0  # Default value
        assert updated_log.error_message == "Failed to parse feed: Connection error"

    # Handle timezone awareness
    completed_at = updated_log.completed_at
    if completed_at.tzinfo is None:
        completed_at = completed_at.replace(tzinfo=timezone.utc)

    assert before_update <= completed_at <= after_update

    # Verify it's updated in the database
    db_log = db_session.get(RSSFeedProcessingLog, log.id)
    assert db_log.status == expected_status
    assert db_log.completed_at is not None


def test_update_processing_completed_nonexistent(db_session):
    """Test updating a non-existent processing log."""
    result = feed_processing_log.update_processing_completed(
        db_session, log_id=999, status="success", articles_found=10, articles_added=5
    )
    assert result is None


def test_singleton_instance():
    """Test singleton instance behavior."""
    assert isinstance(feed_processing_log, CRUDFeedProcessingLog)


def test_status_transition_validation(db_session):
    """Test proper status transition flow."""
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

    # Create a processing log with 'started' status
    log = feed_processing_log.create_processing_started(db_session, feed_id=feed.id)
    assert log.status == "started"
    assert log.completed_at is None

    # Update to 'success' status
    updated_log = feed_processing_log.update_processing_completed(
        db_session, log_id=log.id, status="success", articles_found=10, articles_added=5
    )

    # Verify the transition
    assert updated_log.status == "success"
    assert updated_log.completed_at is not None
    assert updated_log.articles_found == 10
    assert updated_log.articles_added == 5

    # Update to 'error' status
    error_log = feed_processing_log.update_processing_completed(
        db_session, log_id=log.id, status="error", error_message="Something went wrong"
    )

    # Verify the error update
    assert error_log.status == "error"
    assert error_log.error_message == "Something went wrong"

    # Verify the log in the database has the updated status
    db_log = db_session.get(RSSFeedProcessingLog, log.id)
    assert db_log.status == "error"
    assert db_log.error_message == "Something went wrong"


def test_get_by_date_range(db_session):
    """Test retrieving logs within a date range."""
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

    # Create logs with different dates
    now = datetime.now(timezone.utc)

    # Log from 5 days ago
    old_log = RSSFeedProcessingLog(
        feed_id=feed.id,
        status="success",
        started_at=now - timedelta(days=5),
        completed_at=now - timedelta(days=5) + timedelta(minutes=5),
        articles_found=10,
        articles_added=5,
    )

    # Log from 3 days ago
    middle_log = RSSFeedProcessingLog(
        feed_id=feed.id,
        status="success",
        started_at=now - timedelta(days=3),
        completed_at=now - timedelta(days=3) + timedelta(minutes=5),
        articles_found=15,
        articles_added=7,
    )

    # Recent log
    recent_log = RSSFeedProcessingLog(
        feed_id=feed.id,
        status="success",
        started_at=now - timedelta(days=1),
        completed_at=now - timedelta(days=1) + timedelta(minutes=5),
        articles_found=20,
        articles_added=10,
    )

    db_session.add(old_log)
    db_session.add(middle_log)
    db_session.add(recent_log)
    db_session.commit()

    # Query logs within a specific date range (3-2 days ago)
    start_date = now - timedelta(days=4)
    end_date = now - timedelta(days=2)

    # We need to use a direct query since the CRUD module doesn't have a date range method
    # In a real application, you might want to add this method to the CRUD module
    logs_in_range = db_session.exec(
        select(RSSFeedProcessingLog)
        .where(RSSFeedProcessingLog.feed_id == feed.id)
        .where(RSSFeedProcessingLog.started_at >= start_date)
        .where(RSSFeedProcessingLog.started_at <= end_date)
        .order_by(RSSFeedProcessingLog.started_at.desc())
    ).all()

    # Verify only the middle log is in the range
    assert len(logs_in_range) == 1
    assert logs_in_range[0].id == middle_log.id


def test_get_by_feed_id_and_status(db_session):
    """Test retrieving logs by both feed ID and status."""
    # Create two feeds
    feed1 = RSSFeed(
        url="https://example.com/feed1.xml",
        name="Test Feed 1",
        description="A test feed",
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    feed2 = RSSFeed(
        url="https://example.com/feed2.xml",
        name="Test Feed 2",
        description="Another test feed",
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    db_session.add(feed1)
    db_session.add(feed2)
    db_session.commit()

    # Create logs with different statuses for each feed
    # Feed 1 logs
    feed1_success_log = RSSFeedProcessingLog(
        feed_id=feed1.id,
        status="success",
        started_at=datetime.now(timezone.utc) - timedelta(hours=2),
        completed_at=datetime.now(timezone.utc) - timedelta(hours=2) + timedelta(minutes=5),
        articles_found=10,
        articles_added=5,
    )

    feed1_error_log = RSSFeedProcessingLog(
        feed_id=feed1.id,
        status="error",
        started_at=datetime.now(timezone.utc) - timedelta(hours=1),
        completed_at=datetime.now(timezone.utc) - timedelta(hours=1) + timedelta(minutes=5),
        error_message="Test error",
    )

    # Feed 2 logs
    feed2_success_log = RSSFeedProcessingLog(
        feed_id=feed2.id,
        status="success",
        started_at=datetime.now(timezone.utc) - timedelta(hours=2),
        completed_at=datetime.now(timezone.utc) - timedelta(hours=2) + timedelta(minutes=5),
        articles_found=15,
        articles_added=7,
    )

    feed2_started_log = RSSFeedProcessingLog(
        feed_id=feed2.id,
        status="started",
        started_at=datetime.now(timezone.utc) - timedelta(minutes=30),
    )

    db_session.add(feed1_success_log)
    db_session.add(feed1_error_log)
    db_session.add(feed2_success_log)
    db_session.add(feed2_started_log)
    db_session.commit()

    # Query logs by feed ID and status
    # We need to use a direct query since the CRUD module doesn't have a combined method
    # In a real application, you might want to add this method to the CRUD module
    feed1_success_logs = db_session.exec(
        select(RSSFeedProcessingLog)
        .where(RSSFeedProcessingLog.feed_id == feed1.id)
        .where(RSSFeedProcessingLog.status == "success")
        .order_by(RSSFeedProcessingLog.started_at.desc())
    ).all()

    feed2_started_logs = db_session.exec(
        select(RSSFeedProcessingLog)
        .where(RSSFeedProcessingLog.feed_id == feed2.id)
        .where(RSSFeedProcessingLog.status == "started")
        .order_by(RSSFeedProcessingLog.started_at.desc())
    ).all()

    # Verify the results
    assert len(feed1_success_logs) == 1
    assert feed1_success_logs[0].id == feed1_success_log.id

    assert len(feed2_started_logs) == 1
    assert feed2_started_logs[0].id == feed2_started_log.id


@pytest.mark.parametrize(
    "articles_found,articles_added,error_message",
    [
        (0, 0, ""),  # Edge case: no articles, empty error
        (1000000, 999999, "E" * 1000),  # Edge case: very large values
        (42, 21, "This should not be saved"),  # Normal values for non-existent log
    ],
)
def test_edge_cases(db_session, articles_found, articles_added, error_message):
    """Test creating and updating logs with edge case values."""
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

    # Test updating non-existent log (should return None)
    if articles_found == 42:  # Use this as a flag for non-existent log test
        result = feed_processing_log.update_processing_completed(
            db_session,
            log_id=999,  # Non-existent ID
            status="success",
            articles_found=articles_found,
            articles_added=articles_added,
            error_message=error_message,
        )
        assert result is None
        logs = db_session.exec(select(RSSFeedProcessingLog)).all()
        assert len(logs) == 0
    else:
        # Create a log and update with edge case values
        log = feed_processing_log.create_processing_started(db_session, feed_id=feed.id)

        updated_log = feed_processing_log.update_processing_completed(
            db_session,
            log_id=log.id,
            status="success",
            articles_found=articles_found,
            articles_added=articles_added,
            error_message=error_message,
        )

        # Verify the update
        assert updated_log is not None
        assert updated_log.status == "success"
        assert updated_log.articles_found == articles_found
        assert updated_log.articles_added == articles_added
        assert updated_log.error_message == error_message

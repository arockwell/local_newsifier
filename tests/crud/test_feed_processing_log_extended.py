"""Extended tests for the feed processing log CRUD module."""

from datetime import datetime, timezone, timedelta

import pytest
from sqlmodel import Session, select

from local_newsifier.crud.feed_processing_log import CRUDFeedProcessingLog, feed_processing_log
from local_newsifier.models.rss_feed import RSSFeed, RSSFeedProcessingLog


def test_create_processing_with_custom_parameters(db_session):
    """Test creating a log with custom parameters."""
    # Create a feed
    feed = RSSFeed(
        url="https://example.com/feed.xml",
        name="Test Feed",
        description="A test feed",
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db_session.add(feed)
    db_session.commit()
    
    # Create a custom log directly using the model
    custom_started_at = datetime.now(timezone.utc) - timedelta(hours=2)
    log_data = RSSFeedProcessingLog(
        feed_id=feed.id,
        status="started",
        started_at=custom_started_at,
        articles_found=0,
        articles_added=0
    )
    db_session.add(log_data)
    db_session.commit()
    
    # Verify the log was created with correct values
    retrieved_log = feed_processing_log.get(db_session, id=log_data.id)
    assert retrieved_log is not None
    assert retrieved_log.feed_id == feed.id
    assert retrieved_log.status == "started"
    
    # Compare datetime values accounting for timezone differences
    if retrieved_log.started_at.tzinfo is None:
        retrieved_time = retrieved_log.started_at.replace(tzinfo=timezone.utc)
    else:
        retrieved_time = retrieved_log.started_at
        
    assert retrieved_time == custom_started_at
    assert retrieved_log.completed_at is None


def test_invalid_status_update(db_session):
    """Test updating with invalid status values."""
    # Create a feed
    feed = RSSFeed(
        url="https://example.com/feed.xml",
        name="Test Feed",
        description="A test feed",
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db_session.add(feed)
    db_session.commit()
    
    # Create a processing log
    log = feed_processing_log.create_processing_started(db_session, feed_id=feed.id)
    
    # Update with an invalid status
    # Note: This test verifies that the system doesn't enforce status validation at the CRUD level
    # In a real application, validation might be handled at the service layer
    updated_log = feed_processing_log.update_processing_completed(
        db_session,
        log_id=log.id,
        status="invalid_status",  # This is not a standard status
        articles_found=0,
        articles_added=0
    )
    
    # Verify the update was applied despite the invalid status
    assert updated_log is not None
    assert updated_log.status == "invalid_status"
    assert updated_log.completed_at is not None


def test_status_transition_validation(db_session):
    """Test proper status transition flow."""
    # Create a feed
    feed = RSSFeed(
        url="https://example.com/feed.xml",
        name="Test Feed",
        description="A test feed",
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db_session.add(feed)
    db_session.commit()
    
    # Create a processing log with 'started' status
    log = feed_processing_log.create_processing_started(db_session, feed_id=feed.id)
    assert log.status == "started"
    assert log.completed_at is None
    
    # Update to 'success' status
    updated_log = feed_processing_log.update_processing_completed(
        db_session,
        log_id=log.id,
        status="success",
        articles_found=10,
        articles_added=5
    )
    
    # Verify the transition
    assert updated_log.status == "success"
    assert updated_log.completed_at is not None
    assert updated_log.articles_found == 10
    assert updated_log.articles_added == 5
    
    # Update to 'error' status
    error_log = feed_processing_log.update_processing_completed(
        db_session,
        log_id=log.id,
        status="error",
        error_message="Something went wrong"
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
        updated_at=datetime.now(timezone.utc)
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
        articles_added=5
    )
    
    # Log from 3 days ago
    middle_log = RSSFeedProcessingLog(
        feed_id=feed.id,
        status="success",
        started_at=now - timedelta(days=3),
        completed_at=now - timedelta(days=3) + timedelta(minutes=5),
        articles_found=15,
        articles_added=7
    )
    
    # Recent log
    recent_log = RSSFeedProcessingLog(
        feed_id=feed.id,
        status="success",
        started_at=now - timedelta(days=1),
        completed_at=now - timedelta(days=1) + timedelta(minutes=5),
        articles_found=20,
        articles_added=10
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
        updated_at=datetime.now(timezone.utc)
    )
    
    feed2 = RSSFeed(
        url="https://example.com/feed2.xml",
        name="Test Feed 2",
        description="Another test feed",
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
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
        articles_added=5
    )
    
    feed1_error_log = RSSFeedProcessingLog(
        feed_id=feed1.id,
        status="error",
        started_at=datetime.now(timezone.utc) - timedelta(hours=1),
        completed_at=datetime.now(timezone.utc) - timedelta(hours=1) + timedelta(minutes=5),
        error_message="Test error"
    )
    
    # Feed 2 logs
    feed2_success_log = RSSFeedProcessingLog(
        feed_id=feed2.id,
        status="success",
        started_at=datetime.now(timezone.utc) - timedelta(hours=2),
        completed_at=datetime.now(timezone.utc) - timedelta(hours=2) + timedelta(minutes=5),
        articles_found=15,
        articles_added=7
    )
    
    feed2_started_log = RSSFeedProcessingLog(
        feed_id=feed2.id,
        status="started",
        started_at=datetime.now(timezone.utc) - timedelta(minutes=30)
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


def test_update_nonexistent_log_with_custom_values(db_session):
    """Test updating a non-existent log with custom values."""
    # Try to update a non-existent log with custom values
    result = feed_processing_log.update_processing_completed(
        db_session,
        log_id=999,  # Non-existent ID
        status="success",
        articles_found=42,
        articles_added=21,
        error_message="This should not be saved"
    )
    
    # Verify the result is None
    assert result is None
    
    # Verify no log was created
    logs = db_session.exec(select(RSSFeedProcessingLog)).all()
    assert len(logs) == 0


def test_create_and_update_with_edge_values(db_session):
    """Test creating and updating logs with edge case values."""
    # Create a feed
    feed = RSSFeed(
        url="https://example.com/feed.xml",
        name="Test Feed",
        description="A test feed",
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db_session.add(feed)
    db_session.commit()
    
    # Create a log
    log = feed_processing_log.create_processing_started(db_session, feed_id=feed.id)
    
    # Update with edge case values
    updated_log = feed_processing_log.update_processing_completed(
        db_session,
        log_id=log.id,
        status="success",
        articles_found=0,  # Edge case: no articles found
        articles_added=0,  # Edge case: no articles added
        error_message=""   # Edge case: empty error message
    )
    
    # Verify the update
    assert updated_log is not None
    assert updated_log.status == "success"
    assert updated_log.articles_found == 0
    assert updated_log.articles_added == 0
    assert updated_log.error_message == ""
    
    # Create another log and update with different edge cases
    log2 = feed_processing_log.create_processing_started(db_session, feed_id=feed.id)
    
    # Update with very large values
    updated_log2 = feed_processing_log.update_processing_completed(
        db_session,
        log_id=log2.id,
        status="success",
        articles_found=1000000,  # Edge case: very large number
        articles_added=999999,   # Edge case: very large number
        error_message="E" * 1000  # Edge case: very long error message
    )
    
    # Verify the update
    assert updated_log2 is not None
    assert updated_log2.status == "success"
    assert updated_log2.articles_found == 1000000
    assert updated_log2.articles_added == 999999
    assert len(updated_log2.error_message) == 1000

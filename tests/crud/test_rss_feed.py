"""Tests for the RSS feed CRUD module."""

from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest
from sqlmodel import Session, select

from local_newsifier.crud.rss_feed import CRUDRSSFeed, rss_feed
from local_newsifier.models.rss_feed import RSSFeed


def test_get_by_url(db_session):
    """Test getting a feed by URL."""
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

    # Test getting by URL
    found_feed = rss_feed.get_by_url(db_session, url="https://example.com/feed.xml")
    assert found_feed is not None
    assert found_feed.url == "https://example.com/feed.xml"
    assert found_feed.name == "Test Feed"

    # Test with non-existent URL
    non_existent = rss_feed.get_by_url(db_session, url="https://nonexistent.com/feed.xml")
    assert non_existent is None


def test_get_active_feeds(db_session):
    """Test getting active feeds."""
    # Create active and inactive feeds
    feeds = [
        RSSFeed(
            url="https://example.com/feed1.xml",
            name="Active Feed 1",
            description="An active feed",
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        ),
        RSSFeed(
            url="https://example.com/feed2.xml",
            name="Active Feed 2",
            description="Another active feed",
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        ),
        RSSFeed(
            url="https://example.com/feed3.xml",
            name="Inactive Feed",
            description="An inactive feed",
            is_active=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        ),
    ]

    for feed in feeds:
        db_session.add(feed)
    db_session.commit()

    # Test getting active feeds
    active_feeds = rss_feed.get_active_feeds(db_session)
    assert len(active_feeds) == 2
    active_urls = [feed.url for feed in active_feeds]
    assert "https://example.com/feed1.xml" in active_urls
    assert "https://example.com/feed2.xml" in active_urls
    assert "https://example.com/feed3.xml" not in active_urls

    # Test pagination
    limited_feeds = rss_feed.get_active_feeds(db_session, skip=1, limit=1)
    assert len(limited_feeds) == 1


def test_update_last_fetched(db_session):
    """Test updating the last_fetched_at timestamp."""
    # Create a feed with an old last_fetched_at
    old_time = datetime.now(timezone.utc) - timedelta(days=1)
    feed = RSSFeed(
        url="https://example.com/feed.xml",
        name="Test Feed",
        description="A test feed",
        is_active=True,
        created_at=old_time,
        updated_at=old_time,
        last_fetched_at=old_time,
    )
    db_session.add(feed)
    db_session.commit()

    # Capture the current feed ID
    feed_id = feed.id

    # Update the last_fetched_at timestamp
    # Store the initial values
    initial_last_fetched = feed.last_fetched_at
    initial_updated_at = feed.updated_at

    # Force a small delay to ensure timestamps will be different
    import time

    time.sleep(0.01)

    # Update the feed
    updated_feed = rss_feed.update_last_fetched(db_session, id=feed_id)

    # Verify the feed was updated
    assert updated_feed is not None
    assert updated_feed.last_fetched_at > initial_last_fetched
    assert updated_feed.updated_at > initial_updated_at

    # Verify in the database
    db_feed = db_session.get(RSSFeed, feed_id)

    # Handle timezone-awareness for comparison
    if db_feed.last_fetched_at.tzinfo is None:
        # If the database returns naive datetime, convert it to aware
        last_fetched_aware = db_feed.last_fetched_at.replace(tzinfo=timezone.utc)
    else:
        last_fetched_aware = db_feed.last_fetched_at

    assert last_fetched_aware > old_time


def test_update_last_fetched_nonexistent(db_session):
    """Test updating the last_fetched_at timestamp for a non-existent feed."""
    result = rss_feed.update_last_fetched(db_session, id=999)
    assert result is None


def test_singleton_instance():
    """Test singleton instance behavior."""
    assert isinstance(rss_feed, CRUDRSSFeed)

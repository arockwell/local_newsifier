"""Tests for the error-handled RSS feed CRUD module."""

from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest
from sqlalchemy.exc import IntegrityError
from sqlmodel import select

from local_newsifier.crud.error_handled_base import (DuplicateEntityError,
                                                     EntityNotFoundError)
from local_newsifier.crud.error_handled_rss_feed import (
    ErrorHandledCRUDRSSFeed, error_handled_rss_feed)
from local_newsifier.models.rss_feed import RSSFeed


class TestErrorHandledRSSFeedCRUD:
    """Tests for ErrorHandledCRUDRSSFeed class."""

    def test_create(self, db_session):
        """Test creating a new RSS feed."""
        # Test data for a new feed
        feed_data = {
            "url": "https://example.com/test-feed.xml",
            "name": "Test Feed",
            "description": "A test RSS feed",
            "is_active": True,
        }

        # Create the feed
        feed = error_handled_rss_feed.create(db_session, obj_in=feed_data)

        # Verify it was created correctly
        assert feed is not None
        assert feed.id is not None
        assert feed.url == feed_data["url"]
        assert feed.name == feed_data["name"]
        assert feed.description == feed_data["description"]
        assert feed.is_active is True
        assert feed.created_at is not None
        assert feed.updated_at is not None

        # Verify it was saved to the database
        statement = select(RSSFeed).where(RSSFeed.id == feed.id)
        result = db_session.exec(statement).first()
        assert result is not None
        assert result.name == feed_data["name"]

    def test_create_duplicate_url(self, db_session):
        """Test creating a feed with a duplicate URL."""
        # Create a feed first
        feed_data = {
            "url": "https://example.com/duplicate-feed.xml",
            "name": "Original Feed",
            "description": "The original feed",
            "is_active": True,
        }
        error_handled_rss_feed.create(db_session, obj_in=feed_data)

        # Try to create another feed with the same URL
        duplicate_data = {
            "url": "https://example.com/duplicate-feed.xml",  # Same URL
            "name": "Duplicate Feed",
            "description": "A feed with a duplicate URL",
            "is_active": True,
        }

        # Mock the database error that would occur
        with patch.object(db_session, "commit") as mock_commit:
            # Simulate an IntegrityError for duplicate entry
            mock_commit.side_effect = IntegrityError(
                "UNIQUE constraint failed: rss_feeds.url", params=None, orig=None
            )

            with pytest.raises(DuplicateEntityError) as excinfo:
                error_handled_rss_feed.create(db_session, obj_in=duplicate_data)

            assert "Entity with these attributes already exists" in str(excinfo.value)
            assert excinfo.value.error_type == "validation"

    def test_get_by_url(self, db_session):
        """Test getting a feed by URL."""
        # Create a feed first
        feed_data = {
            "url": "https://example.com/get-by-url-feed.xml",
            "name": "Test Feed",
            "description": "A test feed for get_by_url",
            "is_active": True,
        }
        created_feed = error_handled_rss_feed.create(db_session, obj_in=feed_data)

        # Get the feed by URL
        feed = error_handled_rss_feed.get_by_url(
            db_session, url="https://example.com/get-by-url-feed.xml"
        )

        # Verify we got the right feed
        assert feed is not None
        assert feed.id == created_feed.id
        assert feed.name == created_feed.name
        assert feed.url == created_feed.url

    def test_get_by_url_not_found(self, db_session):
        """Test getting a non-existent feed by URL."""
        with pytest.raises(EntityNotFoundError) as excinfo:
            error_handled_rss_feed.get_by_url(
                db_session, url="https://example.com/nonexistent-feed.xml"
            )

        # Check error details
        assert (
            "RSS feed with URL 'https://example.com/nonexistent-feed.xml' not found"
            in str(excinfo.value)
        )
        assert excinfo.value.error_type == "not_found"
        assert (
            excinfo.value.context["url"] == "https://example.com/nonexistent-feed.xml"
        )

    def test_get_active_feeds(self, db_session):
        """Test getting active feeds with error handling."""
        # Create active and inactive feeds
        feeds_data = [
            {
                "url": "https://example.com/active1.xml",
                "name": "Active Feed 1",
                "description": "An active feed",
                "is_active": True,
            },
            {
                "url": "https://example.com/active2.xml",
                "name": "Active Feed 2",
                "description": "Another active feed",
                "is_active": True,
            },
            {
                "url": "https://example.com/inactive.xml",
                "name": "Inactive Feed",
                "description": "An inactive feed",
                "is_active": False,
            },
        ]

        for feed_data in feeds_data:
            error_handled_rss_feed.create(db_session, obj_in=feed_data)

        # Get active feeds
        active_feeds = error_handled_rss_feed.get_active_feeds(db_session)

        # Verify we got only active feeds
        assert len(active_feeds) == 2
        active_urls = [feed.url for feed in active_feeds]
        assert "https://example.com/active1.xml" in active_urls
        assert "https://example.com/active2.xml" in active_urls
        assert "https://example.com/inactive.xml" not in active_urls

        # Test pagination
        limited_feeds = error_handled_rss_feed.get_active_feeds(
            db_session, skip=1, limit=1
        )
        assert len(limited_feeds) == 1

    def test_update_last_fetched(self, db_session):
        """Test updating the last_fetched_at timestamp with error handling."""
        # Create a feed with an old last_fetched_at
        old_time = datetime.now(timezone.utc) - timedelta(days=1)
        feed_data = {
            "url": "https://example.com/update-feed.xml",
            "name": "Update Test Feed",
            "description": "A feed for testing updates",
            "is_active": True,
            "last_fetched_at": old_time,
        }
        created_feed = error_handled_rss_feed.create(db_session, obj_in=feed_data)

        # Store the initial values
        feed_id = created_feed.id
        initial_last_fetched = created_feed.last_fetched_at
        initial_updated_at = created_feed.updated_at

        # Force a small delay to ensure timestamps will be different
        import time

        time.sleep(0.01)

        # Update the last_fetched_at timestamp
        updated_feed = error_handled_rss_feed.update_last_fetched(
            db_session, id=feed_id
        )

        # Verify the feed was updated
        assert updated_feed is not None
        assert updated_feed.last_fetched_at > initial_last_fetched
        assert updated_feed.updated_at > initial_updated_at

        # Verify in the database
        db_feed = db_session.get(RSSFeed, feed_id)
        assert db_feed.last_fetched_at > old_time

    def test_update_last_fetched_not_found(self, db_session):
        """Test updating the last_fetched_at timestamp for a non-existent feed."""
        with pytest.raises(EntityNotFoundError) as excinfo:
            error_handled_rss_feed.update_last_fetched(db_session, id=999)

        assert "RSSFeed with id 999 not found" in str(excinfo.value)
        assert excinfo.value.error_type == "not_found"
        assert excinfo.value.context["id"] == 999

    def test_remove(self, db_session):
        """Test removing a feed with error handling."""
        # Create a feed first
        feed_data = {
            "url": "https://example.com/remove-feed.xml",
            "name": "Feed to Remove",
            "description": "A feed that will be removed",
            "is_active": True,
        }
        created_feed = error_handled_rss_feed.create(db_session, obj_in=feed_data)

        # Remove the feed
        removed_feed = error_handled_rss_feed.remove(db_session, id=created_feed.id)

        # Verify the returned feed is correct
        assert removed_feed is not None
        assert removed_feed.id == created_feed.id
        assert removed_feed.url == created_feed.url

        # Verify it was removed from the database
        db_feed = db_session.get(RSSFeed, created_feed.id)
        assert db_feed is None

    def test_remove_not_found(self, db_session):
        """Test removing a non-existent feed."""
        with pytest.raises(EntityNotFoundError) as excinfo:
            error_handled_rss_feed.remove(db_session, id=999)

        assert "RSSFeed with id 999 not found" in str(excinfo.value)
        assert excinfo.value.error_type == "not_found"

    def test_singleton_instance(self):
        """Test singleton instance behavior."""
        assert isinstance(error_handled_rss_feed, ErrorHandledCRUDRSSFeed)
        assert error_handled_rss_feed.model == RSSFeed

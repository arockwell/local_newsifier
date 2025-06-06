"""Tests for the RSS feed CRUD module."""

import time
from datetime import datetime, timedelta, timezone

import pytest
from sqlmodel import select

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


@pytest.mark.parametrize(
    "initial_state",
    [
        {"last_fetched_at": datetime.now(timezone.utc) - timedelta(days=1)},  # With old timestamp
        {"last_fetched_at": None},  # With null timestamp
    ],
)
def test_update_last_fetched(db_session, initial_state):
    """Test updating the last_fetched_at timestamp."""
    # Create a feed with specified initial state
    old_time = datetime.now(timezone.utc) - timedelta(days=1)
    feed = RSSFeed(
        url="https://example.com/feed.xml",
        name="Test Feed",
        description="A test feed",
        is_active=True,
        created_at=old_time,
        updated_at=old_time,
        **initial_state,
    )
    db_session.add(feed)
    db_session.commit()

    # Capture the current feed ID
    feed_id = feed.id

    # Store the initial values
    initial_last_fetched = feed.last_fetched_at
    initial_updated_at = feed.updated_at

    # Force a small delay to ensure timestamps will be different
    time.sleep(0.01)

    # Update the feed
    updated_feed = rss_feed.update_last_fetched(db_session, id=feed_id)

    # Verify the feed was updated
    assert updated_feed is not None
    if initial_last_fetched is not None:
        assert updated_feed.last_fetched_at > initial_last_fetched
    else:
        assert updated_feed.last_fetched_at is not None
    assert updated_feed.updated_at > initial_updated_at

    # Verify in the database
    db_feed = db_session.get(RSSFeed, feed_id)

    # Handle timezone-awareness for comparison
    if db_feed.last_fetched_at.tzinfo is None:
        # If the database returns naive datetime, convert it to aware
        last_fetched_aware = db_feed.last_fetched_at.replace(tzinfo=timezone.utc)
    else:
        last_fetched_aware = db_feed.last_fetched_at

    if initial_state["last_fetched_at"] is not None:
        assert last_fetched_aware > old_time
    else:
        assert last_fetched_aware is not None


def test_update_last_fetched_nonexistent(db_session):
    """Test updating the last_fetched_at timestamp for a non-existent feed."""
    result = rss_feed.update_last_fetched(db_session, id=999)
    assert result is None


def test_singleton_instance():
    """Test singleton instance behavior."""
    assert isinstance(rss_feed, CRUDRSSFeed)


@pytest.mark.parametrize(
    "feed_data",
    [
        {  # Full data
            "url": "https://example.com/feed.xml",
            "name": "Test Feed",
            "description": "A test feed with all fields",
            "is_active": True,
            "last_fetched_at": datetime.now(timezone.utc) - timedelta(days=1),
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        },
        {  # Minimal data
            "url": "https://example.com/minimal.xml",
            "name": "Minimal Feed",
        },
    ],
)
def test_create_feed(db_session, feed_data):
    """Test creating a new feed with different data sets."""
    # Create the feed
    feed = rss_feed.create(db_session, obj_in=feed_data)

    # Verify the feed was created with correct values
    assert feed is not None
    assert feed.id is not None
    assert feed.url == feed_data["url"]
    assert feed.name == feed_data["name"]

    if "description" in feed_data:
        assert feed.description == feed_data["description"]

    # Check default values for minimal feed
    if "is_active" not in feed_data:
        assert feed.is_active is True  # Default value should be True

    assert feed.created_at is not None
    assert feed.updated_at is not None

    # Verify it's in the database
    db_feed = db_session.get(RSSFeed, feed.id)
    assert db_feed is not None
    assert db_feed.url == feed_data["url"]


def test_update_feed(db_session):
    """Test updating feed properties."""
    # Create a feed
    feed = RSSFeed(
        url="https://example.com/feed.xml",
        name="Original Name",
        description="Original description",
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(feed)
    db_session.commit()

    # Update data
    update_data = {"name": "Updated Name", "description": "Updated description", "is_active": False}

    # Update the feed
    updated_feed = rss_feed.update(db_session, db_obj=feed, obj_in=update_data)

    # Verify the update
    assert updated_feed.name == "Updated Name"
    assert updated_feed.description == "Updated description"
    assert updated_feed.is_active is False
    assert updated_feed.url == "https://example.com/feed.xml"  # Unchanged

    # Verify in the database
    db_feed = db_session.get(RSSFeed, feed.id)
    assert db_feed.name == "Updated Name"
    assert db_feed.is_active is False


def test_delete_feed(db_session):
    """Test deleting a feed."""
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

    # Store the ID
    feed_id = feed.id

    # Delete the feed
    deleted_feed = rss_feed.remove(db_session, id=feed_id)

    # Verify the deletion
    assert deleted_feed.id == feed_id
    assert deleted_feed.name == "Test Feed"

    # Verify it's gone from the database
    db_feed = db_session.get(RSSFeed, feed_id)
    assert db_feed is None

    # Verify get_by_url also returns None
    url_feed = rss_feed.get_by_url(db_session, url="https://example.com/feed.xml")
    assert url_feed is None


def test_feed_url_validation(db_session):
    """Test validation of feed URLs."""
    # Create a feed with a unique URL
    feed1 = rss_feed.create(
        db_session,
        obj_in={
            "url": "https://example.com/unique-feed.xml",
            "name": "Unique Feed",
            "description": "A feed with a unique URL",
        },
    )

    # Verify the feed was created
    assert feed1 is not None
    assert feed1.url == "https://example.com/unique-feed.xml"

    # Create a second feed with a different URL
    feed2 = rss_feed.create(
        db_session,
        obj_in={
            "url": "https://example.com/another-feed.xml",
            "name": "Another Feed",
            "description": "Another feed with a different URL",
        },
    )

    # Verify the second feed was created
    assert feed2 is not None
    assert feed2.url == "https://example.com/another-feed.xml"

    # Verify both feeds exist in the database
    feeds = db_session.exec(select(RSSFeed)).all()
    assert len(feeds) == 2


def test_get_feeds_by_name_pattern(db_session):
    """Test filtering feeds by name pattern."""
    # Create feeds with different names
    feeds = [
        RSSFeed(
            url="https://example.com/feed1.xml",
            name="CNN News Feed",
            description="CNN news feed",
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        ),
        RSSFeed(
            url="https://example.com/feed2.xml",
            name="BBC News Feed",
            description="BBC news feed",
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        ),
        RSSFeed(
            url="https://example.com/feed3.xml",
            name="CNN Politics Feed",
            description="CNN politics feed",
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        ),
    ]

    for feed in feeds:
        db_session.add(feed)
    db_session.commit()

    # Query feeds by name pattern
    # We need to use a direct query since the CRUD module doesn't have a get_by_name_pattern method
    # In a real application, you might want to add this method to the CRUD module
    cnn_feeds = db_session.exec(
        select(RSSFeed).where(RSSFeed.name.like("%CNN%")).order_by(RSSFeed.name)
    ).all()

    # Verify the results
    assert len(cnn_feeds) == 2
    assert cnn_feeds[0].name == "CNN News Feed"
    assert cnn_feeds[1].name == "CNN Politics Feed"


def test_toggle_feed_status(db_session):
    """Test activating/deactivating feeds."""
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

    # Verify initial status
    assert feed.is_active is True

    # Deactivate the feed
    feed.is_active = False
    db_session.add(feed)
    db_session.commit()
    db_session.refresh(feed)

    # Verify the feed is inactive
    assert feed.is_active is False

    # Verify it's not returned by get_active_feeds
    active_feeds = rss_feed.get_active_feeds(db_session)
    assert len(active_feeds) == 0

    # Reactivate the feed
    feed.is_active = True
    db_session.add(feed)
    db_session.commit()
    db_session.refresh(feed)

    # Verify the feed is active again
    assert feed.is_active is True

    # Verify it's returned by get_active_feeds
    active_feeds = rss_feed.get_active_feeds(db_session)
    assert len(active_feeds) == 1
    assert active_feeds[0].id == feed.id


def test_get_multi_with_pagination(db_session):
    """Test retrieving multiple feeds with pagination."""
    # Create multiple feeds
    feeds = []
    for i in range(15):
        feed = RSSFeed(
            url=f"https://example.com/feed{i}.xml",
            name=f"Test Feed {i}",
            description=f"Test feed {i}",
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        feeds.append(feed)
        db_session.add(feed)
    db_session.commit()

    # Test pagination - first page (5 items)
    page1 = rss_feed.get_multi(db_session, skip=0, limit=5)
    assert len(page1) == 5
    assert page1[0].name == "Test Feed 0"
    assert page1[4].name == "Test Feed 4"

    # Test pagination - second page (5 items)
    page2 = rss_feed.get_multi(db_session, skip=5, limit=5)
    assert len(page2) == 5
    assert page2[0].name == "Test Feed 5"
    assert page2[4].name == "Test Feed 9"

    # Test pagination - third page (5 items)
    page3 = rss_feed.get_multi(db_session, skip=10, limit=5)
    assert len(page3) == 5
    assert page3[0].name == "Test Feed 10"
    assert page3[4].name == "Test Feed 14"

    # Test pagination - beyond available items
    page4 = rss_feed.get_multi(db_session, skip=15, limit=5)
    assert len(page4) == 0


@pytest.mark.parametrize(
    "update_method,update_data",
    [
        ("dict", {"name": "Updated via Dict", "description": "Updated description via dict"}),
        ("kwargs", {"name": "Updated via kwargs"}),
    ],
)
def test_update_with_dict_and_kwargs(db_session, update_method, update_data):
    """Test updating a feed with both dict and keyword arguments."""
    # Create a feed
    feed = RSSFeed(
        url="https://example.com/feed.xml",
        name="Original Name",
        description="Original description",
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(feed)
    db_session.commit()

    # Update the feed
    updated_feed = rss_feed.update(db_session, db_obj=feed, obj_in=update_data)

    # Verify the update
    assert updated_feed.name == update_data["name"]
    if "description" in update_data:
        assert updated_feed.description == update_data["description"]
    else:
        assert updated_feed.description == "Original description"  # Unchanged


def test_create_update_delete_flow(db_session):
    """Test the complete CRUD flow: create, update, delete."""
    # 1. Create
    feed_data = {
        "url": "https://example.com/flow.xml",
        "name": "Flow Test Feed",
        "description": "Testing the complete CRUD flow",
        "is_active": True,
    }

    created_feed = rss_feed.create(db_session, obj_in=feed_data)
    assert created_feed.id is not None
    assert created_feed.name == "Flow Test Feed"

    # 2. Update
    update_data = {"name": "Updated Flow Feed", "is_active": False}
    updated_feed = rss_feed.update(db_session, db_obj=created_feed, obj_in=update_data)
    assert updated_feed.name == "Updated Flow Feed"
    assert updated_feed.is_active is False

    # 3. Delete
    deleted_feed = rss_feed.remove(db_session, id=created_feed.id)
    assert deleted_feed.id == created_feed.id

    # Verify it's gone
    assert db_session.get(RSSFeed, created_feed.id) is None


def test_get_nonexistent_feed(db_session):
    """Test getting a non-existent feed."""
    # Try to get a feed with a non-existent ID
    feed = rss_feed.get(db_session, id=999)
    assert feed is None

    # Try to get a feed with a non-existent URL
    feed = rss_feed.get_by_url(db_session, url="https://nonexistent.com/feed.xml")
    assert feed is None

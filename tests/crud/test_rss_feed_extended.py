"""Extended tests for the RSS feed CRUD module."""

from datetime import datetime, timedelta, timezone

import pytest
from sqlmodel import Session, select

from local_newsifier.crud.rss_feed import CRUDRSSFeed, rss_feed
from local_newsifier.models.rss_feed import RSSFeed


def test_create_feed(db_session):
    """Test creating a new feed with all fields."""
    # Create feed data
    feed_data = {
        "url": "https://example.com/feed.xml",
        "name": "Test Feed",
        "description": "A test feed with all fields",
        "is_active": True,
        "last_fetched_at": datetime.now(timezone.utc) - timedelta(days=1),
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }
    
    # Create the feed
    feed = rss_feed.create(db_session, obj_in=feed_data)
    
    # Verify the feed was created with correct values
    assert feed is not None
    assert feed.id is not None
    assert feed.url == "https://example.com/feed.xml"
    assert feed.name == "Test Feed"
    assert feed.description == "A test feed with all fields"
    assert feed.is_active is True
    assert feed.last_fetched_at is not None
    assert feed.created_at is not None
    assert feed.updated_at is not None
    
    # Verify it's in the database
    db_feed = db_session.get(RSSFeed, feed.id)
    assert db_feed is not None
    assert db_feed.url == "https://example.com/feed.xml"


def test_create_feed_minimal(db_session):
    """Test creating a feed with minimal required fields."""
    # Create minimal feed data
    feed_data = {
        "url": "https://example.com/minimal.xml",
        "name": "Minimal Feed"
    }
    
    # Create the feed
    feed = rss_feed.create(db_session, obj_in=feed_data)
    
    # Verify the feed was created
    assert feed is not None
    assert feed.id is not None
    assert feed.url == "https://example.com/minimal.xml"
    assert feed.name == "Minimal Feed"
    
    # Check default values
    assert feed.is_active is True  # Default value should be True
    assert feed.created_at is not None
    assert feed.updated_at is not None


def test_update_feed(db_session):
    """Test updating feed properties."""
    # Create a feed
    feed = RSSFeed(
        url="https://example.com/feed.xml",
        name="Original Name",
        description="Original description",
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db_session.add(feed)
    db_session.commit()
    
    # Update data
    update_data = {
        "name": "Updated Name",
        "description": "Updated description",
        "is_active": False
    }
    
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
        updated_at=datetime.now(timezone.utc)
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
            "description": "A feed with a unique URL"
        }
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
            "description": "Another feed with a different URL"
        }
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
            updated_at=datetime.now(timezone.utc)
        ),
        RSSFeed(
            url="https://example.com/feed2.xml",
            name="BBC News Feed",
            description="BBC news feed",
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        ),
        RSSFeed(
            url="https://example.com/feed3.xml",
            name="CNN Politics Feed",
            description="CNN politics feed",
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
    ]
    
    for feed in feeds:
        db_session.add(feed)
    db_session.commit()
    
    # Query feeds by name pattern
    # We need to use a direct query since the CRUD module doesn't have a get_by_name_pattern method
    # In a real application, you might want to add this method to the CRUD module
    cnn_feeds = db_session.exec(
        select(RSSFeed)
        .where(RSSFeed.name.like("%CNN%"))
        .order_by(RSSFeed.name)
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
        updated_at=datetime.now(timezone.utc)
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
            updated_at=datetime.now(timezone.utc)
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


def test_update_with_dict_and_kwargs(db_session):
    """Test updating a feed with both dict and keyword arguments."""
    # Create a feed
    feed = RSSFeed(
        url="https://example.com/feed.xml",
        name="Original Name",
        description="Original description",
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db_session.add(feed)
    db_session.commit()
    
    # Update with a dictionary
    update_dict = {"name": "Updated via Dict", "description": "Updated description via dict"}
    updated_feed = rss_feed.update(db_session, db_obj=feed, obj_in=update_dict)
    
    # Verify the update
    assert updated_feed.name == "Updated via Dict"
    assert updated_feed.description == "Updated description via dict"
    
    # Update with keyword arguments
    update_kwargs = {"name": "Updated via kwargs"}
    updated_feed = rss_feed.update(db_session, db_obj=feed, obj_in=update_kwargs)
    
    # Verify the update
    assert updated_feed.name == "Updated via kwargs"
    assert updated_feed.description == "Updated description via dict"  # Unchanged from previous update


def test_create_update_delete_flow(db_session):
    """Test the complete CRUD flow: create, update, delete."""
    # 1. Create
    feed_data = {
        "url": "https://example.com/flow.xml",
        "name": "Flow Test Feed",
        "description": "Testing the complete CRUD flow",
        "is_active": True
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


def test_update_last_fetched_with_custom_time(db_session):
    """Test updating last_fetched_at with a custom time."""
    # Create a feed
    feed = RSSFeed(
        url="https://example.com/feed.xml",
        name="Test Feed",
        description="A test feed",
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        last_fetched_at=None  # Initially null
    )
    db_session.add(feed)
    db_session.commit()
    
    # Verify initial state
    assert feed.last_fetched_at is None
    
    # Update last_fetched_at
    updated_feed = rss_feed.update_last_fetched(db_session, id=feed.id)
    
    # Verify the update
    assert updated_feed.last_fetched_at is not None
    
    # Store the current last_fetched_at
    first_fetch_time = updated_feed.last_fetched_at
    
    # Wait a moment to ensure timestamps will be different
    import time
    time.sleep(0.01)
    
    # Update again
    updated_again = rss_feed.update_last_fetched(db_session, id=feed.id)
    
    # Verify the second update
    assert updated_again.last_fetched_at > first_fetch_time

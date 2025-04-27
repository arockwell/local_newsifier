"""Tests for the RSSFeedService."""

import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch, call

from local_newsifier.services.rss_feed_service import (
    RSSFeedService,
    register_process_article_task,
    register_article_service,
    _process_article_task,
)
from local_newsifier.models.rss_feed import RSSFeed, RSSFeedProcessingLog


@pytest.fixture
def reset_global_task():
    """Reset the global task variable before and after tests."""
    global _process_article_task
    original = _process_article_task
    _process_article_task = None
    yield
    _process_article_task = original


@pytest.fixture
def mock_db_session():
    """Create a mock database session."""
    return MagicMock()


@pytest.fixture
def mock_session_factory(mock_db_session):
    """Create a mock session factory that returns the mock session."""
    mock_factory = MagicMock()
    mock_factory.return_value = mock_db_session
    return mock_factory


def test_get_feed_found(mock_db_session, mock_session_factory):
    """Test retrieving an existing feed by ID."""
    # Arrange
    mock_rss_feed_crud = MagicMock()
    mock_feed = MagicMock()
    mock_feed.id = 1
    mock_feed.url = "https://example.com/feed"
    mock_feed.name = "Example Feed"
    mock_feed.description = "Example description"
    mock_feed.is_active = True
    mock_feed.last_fetched_at = datetime(2025, 1, 1, tzinfo=timezone.utc)
    mock_feed.created_at = datetime(2025, 1, 1, tzinfo=timezone.utc)
    mock_feed.updated_at = datetime(2025, 1, 1, tzinfo=timezone.utc)
    
    mock_rss_feed_crud.get.return_value = mock_feed
    
    # Create service with session factory
    service = RSSFeedService(
        rss_feed_crud=mock_rss_feed_crud,
        feed_processing_log_crud=MagicMock(),
        article_service=MagicMock(),
        session_factory=mock_session_factory
    )
    
    # Act
    result = service.get_feed(1)
    
    # Assert
    mock_rss_feed_crud.get.assert_called_once_with(mock_db_session, id=1)
    assert result["id"] == 1
    assert result["url"] == "https://example.com/feed"
    assert result["name"] == "Example Feed"
    assert result["description"] == "Example description"
    assert result["is_active"] is True
    assert "created_at" in result
    assert "updated_at" in result


def test_get_feed_not_found(mock_db_session, mock_session_factory):
    """Test retrieving a non-existent feed by ID."""
    # Arrange
    mock_rss_feed_crud = MagicMock()
    mock_rss_feed_crud.get.return_value = None
    
    # Create service with session factory
    service = RSSFeedService(
        rss_feed_crud=mock_rss_feed_crud,
        feed_processing_log_crud=MagicMock(),
        article_service=MagicMock(),
        session_factory=mock_session_factory
    )
    
    # Act
    result = service.get_feed(999)
    
    # Assert
    mock_rss_feed_crud.get.assert_called_once_with(mock_db_session, id=999)
    assert result is None


def test_get_feed_by_url_found(mock_db_session, mock_session_factory):
    """Test retrieving an existing feed by URL."""
    # Arrange
    url = "https://example.com/feed"
    mock_rss_feed_crud = MagicMock()
    mock_feed = MagicMock()
    mock_feed.id = 1
    mock_feed.url = url
    mock_feed.name = "Example Feed"
    mock_feed.description = "Example description"
    mock_feed.is_active = True
    mock_feed.last_fetched_at = datetime(2025, 1, 1, tzinfo=timezone.utc)
    mock_feed.created_at = datetime(2025, 1, 1, tzinfo=timezone.utc)
    mock_feed.updated_at = datetime(2025, 1, 1, tzinfo=timezone.utc)
    
    mock_rss_feed_crud.get_by_url.return_value = mock_feed
    
    # Create service with session factory
    service = RSSFeedService(
        rss_feed_crud=mock_rss_feed_crud,
        feed_processing_log_crud=MagicMock(),
        article_service=MagicMock(),
        session_factory=mock_session_factory
    )
    
    # Act
    result = service.get_feed_by_url(url)
    
    # Assert
    mock_rss_feed_crud.get_by_url.assert_called_once_with(mock_db_session, url=url)
    assert result["id"] == 1
    assert result["url"] == url
    assert result["name"] == "Example Feed"


def test_get_feed_by_url_not_found(mock_db_session, mock_session_factory):
    """Test retrieving a non-existent feed by URL."""
    # Arrange
    url = "https://example.com/nonexistent"
    mock_rss_feed_crud = MagicMock()
    mock_rss_feed_crud.get_by_url.return_value = None
    
    # Create service with session factory
    service = RSSFeedService(
        rss_feed_crud=mock_rss_feed_crud,
        feed_processing_log_crud=MagicMock(),
        article_service=MagicMock(),
        session_factory=mock_session_factory
    )
    
    # Act
    result = service.get_feed_by_url(url)
    
    # Assert
    mock_rss_feed_crud.get_by_url.assert_called_once_with(mock_db_session, url=url)
    assert result is None


def test_list_feeds_all(mock_db_session, mock_session_factory):
    """Test listing all feeds."""
    # Arrange
    mock_rss_feed_crud = MagicMock()
    
    mock_feed1 = MagicMock()
    mock_feed1.id = 1
    mock_feed1.url = "https://example.com/feed1"
    mock_feed1.name = "Feed 1"
    mock_feed1.description = "Description 1"
    mock_feed1.is_active = True
    mock_feed1.created_at = datetime(2025, 1, 1, tzinfo=timezone.utc)
    mock_feed1.updated_at = datetime(2025, 1, 1, tzinfo=timezone.utc)
    
    mock_feed2 = MagicMock()
    mock_feed2.id = 2
    mock_feed2.url = "https://example.com/feed2"
    mock_feed2.name = "Feed 2"
    mock_feed2.description = "Description 2"
    mock_feed2.is_active = False
    mock_feed2.created_at = datetime(2025, 1, 2, tzinfo=timezone.utc)
    mock_feed2.updated_at = datetime(2025, 1, 2, tzinfo=timezone.utc)
    
    mock_feeds = [mock_feed1, mock_feed2]
    mock_rss_feed_crud.get_multi.return_value = mock_feeds
    
    # Create service with session factory
    service = RSSFeedService(
        rss_feed_crud=mock_rss_feed_crud,
        feed_processing_log_crud=MagicMock(),
        article_service=MagicMock(),
        session_factory=mock_session_factory
    )
    
    # Act
    result = service.list_feeds(skip=0, limit=10, active_only=False)
    
    # Assert
    mock_rss_feed_crud.get_multi.assert_called_once_with(
        mock_db_session, skip=0, limit=10
    )
    assert len(result) == 2
    assert result[0]["id"] == 1
    assert result[0]["name"] == "Feed 1"
    assert result[1]["id"] == 2
    assert result[1]["name"] == "Feed 2"


def test_list_feeds_active_only(mock_db_session, mock_session_factory):
    """Test listing active feeds only."""
    # Arrange
    mock_rss_feed_crud = MagicMock()
    
    mock_feed = MagicMock()
    mock_feed.id = 1
    mock_feed.url = "https://example.com/feed1"
    mock_feed.name = "Feed 1"
    mock_feed.description = "Description 1"
    mock_feed.is_active = True
    mock_feed.created_at = datetime(2025, 1, 1, tzinfo=timezone.utc)
    mock_feed.updated_at = datetime(2025, 1, 1, tzinfo=timezone.utc)
    
    mock_feeds = [mock_feed]
    mock_rss_feed_crud.get_active_feeds.return_value = mock_feeds
    
    # Create service with session factory
    service = RSSFeedService(
        rss_feed_crud=mock_rss_feed_crud,
        feed_processing_log_crud=MagicMock(),
        article_service=MagicMock(),
        session_factory=mock_session_factory
    )
    
    # Act
    result = service.list_feeds(skip=0, limit=10, active_only=True)
    
    # Assert
    mock_rss_feed_crud.get_active_feeds.assert_called_once_with(
        mock_db_session, skip=0, limit=10
    )
    assert len(result) == 1
    assert result[0]["id"] == 1
    assert result[0]["name"] == "Feed 1"
    assert result[0]["is_active"] is True


def test_create_feed_success(mock_db_session, mock_session_factory):
    """Test creating a new feed successfully."""
    # Arrange
    url = "https://example.com/newfeed"
    name = "New Feed"
    description = "New feed description"
    
    mock_rss_feed_crud = MagicMock()
    mock_rss_feed_crud.get_by_url.return_value = None  # Feed doesn't exist yet
    
    mock_new_feed = MagicMock()
    mock_new_feed.id = 1
    mock_new_feed.url = url
    mock_new_feed.name = name
    mock_new_feed.description = description
    mock_new_feed.is_active = True
    mock_new_feed.created_at = datetime(2025, 1, 1, tzinfo=timezone.utc)
    mock_new_feed.updated_at = datetime(2025, 1, 1, tzinfo=timezone.utc)
    
    mock_rss_feed_crud.create.return_value = mock_new_feed
    
    # Create service with session factory
    service = RSSFeedService(
        rss_feed_crud=mock_rss_feed_crud,
        feed_processing_log_crud=MagicMock(),
        article_service=MagicMock(),
        session_factory=mock_session_factory
    )
    
    # Act
    result = service.create_feed(url=url, name=name, description=description)
    
    # Assert
    mock_rss_feed_crud.get_by_url.assert_called_once_with(mock_db_session, url=url)
    mock_rss_feed_crud.create.assert_called_once()
    
    assert result["id"] == 1
    assert result["url"] == url
    assert result["name"] == name
    assert result["description"] == description
    assert result["is_active"] is True


def test_create_feed_already_exists(mock_db_session, mock_session_factory):
    """Test creating a feed that already exists."""
    # Arrange
    url = "https://example.com/existingfeed"
    name = "Existing Feed"
    description = "Existing feed description"
    
    mock_rss_feed_crud = MagicMock()
    
    mock_existing_feed = MagicMock()
    mock_existing_feed.id = 1
    mock_existing_feed.url = url
    mock_existing_feed.name = "Original Name"  # Different from what we're trying to create
    mock_existing_feed.description = "Original description"
    mock_existing_feed.is_active = True
    
    mock_rss_feed_crud.get_by_url.return_value = mock_existing_feed
    
    # Create service with session factory
    service = RSSFeedService(
        rss_feed_crud=mock_rss_feed_crud,
        feed_processing_log_crud=MagicMock(),
        article_service=MagicMock(),
        session_factory=mock_session_factory
    )
    
    # Act & Assert
    with pytest.raises(ValueError, match=f"Feed with URL '{url}' already exists"):
        service.create_feed(url=url, name=name, description=description)
    
    mock_rss_feed_crud.get_by_url.assert_called_once_with(mock_db_session, url=url)
    mock_rss_feed_crud.create.assert_not_called()


def test_update_feed_success(mock_db_session, mock_session_factory):
    """Test updating a feed successfully."""
    # Arrange
    feed_id = 1
    new_name = "Updated Feed"
    new_description = "Updated description"
    new_active_status = False
    
    mock_rss_feed_crud = MagicMock()
    
    mock_existing_feed = MagicMock()
    mock_existing_feed.id = feed_id
    mock_existing_feed.url = "https://example.com/feed"
    mock_existing_feed.name = "Original Name"
    mock_existing_feed.description = "Original description"
    mock_existing_feed.is_active = True
    mock_existing_feed.created_at = datetime(2025, 1, 1, tzinfo=timezone.utc)
    mock_existing_feed.updated_at = datetime(2025, 1, 1, tzinfo=timezone.utc)
    
    mock_updated_feed = MagicMock()
    mock_updated_feed.id = feed_id
    mock_updated_feed.url = "https://example.com/feed"
    mock_updated_feed.name = new_name
    mock_updated_feed.description = new_description
    mock_updated_feed.is_active = new_active_status
    mock_updated_feed.created_at = datetime(2025, 1, 1, tzinfo=timezone.utc)
    mock_updated_feed.updated_at = datetime(2025, 1, 2, tzinfo=timezone.utc)  # Updated timestamp
    
    mock_rss_feed_crud.get.return_value = mock_existing_feed
    mock_rss_feed_crud.update.return_value = mock_updated_feed
    
    # Create service with session factory
    service = RSSFeedService(
        rss_feed_crud=mock_rss_feed_crud,
        feed_processing_log_crud=MagicMock(),
        article_service=MagicMock(),
        session_factory=mock_session_factory
    )
    
    # Act
    result = service.update_feed(
        feed_id=feed_id,
        name=new_name,
        description=new_description,
        is_active=new_active_status
    )
    
    # Assert
    mock_rss_feed_crud.get.assert_called_once_with(mock_db_session, id=feed_id)
    mock_rss_feed_crud.update.assert_called_once()
    
    assert result["id"] == feed_id
    assert result["name"] == new_name
    assert result["description"] == new_description
    assert result["is_active"] == new_active_status


def test_update_feed_not_found(mock_db_session, mock_session_factory):
    """Test updating a feed that doesn't exist."""
    # Arrange
    feed_id = 999
    new_name = "Updated Feed"
    
    mock_rss_feed_crud = MagicMock()
    mock_rss_feed_crud.get.return_value = None
    
    # Create service with session factory
    service = RSSFeedService(
        rss_feed_crud=mock_rss_feed_crud,
        feed_processing_log_crud=MagicMock(),
        article_service=MagicMock(),
        session_factory=mock_session_factory
    )
    
    # Act
    result = service.update_feed(feed_id=feed_id, name=new_name)
    
    # Assert
    mock_rss_feed_crud.get.assert_called_once_with(mock_db_session, id=feed_id)
    mock_rss_feed_crud.update.assert_not_called()
    assert result is None


def test_update_feed_partial(mock_db_session, mock_session_factory):
    """Test updating only some fields of a feed."""
    # Arrange
    feed_id = 1
    new_name = "Updated Feed"
    
    mock_rss_feed_crud = MagicMock()
    
    mock_existing_feed = MagicMock()
    mock_existing_feed.id = feed_id
    mock_existing_feed.url = "https://example.com/feed"
    mock_existing_feed.name = "Original Name"
    mock_existing_feed.description = "Original description"
    mock_existing_feed.is_active = True
    mock_existing_feed.created_at = datetime(2025, 1, 1, tzinfo=timezone.utc)
    mock_existing_feed.updated_at = datetime(2025, 1, 1, tzinfo=timezone.utc)
    
    mock_updated_feed = MagicMock()
    mock_updated_feed.id = feed_id
    mock_updated_feed.url = "https://example.com/feed"
    mock_updated_feed.name = new_name
    mock_updated_feed.description = "Original description"  # Unchanged
    mock_updated_feed.is_active = True  # Unchanged
    mock_updated_feed.created_at = datetime(2025, 1, 1, tzinfo=timezone.utc)
    mock_updated_feed.updated_at = datetime(2025, 1, 2, tzinfo=timezone.utc)  # Updated timestamp
    
    mock_rss_feed_crud.get.return_value = mock_existing_feed
    mock_rss_feed_crud.update.return_value = mock_updated_feed
    
    # Create service with session factory
    service = RSSFeedService(
        rss_feed_crud=mock_rss_feed_crud,
        feed_processing_log_crud=MagicMock(),
        article_service=MagicMock(),
        session_factory=mock_session_factory
    )
    
    # Act - only update name
    result = service.update_feed(feed_id=feed_id, name=new_name)
    
    # Assert
    mock_rss_feed_crud.get.assert_called_once_with(mock_db_session, id=feed_id)
    mock_rss_feed_crud.update.assert_called_once()
    
    # Verify only specified fields were changed
    assert result["id"] == feed_id
    assert result["name"] == new_name
    assert result["description"] == "Original description"
    assert result["is_active"] is True


def test_remove_feed_success(mock_db_session, mock_session_factory):
    """Test removing a feed successfully."""
    # Arrange
    feed_id = 1
    
    mock_rss_feed_crud = MagicMock()
    
    mock_feed = MagicMock()
    mock_feed.id = feed_id
    mock_feed.url = "https://example.com/feed"
    mock_feed.name = "Feed to Remove"
    mock_feed.description = "This feed will be removed"
    mock_feed.is_active = True
    mock_feed.created_at = datetime(2025, 1, 1, tzinfo=timezone.utc)
    mock_feed.updated_at = datetime(2025, 1, 1, tzinfo=timezone.utc)
    
    mock_rss_feed_crud.get.return_value = mock_feed
    mock_rss_feed_crud.remove.return_value = mock_feed  # Successfully removed feed
    
    # Create service with session factory
    service = RSSFeedService(
        rss_feed_crud=mock_rss_feed_crud,
        feed_processing_log_crud=MagicMock(),
        article_service=MagicMock(),
        session_factory=mock_session_factory
    )
    
    # Act
    result = service.remove_feed(feed_id)
    
    # Assert
    mock_rss_feed_crud.get.assert_called_once_with(mock_db_session, id=feed_id)
    mock_rss_feed_crud.remove.assert_called_once_with(mock_db_session, id=feed_id)
    
    assert result["id"] == feed_id
    assert result["name"] == "Feed to Remove"


def test_remove_feed_not_found(mock_db_session, mock_session_factory):
    """Test removing a feed that doesn't exist."""
    # Arrange
    feed_id = 999
    
    mock_rss_feed_crud = MagicMock()
    mock_rss_feed_crud.get.return_value = None
    
    # Create service with session factory
    service = RSSFeedService(
        rss_feed_crud=mock_rss_feed_crud,
        feed_processing_log_crud=MagicMock(),
        article_service=MagicMock(),
        session_factory=mock_session_factory
    )
    
    # Act
    result = service.remove_feed(feed_id)
    
    # Assert
    mock_rss_feed_crud.get.assert_called_once_with(mock_db_session, id=feed_id)
    mock_rss_feed_crud.remove.assert_not_called()
    assert result is None


def test_remove_feed_removal_failed(mock_db_session, mock_session_factory):
    """Test when feed removal fails for some reason."""
    # Arrange
    feed_id = 1
    
    mock_rss_feed_crud = MagicMock()
    
    mock_feed = MagicMock()
    mock_feed.id = feed_id
    mock_feed.url = "https://example.com/feed"
    mock_feed.name = "Feed to Remove"
    mock_feed.description = "This feed will be removed"
    mock_feed.is_active = True
    
    mock_rss_feed_crud.get.return_value = mock_feed
    mock_rss_feed_crud.remove.return_value = None  # Removal failed
    
    # Create service with session factory
    service = RSSFeedService(
        rss_feed_crud=mock_rss_feed_crud,
        feed_processing_log_crud=MagicMock(),
        article_service=MagicMock(),
        session_factory=mock_session_factory
    )
    
    # Act
    result = service.remove_feed(feed_id)
    
    # Assert
    mock_rss_feed_crud.get.assert_called_once_with(mock_db_session, id=feed_id)
    mock_rss_feed_crud.remove.assert_called_once_with(mock_db_session, id=feed_id)
    assert result is None


@patch('local_newsifier.services.rss_feed_service.parse_rss_feed')
def test_process_feed_success(mock_parse_rss_feed, mock_db_session, mock_session_factory):
    """Test processing a feed successfully."""
    # Arrange
    feed_id = 1
    
    # Mock RSS feed
    mock_rss_feed_crud = MagicMock()
    
    mock_feed = MagicMock()
    mock_feed.id = feed_id
    mock_feed.url = "https://example.com/feed"
    mock_feed.name = "Example Feed"
    
    mock_rss_feed_crud.get.return_value = mock_feed
    
    # Mock feed processing log
    mock_feed_processing_log_crud = MagicMock()
    
    mock_log = MagicMock()
    mock_log.id = 1
    mock_log.feed_id = feed_id
    
    mock_feed_processing_log_crud.create_processing_started.return_value = mock_log
    
    # Mock article service
    mock_article_service = MagicMock()
    mock_article_service.create_article_from_rss_entry.return_value = 123  # Article ID
    
    # Mock RSS data
    mock_parse_rss_feed.return_value = {
        "feed": {
            "title": "Example Feed",
            "link": "https://example.com",
            "description": "An example feed"
        },
        "entries": [
            {
                "title": "Article 1",
                "link": "https://example.com/article1",
                "description": "First article"
            },
            {
                "title": "Article 2",
                "link": "https://example.com/article2",
                "description": "Second article"
            }
        ]
    }
    
    # Mock task queue function
    mock_task_queue_func = MagicMock()
    
    # Create service with session factory
    service = RSSFeedService(
        rss_feed_crud=mock_rss_feed_crud,
        feed_processing_log_crud=mock_feed_processing_log_crud,
        article_service=mock_article_service,
        session_factory=mock_session_factory
    )
    
    # Act
    result = service.process_feed(feed_id, task_queue_func=mock_task_queue_func)
    
    # Assert
    mock_rss_feed_crud.get.assert_called_once_with(mock_db_session, id=feed_id)
    mock_parse_rss_feed.assert_called_once_with(mock_feed.url)
    mock_feed_processing_log_crud.create_processing_started.assert_called_once_with(
        mock_db_session, feed_id=feed_id
    )
    mock_feed_processing_log_crud.update_processing_completed.assert_called_once()
    
    assert mock_article_service.create_article_from_rss_entry.call_count == 2
    assert mock_task_queue_func.call_count == 2
    
    assert result["status"] == "success"
    assert result["feed_id"] == feed_id
    assert result["feed_name"] == "Example Feed"
    assert result["articles_found"] == 2
    assert result["articles_added"] == 2
    
    # Verify feed last fetched time was updated
    mock_rss_feed_crud.update_last_fetched.assert_called_once_with(mock_db_session, id=feed_id)


@patch('local_newsifier.services.rss_feed_service.parse_rss_feed')
def test_process_feed_with_global_task_func(mock_parse_rss_feed, reset_global_task, mock_db_session, mock_session_factory):
    """Test processing a feed with the global task function."""
    # Arrange
    global _process_article_task
    feed_id = 1
    
    # Set up global task
    mock_global_task = MagicMock()
    mock_global_task.delay = MagicMock()
    _process_article_task = mock_global_task
    
    # Mock RSS feed
    mock_rss_feed_crud = MagicMock()
    
    mock_feed = MagicMock()
    mock_feed.id = feed_id
    mock_feed.url = "https://example.com/feed"
    mock_feed.name = "Example Feed"
    
    mock_rss_feed_crud.get.return_value = mock_feed
    
    # Mock feed processing log
    mock_feed_processing_log_crud = MagicMock()
    
    mock_log = MagicMock()
    mock_log.id = 1
    mock_log.feed_id = feed_id
    
    mock_feed_processing_log_crud.create_processing_started.return_value = mock_log
    
    # Mock article service
    mock_article_service = MagicMock()
    mock_article_service.create_article_from_rss_entry.return_value = 123  # Article ID
    
    # Mock RSS data
    mock_parse_rss_feed.return_value = {
        "feed": {
            "title": "Example Feed",
            "link": "https://example.com",
            "description": "An example feed"
        },
        "entries": [
            {
                "title": "Article 1",
                "link": "https://example.com/article1",
                "description": "First article"
            },
            {
                "title": "Article 2",
                "link": "https://example.com/article2",
                "description": "Second article"
            }
        ]
    }
    
    # Mock session manager
    mock_session = MagicMock()
    
    # Create service with session factory
    service = RSSFeedService(
        rss_feed_crud=mock_rss_feed_crud,
        feed_processing_log_crud=mock_feed_processing_log_crud,
        article_service=mock_article_service,
        session_factory=mock_session_factory
    )
    
    # Act
    result = service.process_feed(feed_id)
    
    # Assert
    assert mock_article_service.create_article_from_rss_entry.call_count == 2
    assert mock_global_task.delay.call_count == 2
    mock_global_task.delay.assert_any_call(123)
    
    assert result["status"] == "success"
    assert result["articles_added"] == 2


@patch('local_newsifier.services.rss_feed_service.ArticleService')
@patch('local_newsifier.services.rss_feed_service.parse_rss_feed')
def test_process_feed_no_service_no_task(mock_parse_rss_feed, mock_article_service_class, reset_global_task, mock_db_session, mock_session_factory):
    """Test processing a feed with no article service and no global task."""
    # Arrange
    global _process_article_task
    feed_id = 1
    _process_article_task = None  # Ensure global task is None
    
    # Mock RSS feed
    mock_rss_feed_crud = MagicMock()
    
    mock_feed = MagicMock()
    mock_feed.id = feed_id
    mock_feed.url = "https://example.com/feed"
    mock_feed.name = "Example Feed"
    
    mock_rss_feed_crud.get.return_value = mock_feed
    
    # Mock feed processing log
    mock_feed_processing_log_crud = MagicMock()
    
    mock_log = MagicMock()
    mock_log.id = 1
    mock_log.feed_id = feed_id
    
    mock_feed_processing_log_crud.create_processing_started.return_value = mock_log
    
    # Mock RSS data
    mock_parse_rss_feed.return_value = {
        "feed": {
            "title": "Example Feed",
            "link": "https://example.com",
            "description": "An example feed"
        },
        "entries": [
            {
                "title": "Article 1",
                "link": "https://example.com/article1",
                "description": "First article"
            },
            {
                "title": "Article 2",
                "link": "https://example.com/article2",
                "description": "Second article"
            }
        ]
    }
    
    # Mock temporary article service
    mock_temp_article_service = MagicMock()
    mock_temp_article_service.create_article_from_rss_entry.return_value = 123
    mock_article_service_class.return_value = mock_temp_article_service
    
    # Create service with no article service
    service = RSSFeedService(
        rss_feed_crud=mock_rss_feed_crud,
        feed_processing_log_crud=mock_feed_processing_log_crud,
        article_service=None,  # No article service
        session_factory=mock_session_factory
    )
    
    # Act
    result = service.process_feed(feed_id)
    
    # Assert
    mock_article_service_class.assert_called_once()
    assert mock_temp_article_service.create_article_from_rss_entry.call_count == 2
    
    assert result["status"] == "success"
    assert result["feed_id"] == feed_id
    assert result["feed_name"] == "Example Feed"
    assert result["articles_found"] == 2
    assert result["articles_added"] == 2


@patch('local_newsifier.services.rss_feed_service.ArticleService', side_effect=ImportError("Mock import error"))
@patch('local_newsifier.services.rss_feed_service.parse_rss_feed')
def test_process_feed_temp_service_fails(mock_parse_rss_feed, mock_article_service_class, reset_global_task, mock_db_session, mock_session_factory):
    """Test handling when temporary article service creation fails."""
    # Arrange
    global _process_article_task
    feed_id = 1
    _process_article_task = None  # Ensure global task is None
    
    # Mock RSS feed
    mock_rss_feed_crud = MagicMock()
    
    mock_feed = MagicMock()
    mock_feed.id = feed_id
    mock_feed.url = "https://example.com/feed"
    mock_feed.name = "Example Feed"
    
    mock_rss_feed_crud.get.return_value = mock_feed
    
    # Mock feed processing log
    mock_feed_processing_log_crud = MagicMock()
    
    mock_log = MagicMock()
    mock_log.id = 1
    mock_log.feed_id = feed_id
    
    mock_feed_processing_log_crud.create_processing_started.return_value = mock_log
    
    # Mock RSS data
    mock_parse_rss_feed.return_value = {
        "feed": {"title": "Example Feed"},
        "entries": [{"title": "Article 1"}, {"title": "Article 2"}]
    }
    
    # Create service with no article service
    service = RSSFeedService(
        rss_feed_crud=mock_rss_feed_crud,
        feed_processing_log_crud=mock_feed_processing_log_crud,
        article_service=None,  # No article service
        session_factory=mock_session_factory
    )
    
    # Act & Assert
    with pytest.raises(ValueError, match="Article service not initialized and failed to create temporary service"):
        service.process_feed(feed_id)
    
    mock_article_service_class.assert_called_once()


def test_process_feed_feed_not_found(mock_db_session, mock_session_factory):
    """Test handling when feed is not found."""
    # Arrange
    feed_id = 999
    
    # Mock RSS feed - not found
    mock_rss_feed_crud = MagicMock()
    mock_rss_feed_crud.get.return_value = None
    
    # Create service
    service = RSSFeedService(
        rss_feed_crud=mock_rss_feed_crud,
        feed_processing_log_crud=MagicMock(),
        article_service=MagicMock(),
        session_factory=mock_session_factory
    )
    
    # Act
    result = service.process_feed(feed_id)
    
    # Assert
    mock_rss_feed_crud.get.assert_called_once_with(mock_db_session, id=feed_id)
    
    assert result["status"] == "error"
    assert f"Feed with ID {feed_id} not found" in result["message"]


@patch('local_newsifier.services.rss_feed_service.parse_rss_feed', side_effect=Exception("Mock parsing error"))
def test_process_feed_parse_error(mock_parse_rss_feed, mock_db_session, mock_session_factory):
    """Test handling when RSS parsing fails."""
    # Arrange
    feed_id = 1
    
    # Mock RSS feed
    mock_rss_feed_crud = MagicMock()
    
    mock_feed = MagicMock()
    mock_feed.id = feed_id
    mock_feed.url = "https://example.com/feed"
    mock_feed.name = "Example Feed"
    
    mock_rss_feed_crud.get.return_value = mock_feed
    
    # Mock feed processing log
    mock_feed_processing_log_crud = MagicMock()
    
    mock_log = MagicMock()
    mock_log.id = 1
    mock_log.feed_id = feed_id
    
    mock_feed_processing_log_crud.create_processing_started.return_value = mock_log
    
    # Create service
    service = RSSFeedService(
        rss_feed_crud=mock_rss_feed_crud,
        feed_processing_log_crud=mock_feed_processing_log_crud,
        article_service=MagicMock(),
        session_factory=mock_session_factory
    )
    
    # Act
    result = service.process_feed(feed_id)
    
    # Assert
    mock_parse_rss_feed.assert_called_once_with(mock_feed.url)
    mock_feed_processing_log_crud.update_processing_completed.assert_called_once_with(
        mock_db_session,
        log_id=mock_log.id,
        status="error",
        error_message="Mock parsing error",
    )
    
    assert result["status"] == "error"
    assert result["feed_id"] == feed_id
    assert "Mock parsing error" in result["message"]


def test_get_feed_processing_logs(mock_db_session, mock_session_factory):
    """Test getting processing logs for a feed."""
    # Arrange
    feed_id = 1
    
    # Mock feed processing logs
    mock_feed_processing_log_crud = MagicMock()
    
    mock_log1 = MagicMock()
    mock_log1.id = 1
    mock_log1.feed_id = feed_id
    mock_log1.status = "success"
    mock_log1.articles_found = 10
    mock_log1.articles_added = 8
    mock_log1.error_message = None
    mock_log1.started_at = datetime(2025, 1, 1, tzinfo=timezone.utc)
    mock_log1.completed_at = datetime(2025, 1, 1, 1, tzinfo=timezone.utc)
    
    mock_log2 = MagicMock()
    mock_log2.id = 2
    mock_log2.feed_id = feed_id
    mock_log2.status = "error"
    mock_log2.articles_found = 0
    mock_log2.articles_added = 0
    mock_log2.error_message = "Connection error"
    mock_log2.started_at = datetime(2025, 1, 2, tzinfo=timezone.utc)
    mock_log2.completed_at = datetime(2025, 1, 2, 0, 1, tzinfo=timezone.utc)
    
    mock_logs = [mock_log1, mock_log2]
    mock_feed_processing_log_crud.get_by_feed_id.return_value = mock_logs
    
    # Create service
    service = RSSFeedService(
        rss_feed_crud=MagicMock(),
        feed_processing_log_crud=mock_feed_processing_log_crud,
        article_service=MagicMock(),
        session_factory=mock_session_factory
    )
    
    # Act
    result = service.get_feed_processing_logs(feed_id)
    
    # Assert
    mock_feed_processing_log_crud.get_by_feed_id.assert_called_once_with(
        mock_db_session, feed_id=feed_id, skip=0, limit=100
    )
    
    assert len(result) == 2
    assert result[0]["id"] == 1
    assert result[0]["status"] == "success"
    assert result[0]["articles_found"] == 10
    assert result[0]["articles_added"] == 8
    
    assert result[1]["id"] == 2
    assert result[1]["status"] == "error"
    assert result[1]["error_message"] == "Connection error"


def test_register_process_article_task(reset_global_task):
    """Test registering the process article task."""
    # Arrange
    global _process_article_task
    _process_article_task = None
    
    # Create mock task
    mock_task = MagicMock()
    
    # Act
    register_process_article_task(mock_task)
    
    # Assert
    assert _process_article_task == mock_task


def test_register_article_service():
    """Test registering the article service."""
    # Arrange
    # Use a copy of the instance to avoid affecting other tests
    from local_newsifier.services.rss_feed_service import rss_feed_service
    original_service = rss_feed_service.article_service
    
    # Test service doesn't have to match the real implementation
    mock_article_service = MagicMock()
    
    # Act
    try:
        register_article_service(mock_article_service)
        
        # Assert
        assert rss_feed_service.article_service == mock_article_service
    finally:
        # Restore original service to avoid affecting other tests
        rss_feed_service.article_service = original_service

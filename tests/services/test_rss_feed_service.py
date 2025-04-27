"""Tests for RSS feed service."""
import json
from datetime import datetime, timezone
from unittest.mock import MagicMock, Mock, patch

import pytest
from sqlmodel import Session

from local_newsifier.services.rss_feed_service import (
    RSSFeedService,
    register_process_article_task,
    register_article_service,
    rss_feed_service,
    _process_article_task,
)
from local_newsifier.models.rss_feed import RSSFeed, RSSFeedProcessingLog


@pytest.fixture
def mock_rss_feed_crud():
    """Fixture for mock RSS feed CRUD."""
    mock = MagicMock()
    return mock


@pytest.fixture
def mock_feed_processing_log_crud():
    """Fixture for mock feed processing log CRUD."""
    mock = MagicMock()
    return mock


@pytest.fixture
def mock_article_service():
    """Fixture for mock article service."""
    mock = MagicMock()
    return mock


@pytest.fixture
def mock_session_factory():
    """Fixture for mock session factory."""
    mock_session = MagicMock(spec=Session)
    
    # Mock the context manager behavior
    mock_context = MagicMock()
    mock_context.__enter__ = MagicMock(return_value=mock_session)
    mock_context.__exit__ = MagicMock(return_value=None)
    
    mock_factory = MagicMock(return_value=mock_context)
    return mock_factory, mock_session


@pytest.fixture
def rss_feed_service_instance(
    mock_rss_feed_crud,
    mock_feed_processing_log_crud,
    mock_article_service,
    mock_session_factory,
):
    """Fixture for RSS feed service instance."""
    mock_factory, _ = mock_session_factory
    return RSSFeedService(
        rss_feed_crud=mock_rss_feed_crud,
        feed_processing_log_crud=mock_feed_processing_log_crud,
        article_service=mock_article_service,
        session_factory=mock_factory,
    )


@pytest.fixture
def sample_feed():
    """Fixture for sample feed."""
    return RSSFeed(
        id=1,
        url="https://example.com/feed",
        name="Example Feed",
        description="An example RSS feed",
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        last_fetched_at=None,
    )


@pytest.fixture
def sample_processing_log():
    """Fixture for sample processing log."""
    return RSSFeedProcessingLog(
        id=1,
        feed_id=1,
        status="success",
        articles_found=10,
        articles_added=5,
        error_message=None,
        started_at=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def sample_rss_entry():
    """Fixture for sample RSS entry."""
    return {
        "title": "Example Article",
        "link": "https://example.com/article",
        "description": "An example article",
        "published": "Mon, 01 Jan 2023 00:00:00 GMT",
        "id": "https://example.com/article",
        "summary": "An example article summary",
    }


@pytest.fixture
def sample_feed_data():
    """Fixture for sample feed data."""
    return {
        "feed": {
            "title": "Example Feed",
            "link": "https://example.com",
            "description": "An example RSS feed",
        },
        "entries": [
            {
                "title": "Example Article 1",
                "link": "https://example.com/article1",
                "description": "An example article 1",
                "published": "Mon, 01 Jan 2023 00:00:00 GMT",
                "id": "https://example.com/article1",
                "summary": "An example article 1 summary",
            },
            {
                "title": "Example Article 2",
                "link": "https://example.com/article2",
                "description": "An example article 2",
                "published": "Tue, 02 Jan 2023 00:00:00 GMT",
                "id": "https://example.com/article2",
                "summary": "An example article 2 summary",
            },
        ],
    }


class TestRSSFeedService:
    """Tests for RSS feed service."""

    def test_get_session_with_factory(self, rss_feed_service_instance, mock_session_factory):
        """Test _get_session with factory."""
        _, mock_session = mock_session_factory
        
        # Call the method
        session = rss_feed_service_instance._get_session()
        
        # Verify that the session factory was called
        rss_feed_service_instance.session_factory.assert_called_once()
        
        # Verify that the returned session is the mock session
        assert session == mock_session

    @patch("local_newsifier.services.rss_feed_service.get_session")
    def test_get_session_without_factory(self, mock_get_session):
        """Test _get_session without factory."""
        # Create a service instance without a session factory
        service = RSSFeedService()
        
        # Set up the mock
        mock_session = MagicMock()
        mock_get_session.return_value = iter([mock_session])
        
        # Call the method
        session = service._get_session()
        
        # Verify that get_session was called
        mock_get_session.assert_called_once()
        
        # Verify that the returned session is the mock session
        assert session == mock_session

    def test_get_feed_found(
        self, rss_feed_service_instance, mock_rss_feed_crud, sample_feed, mock_session_factory
    ):
        """Test get_feed with existing feed."""
        _, mock_session = mock_session_factory
        
        # Set up the mock
        mock_rss_feed_crud.get.return_value = sample_feed
        
        # Call the method
        result = rss_feed_service_instance.get_feed(1)
        
        # Verify that the CRUD method was called
        mock_rss_feed_crud.get.assert_called_once_with(mock_session, id=1)
        
        # Verify the result
        assert result["id"] == sample_feed.id
        assert result["url"] == sample_feed.url
        assert result["name"] == sample_feed.name
        assert result["description"] == sample_feed.description
        assert result["is_active"] == sample_feed.is_active
        assert result["last_fetched_at"] is None
        assert result["created_at"] == sample_feed.created_at.isoformat()
        assert result["updated_at"] == sample_feed.updated_at.isoformat()

    def test_get_feed_not_found(
        self, rss_feed_service_instance, mock_rss_feed_crud, mock_session_factory
    ):
        """Test get_feed with non-existing feed."""
        _, mock_session = mock_session_factory
        
        # Set up the mock
        mock_rss_feed_crud.get.return_value = None
        
        # Call the method
        result = rss_feed_service_instance.get_feed(1)
        
        # Verify that the CRUD method was called
        mock_rss_feed_crud.get.assert_called_once_with(mock_session, id=1)
        
        # Verify the result
        assert result is None

    def test_get_feed_by_url_found(
        self, rss_feed_service_instance, mock_rss_feed_crud, sample_feed, mock_session_factory
    ):
        """Test get_feed_by_url with existing feed."""
        _, mock_session = mock_session_factory
        url = "https://example.com/feed"
        
        # Set up the mock
        mock_rss_feed_crud.get_by_url.return_value = sample_feed
        
        # Call the method
        result = rss_feed_service_instance.get_feed_by_url(url)
        
        # Verify that the CRUD method was called
        mock_rss_feed_crud.get_by_url.assert_called_once_with(mock_session, url=url)
        
        # Verify the result
        assert result["id"] == sample_feed.id
        assert result["url"] == sample_feed.url
        assert result["name"] == sample_feed.name
        assert result["description"] == sample_feed.description
        assert result["is_active"] == sample_feed.is_active
        assert result["created_at"] == sample_feed.created_at.isoformat()
        assert result["updated_at"] == sample_feed.updated_at.isoformat()

    def test_get_feed_by_url_not_found(
        self, rss_feed_service_instance, mock_rss_feed_crud, mock_session_factory
    ):
        """Test get_feed_by_url with non-existing feed."""
        _, mock_session = mock_session_factory
        url = "https://example.com/feed"
        
        # Set up the mock
        mock_rss_feed_crud.get_by_url.return_value = None
        
        # Call the method
        result = rss_feed_service_instance.get_feed_by_url(url)
        
        # Verify that the CRUD method was called
        mock_rss_feed_crud.get_by_url.assert_called_once_with(mock_session, url=url)
        
        # Verify the result
        assert result is None

    def test_list_feeds_all(
        self, rss_feed_service_instance, mock_rss_feed_crud, sample_feed, mock_session_factory
    ):
        """Test list_feeds with all feeds."""
        _, mock_session = mock_session_factory
        
        # Set up the mock
        mock_rss_feed_crud.get_multi.return_value = [sample_feed]
        
        # Call the method
        result = rss_feed_service_instance.list_feeds(skip=0, limit=100, active_only=False)
        
        # Verify that the CRUD method was called
        mock_rss_feed_crud.get_multi.assert_called_once_with(mock_session, skip=0, limit=100)
        
        # Verify the result
        assert len(result) == 1
        assert result[0]["id"] == sample_feed.id
        assert result[0]["url"] == sample_feed.url
        assert result[0]["name"] == sample_feed.name
        assert result[0]["description"] == sample_feed.description
        assert result[0]["is_active"] == sample_feed.is_active
        assert result[0]["created_at"] == sample_feed.created_at.isoformat()
        assert result[0]["updated_at"] == sample_feed.updated_at.isoformat()

    def test_list_feeds_active_only(
        self, rss_feed_service_instance, mock_rss_feed_crud, sample_feed, mock_session_factory
    ):
        """Test list_feeds with active feeds only."""
        _, mock_session = mock_session_factory
        
        # Set up the mock
        mock_rss_feed_crud.get_active_feeds.return_value = [sample_feed]
        
        # Call the method
        result = rss_feed_service_instance.list_feeds(skip=0, limit=100, active_only=True)
        
        # Verify that the CRUD method was called
        mock_rss_feed_crud.get_active_feeds.assert_called_once_with(mock_session, skip=0, limit=100)
        
        # Verify the result
        assert len(result) == 1
        assert result[0]["id"] == sample_feed.id
        assert result[0]["url"] == sample_feed.url
        assert result[0]["name"] == sample_feed.name
        assert result[0]["description"] == sample_feed.description
        assert result[0]["is_active"] == sample_feed.is_active
        assert result[0]["created_at"] == sample_feed.created_at.isoformat()
        assert result[0]["updated_at"] == sample_feed.updated_at.isoformat()

    def test_create_feed_success(
        self, rss_feed_service_instance, mock_rss_feed_crud, sample_feed, mock_session_factory
    ):
        """Test create_feed with success."""
        _, mock_session = mock_session_factory
        url = "https://example.com/feed"
        name = "Example Feed"
        description = "An example RSS feed"
        
        # Set up the mock - no existing feed, create successful
        mock_rss_feed_crud.get_by_url.return_value = None
        mock_rss_feed_crud.create.return_value = sample_feed
        
        # Call the method
        result = rss_feed_service_instance.create_feed(url, name, description)
        
        # Verify that the CRUD methods were called
        mock_rss_feed_crud.get_by_url.assert_called_once_with(mock_session, url=url)
        mock_rss_feed_crud.create.assert_called_once()
        
        # Verify the create parameters
        create_args = mock_rss_feed_crud.create.call_args[0]
        create_kwargs = mock_rss_feed_crud.create.call_args[1]
        assert create_args[0] == mock_session
        assert create_kwargs["obj_in"]["url"] == url
        assert create_kwargs["obj_in"]["name"] == name
        assert create_kwargs["obj_in"]["description"] == description
        assert create_kwargs["obj_in"]["is_active"] is True
        
        # Verify the result
        assert result["id"] == sample_feed.id
        assert result["url"] == sample_feed.url
        assert result["name"] == sample_feed.name
        assert result["description"] == sample_feed.description
        assert result["is_active"] == sample_feed.is_active
        assert result["created_at"] == sample_feed.created_at.isoformat()
        assert result["updated_at"] == sample_feed.updated_at.isoformat()

    def test_create_feed_already_exists(
        self, rss_feed_service_instance, mock_rss_feed_crud, sample_feed, mock_session_factory
    ):
        """Test create_feed with existing feed."""
        _, mock_session = mock_session_factory
        url = "https://example.com/feed"
        name = "Example Feed"
        description = "An example RSS feed"
        
        # Set up the mock - existing feed found
        mock_rss_feed_crud.get_by_url.return_value = sample_feed
        
        # Call the method and expect an exception
        with pytest.raises(ValueError, match=f"Feed with URL '{url}' already exists"):
            rss_feed_service_instance.create_feed(url, name, description)
        
        # Verify that the CRUD methods were called
        mock_rss_feed_crud.get_by_url.assert_called_once_with(mock_session, url=url)
        mock_rss_feed_crud.create.assert_not_called()

    def test_update_feed_success(
        self, rss_feed_service_instance, mock_rss_feed_crud, sample_feed, mock_session_factory
    ):
        """Test update_feed with success."""
        _, mock_session = mock_session_factory
        feed_id = 1
        name = "Updated Feed"
        description = "An updated RSS feed"
        is_active = False
        
        # Clone the sample feed for the updated version
        updated_feed = RSSFeed(**sample_feed.dict())
        updated_feed.name = name
        updated_feed.description = description
        updated_feed.is_active = is_active
        
        # Set up the mock
        mock_rss_feed_crud.get.return_value = sample_feed
        mock_rss_feed_crud.update.return_value = updated_feed
        
        # Call the method
        result = rss_feed_service_instance.update_feed(
            feed_id, name=name, description=description, is_active=is_active
        )
        
        # Verify that the CRUD methods were called
        mock_rss_feed_crud.get.assert_called_once_with(mock_session, id=feed_id)
        mock_rss_feed_crud.update.assert_called_once()
        
        # Verify the update parameters
        update_args = mock_rss_feed_crud.update.call_args[0]
        update_kwargs = mock_rss_feed_crud.update.call_args[1]
        assert update_args[0] == mock_session
        assert update_kwargs["db_obj"] == sample_feed
        assert update_kwargs["obj_in"]["name"] == name
        assert update_kwargs["obj_in"]["description"] == description
        assert update_kwargs["obj_in"]["is_active"] is is_active
        assert "updated_at" in update_kwargs["obj_in"]
        
        # Verify the result
        assert result["id"] == updated_feed.id
        assert result["name"] == updated_feed.name
        assert result["description"] == updated_feed.description
        assert result["is_active"] == updated_feed.is_active
        assert result["created_at"] == updated_feed.created_at.isoformat()
        assert result["updated_at"] == updated_feed.updated_at.isoformat()

    def test_update_feed_not_found(
        self, rss_feed_service_instance, mock_rss_feed_crud, mock_session_factory
    ):
        """Test update_feed with non-existing feed."""
        _, mock_session = mock_session_factory
        feed_id = 1
        name = "Updated Feed"
        
        # Set up the mock
        mock_rss_feed_crud.get.return_value = None
        
        # Call the method
        result = rss_feed_service_instance.update_feed(feed_id, name=name)
        
        # Verify that the CRUD methods were called
        mock_rss_feed_crud.get.assert_called_once_with(mock_session, id=feed_id)
        mock_rss_feed_crud.update.assert_not_called()
        
        # Verify the result
        assert result is None

    def test_update_feed_partial(
        self, rss_feed_service_instance, mock_rss_feed_crud, sample_feed, mock_session_factory
    ):
        """Test update_feed with partial update."""
        _, mock_session = mock_session_factory
        feed_id = 1
        name = "Updated Feed"
        
        # Clone the sample feed for the updated version
        updated_feed = RSSFeed(**sample_feed.dict())
        updated_feed.name = name
        
        # Set up the mock
        mock_rss_feed_crud.get.return_value = sample_feed
        mock_rss_feed_crud.update.return_value = updated_feed
        
        # Call the method with only name parameter
        result = rss_feed_service_instance.update_feed(feed_id, name=name)
        
        # Verify that the CRUD methods were called
        mock_rss_feed_crud.get.assert_called_once_with(mock_session, id=feed_id)
        mock_rss_feed_crud.update.assert_called_once()
        
        # Verify the update parameters - only name and updated_at should be present
        update_kwargs = mock_rss_feed_crud.update.call_args[1]
        assert update_kwargs["obj_in"]["name"] == name
        assert "description" not in update_kwargs["obj_in"]
        assert "is_active" not in update_kwargs["obj_in"]
        assert "updated_at" in update_kwargs["obj_in"]
        
        # Verify the result
        assert result["id"] == updated_feed.id
        assert result["name"] == updated_feed.name
        assert result["description"] == updated_feed.description
        assert result["is_active"] == updated_feed.is_active
        assert result["created_at"] == updated_feed.created_at.isoformat()
        assert result["updated_at"] == updated_feed.updated_at.isoformat()

    def test_remove_feed_success(
        self, rss_feed_service_instance, mock_rss_feed_crud, sample_feed, mock_session_factory
    ):
        """Test remove_feed with success."""
        _, mock_session = mock_session_factory
        feed_id = 1
        
        # Set up the mock
        mock_rss_feed_crud.get.return_value = sample_feed
        mock_rss_feed_crud.remove.return_value = sample_feed
        
        # Call the method
        result = rss_feed_service_instance.remove_feed(feed_id)
        
        # Verify that the CRUD methods were called
        mock_rss_feed_crud.get.assert_called_once_with(mock_session, id=feed_id)
        mock_rss_feed_crud.remove.assert_called_once_with(mock_session, id=feed_id)
        
        # Verify the result
        assert result["id"] == sample_feed.id
        assert result["url"] == sample_feed.url
        assert result["name"] == sample_feed.name
        assert result["description"] == sample_feed.description
        assert result["is_active"] == sample_feed.is_active
        assert result["created_at"] == sample_feed.created_at.isoformat()
        assert result["updated_at"] == sample_feed.updated_at.isoformat()

    def test_remove_feed_not_found(
        self, rss_feed_service_instance, mock_rss_feed_crud, mock_session_factory
    ):
        """Test remove_feed with non-existing feed."""
        _, mock_session = mock_session_factory
        feed_id = 1
        
        # Set up the mock
        mock_rss_feed_crud.get.return_value = None
        
        # Call the method
        result = rss_feed_service_instance.remove_feed(feed_id)
        
        # Verify that the CRUD methods were called
        mock_rss_feed_crud.get.assert_called_once_with(mock_session, id=feed_id)
        mock_rss_feed_crud.remove.assert_not_called()
        
        # Verify the result
        assert result is None

    def test_remove_feed_removal_failed(
        self, rss_feed_service_instance, mock_rss_feed_crud, sample_feed, mock_session_factory
    ):
        """Test remove_feed with removal failure."""
        _, mock_session = mock_session_factory
        feed_id = 1
        
        # Set up the mock
        mock_rss_feed_crud.get.return_value = sample_feed
        mock_rss_feed_crud.remove.return_value = None  # Removal failed
        
        # Call the method
        result = rss_feed_service_instance.remove_feed(feed_id)
        
        # Verify that the CRUD methods were called
        mock_rss_feed_crud.get.assert_called_once_with(mock_session, id=feed_id)
        mock_rss_feed_crud.remove.assert_called_once_with(mock_session, id=feed_id)
        
        # Verify the result
        assert result is None

    @patch("local_newsifier.services.rss_feed_service.parse_rss_feed")
    def test_process_feed_success(
        self, 
        mock_parse_rss_feed, 
        rss_feed_service_instance,
        mock_rss_feed_crud,
        mock_feed_processing_log_crud,
        mock_article_service,
        mock_session_factory,
        sample_feed,
        sample_processing_log,
        sample_feed_data
    ):
        """Test process_feed with success."""
        _, mock_session = mock_session_factory
        feed_id = 1
        
        # Set up the mocks
        mock_rss_feed_crud.get.return_value = sample_feed
        mock_feed_processing_log_crud.create_processing_started.return_value = sample_processing_log
        mock_parse_rss_feed.return_value = sample_feed_data
        mock_article_service.create_article_from_rss_entry.return_value = 123  # Article ID
        
        # Mock the task queue function
        mock_task_queue_func = MagicMock()
        
        # Call the method
        result = rss_feed_service_instance.process_feed(feed_id, task_queue_func=mock_task_queue_func)
        
        # Verify the RSSFeed CRUD methods were called
        mock_rss_feed_crud.get.assert_called_once_with(mock_session, id=feed_id)
        mock_rss_feed_crud.update_last_fetched.assert_called_once_with(mock_session, id=feed_id)
        
        # Verify the FeedProcessingLog CRUD methods were called
        mock_feed_processing_log_crud.create_processing_started.assert_called_once_with(
            mock_session, feed_id=feed_id
        )
        mock_feed_processing_log_crud.update_processing_completed.assert_called_once_with(
            mock_session,
            log_id=sample_processing_log.id,
            status="success",
            articles_found=2,  # Two entries in sample_feed_data
            articles_added=2,  # Both should be added
        )
        
        # Verify that the article service method was called for each entry
        assert mock_article_service.create_article_from_rss_entry.call_count == 2
        
        # Verify that the task queue function was called for each article
        assert mock_task_queue_func.call_count == 2
        mock_task_queue_func.assert_any_call(123)
        
        # Verify the result
        assert result["status"] == "success"
        assert result["feed_id"] == feed_id
        assert result["feed_name"] == sample_feed.name
        assert result["articles_found"] == 2
        assert result["articles_added"] == 2

    @patch("local_newsifier.services.rss_feed_service.parse_rss_feed")
    def test_process_feed_with_global_task_func(
        self, 
        mock_parse_rss_feed, 
        rss_feed_service_instance,
        mock_rss_feed_crud,
        mock_feed_processing_log_crud,
        mock_article_service,
        mock_session_factory,
        sample_feed,
        sample_processing_log,
        sample_feed_data
    ):
        """Test process_feed with global task function."""
        # Declare the variable as global first
        global _process_article_task
        # Then save the original global task function
        orig_task = _process_article_task
        
        _, mock_session = mock_session_factory
        feed_id = 1
        
        # Set up the mocks
        mock_rss_feed_crud.get.return_value = sample_feed
        mock_feed_processing_log_crud.create_processing_started.return_value = sample_processing_log
        mock_parse_rss_feed.return_value = sample_feed_data
        mock_article_service.create_article_from_rss_entry.return_value = 123  # Article ID
        mock_global_task = MagicMock()
        mock_global_task.delay = MagicMock()
        _process_article_task = mock_global_task
        
        try:
            # Call the method without task_queue_func
            result = rss_feed_service_instance.process_feed(feed_id)
            
            # Verify that the global task function was called for each article
            assert mock_global_task.delay.call_count == 2
            mock_global_task.delay.assert_any_call(123)
            
            # Verify the result
            assert result["status"] == "success"
            assert result["feed_id"] == feed_id
            assert result["articles_found"] == 2
            assert result["articles_added"] == 2
        finally:
            # Restore the original global task
            _process_article_task = orig_task

    @patch("local_newsifier.services.rss_feed_service.parse_rss_feed")
    def test_process_feed_no_service_no_task(
        self, 
        mock_parse_rss_feed, 
        mock_rss_feed_crud,
        mock_feed_processing_log_crud,
        mock_session_factory,
        sample_feed,
        sample_processing_log,
        sample_feed_data
    ):
        """Test process_feed with no article service and no task function."""
        # Declare the variable as global first
        global _process_article_task
        # Then save the original global task function 
        orig_task = _process_article_task
        
        _, mock_session = mock_session_factory
        feed_id = 1
        
        # Create a service instance with no article service
        service = RSSFeedService(
            rss_feed_crud=mock_rss_feed_crud,
            feed_processing_log_crud=mock_feed_processing_log_crud,
            article_service=None,
            session_factory=mock_session_factory[0],
        )
        
        # Set up the mocks
        mock_rss_feed_crud.get.return_value = sample_feed
        mock_feed_processing_log_crud.create_processing_started.return_value = sample_processing_log
        mock_parse_rss_feed.return_value = sample_feed_data
        _process_article_task = None
        
        try:
            # Mock the article service import and creation
            with patch("local_newsifier.services.rss_feed_service.ArticleService") as mock_article_service_class:
                mock_temp_article_service = MagicMock()
                mock_article_service_class.return_value = mock_temp_article_service
                mock_temp_article_service.create_article_from_rss_entry.return_value = 123  # Article ID
                
                # Mock the article_crud and analysis_result_crud imports
                with patch("local_newsifier.services.rss_feed_service.article") as mock_article_crud, \
                     patch("local_newsifier.services.rss_feed_service.analysis_result") as mock_analysis_result_crud, \
                     patch("local_newsifier.services.rss_feed_service.SessionManager") as mock_session_manager:
                    
                    # Call the method
                    result = service.process_feed(feed_id)
                    
                    # Verify that the temporary article service was created and used
                    mock_article_service_class.assert_called_once()
                    assert mock_temp_article_service.create_article_from_rss_entry.call_count == 2
                    
                    # Verify the result
                    assert result["status"] == "success"
                    assert result["feed_id"] == feed_id
                    assert result["articles_found"] == 2
                    assert result["articles_added"] == 2
                    
                    # Verify warnings were logged (this would be in the real logs)
                    # We can't easily test this aspect without mocking the logger
        finally:
            # Restore the original global task
            _process_article_task = orig_task

    @patch("local_newsifier.services.rss_feed_service.parse_rss_feed")
    def test_process_feed_temp_service_fails(
        self, 
        mock_parse_rss_feed, 
        mock_rss_feed_crud,
        mock_feed_processing_log_crud,
        mock_session_factory,
        sample_feed,
        sample_processing_log,
        sample_feed_data
    ):
        """Test process_feed with no article service and temp service creation fails."""
        # Declare the variable as global first
        global _process_article_task
        # Then save the original global task function
        orig_task = _process_article_task
        
        _, mock_session = mock_session_factory
        feed_id = 1
        
        # Create a service instance with no article service
        service = RSSFeedService(
            rss_feed_crud=mock_rss_feed_crud,
            feed_processing_log_crud=mock_feed_processing_log_crud,
            article_service=None,
            session_factory=mock_session_factory[0],
        )
        
        # Set up the mocks
        mock_rss_feed_crud.get.return_value = sample_feed
        mock_feed_processing_log_crud.create_processing_started.return_value = sample_processing_log
        mock_parse_rss_feed.return_value = sample_feed_data
        _process_article_task = None
        
        try:
            # Mock the article service import to raise an exception
            with patch("local_newsifier.services.rss_feed_service.ArticleService", side_effect=ImportError("Mock import error")), \
                 patch("local_newsifier.services.rss_feed_service.logger.error") as mock_logger_error:
                
                # Call the method and expect an exception
                with pytest.raises(ValueError, match="Article service not initialized and failed to create temporary service"):
                    service.process_feed(feed_id)
                
                # Verify that the error was logged
                mock_logger_error.assert_called_once()
                assert "Failed to create temporary article service" in mock_logger_error.call_args[0][0]
        finally:
            # Restore the original global task
            _process_article_task = orig_task

    @patch("local_newsifier.services.rss_feed_service.parse_rss_feed")
    def test_process_feed_feed_not_found(
        self, 
        mock_parse_rss_feed, 
        rss_feed_service_instance,
        mock_rss_feed_crud,
        mock_session_factory
    ):
        """Test process_feed with non-existing feed."""
        _, mock_session = mock_session_factory
        feed_id = 999  # Non-existing feed ID
        
        # Set up the mock
        mock_rss_feed_crud.get.return_value = None
        
        # Call the method
        result = rss_feed_service_instance.process_feed(feed_id)
        
        # Verify that the CRUD method was called
        mock_rss_feed_crud.get.assert_called_once_with(mock_session, id=feed_id)
        
        # Verify the result
        assert result["status"] == "error"
        assert f"Feed with ID {feed_id} not found" in result["message"]
        
        # Verify that no further processing was done
        mock_parse_rss_feed.assert_not_called()

    @patch("local_newsifier.services.rss_feed_service.parse_rss_feed")
    def test_process_feed_parse_error(
        self, 
        mock_parse_rss_feed, 
        rss_feed_service_instance,
        mock_rss_feed_crud,
        mock_feed_processing_log_crud,
        mock_session_factory,
        sample_feed,
        sample_processing_log
    ):
        """Test process_feed with RSS parsing error."""
        _, mock_session = mock_session_factory
        feed_id = 1
        
        # Set up the mocks
        mock_rss_feed_crud.get.return_value = sample_feed
        mock_feed_processing_log_crud.create_processing_started.return_value = sample_processing_log
        
        # Make parse_rss_feed raise an exception
        mock_parse_rss_feed.side_effect = Exception("Mock parsing error")
        
        # Call the method
        result = rss_feed_service_instance.process_feed(feed_id)
        
        # Verify that the CRUD methods were called
        mock_rss_feed_crud.get.assert_called_once_with(mock_session, id=feed_id)
        mock_feed_processing_log_crud.create_processing_started.assert_called_once_with(
            mock_session, feed_id=feed_id
        )
        
        # Verify that the error was logged in the processing log
        mock_feed_processing_log_crud.update_processing_completed.assert_called_once_with(
            mock_session,
            log_id=sample_processing_log.id,
            status="error",
            error_message="Mock parsing error",
        )
        
        # Verify the result
        assert result["status"] == "error"
        assert result["feed_id"] == feed_id
        assert result["feed_name"] == sample_feed.name
        assert "Mock parsing error" in result["message"]

    @patch("local_newsifier.services.rss_feed_service.parse_rss_feed")
    def test_process_feed_article_error(
        self, 
        mock_parse_rss_feed, 
        rss_feed_service_instance,
        mock_rss_feed_crud,
        mock_feed_processing_log_crud,
        mock_article_service,
        mock_session_factory,
        sample_feed,
        sample_processing_log,
        sample_feed_data
    ):
        """Test process_feed with article processing error."""
        _, mock_session = mock_session_factory
        feed_id = 1
        
        # Set up the mocks
        mock_rss_feed_crud.get.return_value = sample_feed
        mock_feed_processing_log_crud.create_processing_started.return_value = sample_processing_log
        mock_parse_rss_feed.return_value = sample_feed_data
        
        # Make article service raise an exception on the first call
        mock_article_service.create_article_from_rss_entry.side_effect = [
            Exception("Mock article error"),  # First call fails
            123  # Second call succeeds
        ]
        
        # Mock the logger to capture errors
        with patch("local_newsifier.services.rss_feed_service.logger.error") as mock_logger_error:
            # Call the method
            result = rss_feed_service_instance.process_feed(feed_id)
            
            # Verify that the article error was logged
            mock_logger_error.assert_called_once()
            error_message = mock_logger_error.call_args[0][0]
            assert "Error processing article" in error_message
            assert "Mock article error" in error_message
        
        # Verify the result - should still be success overall
        assert result["status"] == "success"
        assert result["feed_id"] == feed_id
        assert result["articles_found"] == 2
        assert result["articles_added"] == 1  # Only one succeeded

    def test_get_feed_processing_logs(
        self, 
        rss_feed_service_instance,
        mock_feed_processing_log_crud,
        mock_session_factory,
        sample_processing_log
    ):
        """Test get_feed_processing_logs."""
        _, mock_session = mock_session_factory
        feed_id = 1
        
        # Set up the mock
        mock_feed_processing_log_crud.get_by_feed_id.return_value = [sample_processing_log]
        
        # Call the method
        result = rss_feed_service_instance.get_feed_processing_logs(feed_id)
        
        # Verify that the CRUD method was called
        mock_feed_processing_log_crud.get_by_feed_id.assert_called_once_with(
            mock_session, feed_id=feed_id, skip=0, limit=100
        )
        
        # Verify the result
        assert len(result) == 1
        assert result[0]["id"] == sample_processing_log.id
        assert result[0]["feed_id"] == sample_processing_log.feed_id
        assert result[0]["status"] == sample_processing_log.status
        assert result[0]["articles_found"] == sample_processing_log.articles_found
        assert result[0]["articles_added"] == sample_processing_log.articles_added
        assert result[0]["error_message"] == sample_processing_log.error_message
        assert result[0]["started_at"] == sample_processing_log.started_at.isoformat()
        assert result[0]["completed_at"] == sample_processing_log.completed_at.isoformat()

    def test_get_feed_processing_logs_with_pagination(
        self, 
        rss_feed_service_instance,
        mock_feed_processing_log_crud,
        mock_session_factory,
        sample_processing_log
    ):
        """Test get_feed_processing_logs with pagination."""
        _, mock_session = mock_session_factory
        feed_id = 1
        skip = 10
        limit = 20
        
        # Set up the mock
        mock_feed_processing_log_crud.get_by_feed_id.return_value = [sample_processing_log]
        
        # Call the method
        result = rss_feed_service_instance.get_feed_processing_logs(feed_id, skip=skip, limit=limit)
        
        # Verify that the CRUD method was called with the correct pagination parameters
        mock_feed_processing_log_crud.get_by_feed_id.assert_called_once_with(
            mock_session, feed_id=feed_id, skip=skip, limit=limit
        )
        
        # Verify the result
        assert len(result) == 1
        assert result[0]["id"] == sample_processing_log.id


def test_register_process_article_task():
    """Test register_process_article_task."""
    # Save the original value
    original_task = _process_article_task
    
    try:
        # Reset the global variable
        global _process_article_task
        _process_article_task = None
        
        # Create a mock task function
        mock_task = MagicMock()
        
        # Register the task
        register_process_article_task(mock_task)
        
        # Verify that the global variable was updated
        assert _process_article_task == mock_task
    finally:
        # Restore the original value
        _process_article_task = original_task


def test_register_article_service():
    """Test register_article_service."""
    # Save the original service
    original_service = rss_feed_service.article_service
    
    try:
        # Reset the service attribute
        rss_feed_service.article_service = None
        
        # Create a mock article service
        mock_article_service = MagicMock()
        
        # Register the article service
        register_article_service(mock_article_service)
        
        # Verify that the service attribute was updated
        assert rss_feed_service.article_service == mock_article_service
    finally:
        # Restore the original service
        rss_feed_service.article_service = original_service

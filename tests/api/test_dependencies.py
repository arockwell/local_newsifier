"""Tests for API dependencies."""

from unittest.mock import MagicMock, Mock, patch

import pytest
from fastapi import HTTPException, Request
from sqlmodel import Session

from local_newsifier.api.dependencies import (get_article_service, get_rss_feed_service,
                                              get_session, get_templates, require_admin)


class TestSessionDependency:
    """Tests for the database session dependency."""

    def test_get_session_from_database_engine(self):
        """Test that get_session creates a session from the engine."""
        # Create a mock engine
        from unittest.mock import MagicMock

        mock_engine = MagicMock()
        mock_session = Mock(spec=Session)

        # Mock the Session class to return our mock session
        with patch("local_newsifier.database.engine.get_engine") as mock_get_engine, patch(
            "local_newsifier.api.dependencies.Session"
        ) as MockSession:
            # Set up the engine mock
            mock_get_engine.return_value = mock_engine
            MockSession.return_value = mock_session

            # Get the session from the generator
            session_generator = get_session()
            session = next(session_generator)

            # Verify the session is what we expect
            assert session is mock_session
            assert mock_get_engine.called
            MockSession.assert_called_once_with(mock_engine)

            # Test cleanup
            try:
                next(session_generator)
            except StopIteration:
                pass

            # Verify cleanup methods were called
            mock_session.commit.assert_called_once()
            mock_session.close.assert_called_once()


class TestServiceDependencies:
    """Tests for service dependencies."""

    def test_get_article_service(self):
        """Test that get_article_service returns an ArticleService instance."""
        # Create mock objects
        mock_session = Mock(spec=Session)
        mock_article_crud = Mock()
        mock_analysis_result_crud = Mock()
        mock_entity_service = Mock()

        # Call the function with mocked dependencies
        result = get_article_service(
            session=mock_session,
            article_crud=mock_article_crud,
            analysis_result_crud=mock_analysis_result_crud,
            entity_service=mock_entity_service,
        )

        # Verify the result
        assert result is not None
        assert hasattr(result, "article_crud")
        assert hasattr(result, "analysis_result_crud")
        assert hasattr(result, "entity_service")
        assert result.article_crud is mock_article_crud
        assert result.analysis_result_crud is mock_analysis_result_crud
        assert result.entity_service is mock_entity_service

    def test_get_rss_feed_service(self):
        """Test that get_rss_feed_service returns an RSSFeedService instance."""
        # Create mock objects
        mock_session = Mock(spec=Session)
        mock_rss_feed_crud = Mock()
        mock_feed_processing_log_crud = Mock()
        mock_article_service = Mock()

        # Call the function with mocked dependencies
        result = get_rss_feed_service(
            session=mock_session,
            rss_feed_crud=mock_rss_feed_crud,
            feed_processing_log_crud=mock_feed_processing_log_crud,
            article_service=mock_article_service,
        )

        # Verify the result
        assert result is not None
        assert hasattr(result, "rss_feed_crud")
        assert hasattr(result, "feed_processing_log_crud")
        assert hasattr(result, "article_service")
        assert result.rss_feed_crud is mock_rss_feed_crud
        assert result.feed_processing_log_crud is mock_feed_processing_log_crud
        assert result.article_service is mock_article_service


class TestTemplatesDependency:
    """Tests for the templates dependency."""

    def test_get_templates(self):
        """Test get_templates returns templates instance."""
        # Import the actual templates instance
        from local_newsifier.api.dependencies import templates

        # Call the function
        result = get_templates()

        # Verify it returns the templates instance
        assert result is templates


class TestRequireAdminDependency:
    """Tests for the require_admin dependency."""

    def test_require_admin_authenticated(self):
        """Test require_admin when authenticated."""
        # Create a mock request with authenticated session
        mock_request = MagicMock(spec=Request)
        mock_request.session = {"authenticated": True}

        # Call the dependency
        result = require_admin(mock_request)

        # Verify result
        assert result is True

    def test_require_admin_not_authenticated(self):
        """Test require_admin when not authenticated."""
        # Create a mock request with unauthenticated session
        mock_request = MagicMock(spec=Request)
        mock_request.session = {}
        mock_request.url.path = "/protected/path"

        # Call the dependency and expect exception
        with pytest.raises(HTTPException) as excinfo:
            require_admin(mock_request)

        # Verify exception details
        assert excinfo.value.status_code == 302
        assert excinfo.value.headers["Location"] == "/login?next=/protected/path"

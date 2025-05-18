"""Tests for API dependencies."""

import os
import importlib
import pytest
from unittest.mock import Mock, patch, MagicMock, PropertyMock
from fastapi import HTTPException, Request
from fastapi.templating import Jinja2Templates
from sqlmodel import Session

from local_newsifier.services.article_service import ArticleService
from local_newsifier.services.rss_feed_service import RSSFeedService

from tests.fixtures.event_loop import event_loop_fixture, injectable_service_fixture

from local_newsifier.api.dependencies import get_session, get_article_service, get_rss_feed_service, get_templates, require_admin


class TestSessionDependency:
    """Tests for the database session dependency."""

    def test_get_session_from_injectable(self):
        """Test that get_session uses the injectable provider."""
        # Create a mock session
        mock_session = Mock(spec=Session)
        
        # Mock the injectable provider
        with patch("local_newsifier.di.providers.get_session") as mock_get_session:
            # Set up the session provider to yield our mock session
            mock_get_session.return_value = iter([mock_session])
            
            # Get the session from the generator
            session_generator = get_session()
            session = next(session_generator)
            
            # Verify the session is what we expect
            assert session is mock_session
            assert mock_get_session.called


class TestServiceDependencies:
    """Tests for service dependencies."""
    
    def test_get_article_service(self, event_loop_fixture):
        """Test that get_article_service returns the service from the injectable provider."""
        # Create mock objects
        mock_session = Mock(spec=Session)
        mock_session_context = MagicMock()
        mock_session_context.__enter__.return_value = mock_session
        mock_service = Mock(spec=ArticleService)
        
        # Set up mocks with appropriate patches
        with patch("local_newsifier.database.engine.get_session") as mock_get_session, \
             patch("local_newsifier.di.providers.get_article_service") as mock_get_injectable_service:
             
            # Configure the mocks
            mock_get_session.return_value = iter([mock_session_context])
            mock_get_injectable_service.return_value = mock_service
            
            # Call the function under test
            result = get_article_service()
            
            # Verify the result
            assert result is mock_service
            assert mock_get_injectable_service.called
            mock_get_injectable_service.assert_called_with(session=mock_session)
    
    def test_get_rss_feed_service(self, event_loop_fixture):
        """Test that get_rss_feed_service returns the service from the injectable provider."""
        # Create mock objects
        mock_session = Mock(spec=Session)
        mock_session_context = MagicMock()
        mock_session_context.__enter__.return_value = mock_session
        mock_service = Mock(spec=RSSFeedService)
        
        # Set up mocks with appropriate patches
        with patch("local_newsifier.database.engine.get_session") as mock_get_session, \
             patch("local_newsifier.di.providers.get_rss_feed_service") as mock_get_injectable_service:
             
            # Configure the mocks
            mock_get_session.return_value = iter([mock_session_context])
            mock_get_injectable_service.return_value = mock_service
            
            # Call the function under test
            result = get_rss_feed_service()
            
            # Verify the result
            assert result is mock_service
            assert mock_get_injectable_service.called
            mock_get_injectable_service.assert_called_with(session=mock_session)


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
"""Tests for API dependencies."""

import os
import importlib
import pytest
from unittest.mock import Mock, patch, MagicMock, PropertyMock
from fastapi import HTTPException, Request
from fastapi.templating import Jinja2Templates
from sqlmodel import Session

from local_newsifier.api.dependencies import get_session, get_article_service, get_rss_feed_service, get_templates, require_admin


class TestSessionDependency:
    """Tests for the database session dependency."""

    @pytest.mark.skip(reason="Now using injectable provider directly")
    def test_get_session_from_injectable(self):
        """Test that get_session uses the injectable provider."""
        # Create a mock session
        mock_session = Mock(spec=Session)
        
        # Mock the injectable provider
        with patch("local_newsifier.api.dependencies.get_injectable_session") as mock_get_session:
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
    
    @pytest.mark.skip(reason="Async event loop issue in fastapi-injectable, to be fixed in a separate PR")
    def test_get_article_service(self):
        """Test that get_article_service returns the service from the injectable provider."""
        # Create mock objects
        mock_service = Mock()
        mock_session = Mock(spec=Session)
        mock_manager = MagicMock()
        mock_manager.__enter__.return_value = mock_session
        
        # Mock the session factory
        with patch("local_newsifier.api.dependencies.get_session") as mock_get_session:
            # Set up the session factory to yield our mock session
            mock_get_session.return_value = iter([mock_session])
            
            # Mock the injectable service provider
            with patch("local_newsifier.api.dependencies.get_injectable_article_service") as mock_get_service:
                # Set up the service provider to return our mock service
                mock_get_service.return_value = mock_service
                
                # Get the service
                service = get_article_service()
                
                # Verify the service is what we expect
                assert service is mock_service
                assert mock_get_service.called
                assert mock_get_service.call_args[1]["session"] is mock_session
    
    @pytest.mark.skip(reason="Async event loop issue in fastapi-injectable, to be fixed in a separate PR")
    def test_get_rss_feed_service(self):
        """Test that get_rss_feed_service returns the service from the injectable provider."""
        # Create mock objects
        mock_service = Mock()
        mock_session = Mock(spec=Session)
        mock_manager = MagicMock()
        mock_manager.__enter__.return_value = mock_session
        
        # Mock the session factory
        with patch("local_newsifier.api.dependencies.get_session") as mock_get_session:
            # Set up the session factory to yield our mock session
            mock_get_session.return_value = iter([mock_session])
            
            # Mock the injectable service provider
            with patch("local_newsifier.api.dependencies.get_injectable_rss_feed_service") as mock_get_service:
                # Set up the service provider to return our mock service
                mock_get_service.return_value = mock_service
                
                # Get the service
                service = get_rss_feed_service()
                
                # Verify the service is what we expect
                assert service is mock_service
                assert mock_get_service.called
                assert mock_get_service.call_args[1]["session"] is mock_session


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
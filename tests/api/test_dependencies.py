"""Tests for API dependencies."""

import os
import importlib
import pytest
from unittest.mock import Mock, patch, MagicMock, PropertyMock
from fastapi import HTTPException, Request
from fastapi.templating import Jinja2Templates
from sqlmodel import Session

from local_newsifier.container import container
from local_newsifier.api.dependencies import get_session, get_article_service, get_rss_feed_service, get_templates, require_admin


class TestSessionDependency:
    """Tests for the database session dependency."""

    def test_get_session_yield(self):
        """Test that get_session yields a database session."""
        # Create a mock session factory and session
        mock_session = Mock(spec=Session)
        mock_manager = MagicMock()  # Use MagicMock for magic methods
        mock_manager.__enter__.return_value = mock_session
        
        # Create a mock for container
        with patch("local_newsifier.api.dependencies.container") as mock_container:
            # Set up the mock container to return None for session_factory
            # This will cause the fallback to SessionManager
            mock_container.get.return_value = None
            
            # Then mock SessionManager
            with patch("local_newsifier.api.dependencies.SessionManager", autospec=True) as MockSessionManager:
                # Set up the SessionManager mock
                MockSessionManager.return_value = mock_manager
                
                # Get the session from the generator
                session_generator = get_session()
                session = next(session_generator)
                
                # Verify the session is what we expect
                assert session is mock_session
                assert mock_container.get.called
                assert mock_container.get.call_args[0][0] == "session_factory"
                assert MockSessionManager.called

    def test_get_session_from_container(self):
        """Test that get_session uses the session factory from the container when available."""
        # Create a mock session factory and session
        mock_session = Mock(spec=Session)
        mock_session_factory = Mock()
        mock_manager = MagicMock()  # Use MagicMock for magic methods
        mock_manager.__enter__.return_value = mock_session
        mock_session_factory.return_value = mock_manager
        
        # Create a mock for container
        with patch("local_newsifier.api.dependencies.container") as mock_container:
            # Set up the mock container to return our session factory
            mock_container.get.return_value = mock_session_factory
            
            # Get the session from the generator
            session_generator = get_session()
            session = next(session_generator)
            
            # Verify the session is what we expect
            assert session is mock_session
            assert mock_container.get.called
            assert mock_container.get.call_args[0][0] == "session_factory"
            assert mock_session_factory.called

    def test_get_session_context_manager(self):
        """Test that the session context manager is used correctly."""
        # Use MagicMock instead which doesn't have the attribute restrictions
        with patch("local_newsifier.api.dependencies.container") as mock_container:
            # Set up container to return None
            mock_container.get.return_value = None
            
            with patch("local_newsifier.api.dependencies.SessionManager") as MockSessionManager:
                # Create a mock session and context manager
                mock_session = MagicMock(spec=Session)
                mock_manager = MagicMock()
                mock_manager.__enter__.return_value = mock_session
                MockSessionManager.return_value = mock_manager
                
                # Use the generator
                session_generator = get_session()
                _ = next(session_generator)
                
                # Try to exhaust the generator to trigger the cleanup
                try:
                    next(session_generator)
                except StopIteration:
                    pass
                
                # Verify context manager was used correctly
                assert mock_manager.__enter__.called
                # Note: In a real context manager, __exit__ would be called, but with our mocking
                # approach and the yield dependency pattern of FastAPI, __exit__ won't be called
                # in the test because FastAPI manages this lifecycle


class TestServiceDependencies:
    """Tests for service dependencies."""
    
    def test_get_article_service(self):
        """Test that get_article_service returns the service from the container."""
        # This test is primarily checking the legacy container path
        # For the new injectable path, we add more comprehensive tests separately
        
        mock_service = Mock()
        
        # Patch the importlib.import_module call to raise ImportError
        with patch.object(importlib, 'import_module', side_effect=ImportError):
            # Patch the container.get call to return our mock service
            with patch.object(container, 'get', return_value=mock_service):
                # Call the function under test
                result = get_article_service()
                
                # Verify we got the service from the container
                assert result is mock_service
                assert container.get.call_count > 0
                assert "article_service" in [call[0][0] for call in container.get.call_args_list]
    
    def test_get_rss_feed_service(self):
        """Test that get_rss_feed_service returns the service from the container."""
        mock_service = Mock()
        
        with patch("local_newsifier.api.dependencies.container") as mock_container:
            # Set up the mock container to return our mock service
            mock_container.get.return_value = mock_service
            
            # Get the service
            service = get_rss_feed_service()
            
            # Verify the service is what we expect
            assert service is mock_service
            assert mock_container.get.called
            assert mock_container.get.call_args[0][0] == "rss_feed_service"


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

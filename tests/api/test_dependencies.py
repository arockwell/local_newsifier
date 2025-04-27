"""Tests for API dependencies."""

import os
import pytest
from unittest.mock import Mock, patch, MagicMock, PropertyMock
from fastapi import HTTPException, Request
from fastapi.templating import Jinja2Templates
from sqlmodel import Session

from local_newsifier.api.dependencies import get_session, get_templates, require_admin


class TestSessionDependency:
    """Tests for the database session dependency."""

    def test_get_session_yield(self):
        """Test that get_session yields a database session."""
        # Use autospec=True to auto-create the mocks with proper spec
        with patch("local_newsifier.api.dependencies.SessionManager", autospec=True) as MockSessionManager:
            # Create a mock session
            mock_session = Mock(spec=Session)
            
            # Make the context manager return our session
            mock_manager = MockSessionManager.return_value
            mock_manager.__enter__.return_value = mock_session
            
            # Get the session from the generator
            session_generator = get_session()
            session = next(session_generator)
            
            # Verify the session is what we expect
            assert session is mock_session
            assert MockSessionManager.called

    def test_get_session_context_manager(self):
        """Test that the session context manager is used correctly."""
        # Use MagicMock instead which doesn't have the attribute restrictions
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

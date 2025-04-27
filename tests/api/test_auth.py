"""Tests for the authentication router."""

import os
from unittest.mock import MagicMock, Mock, patch

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from starlette.middleware.sessions import SessionMiddleware

from local_newsifier.api.dependencies import require_admin
from local_newsifier.api.routers.auth import router
from local_newsifier.config.settings import settings


@pytest.fixture
def app():
    """Create a FastAPI app with session middleware for testing."""
    app = FastAPI()
    app.add_middleware(SessionMiddleware, secret_key="test_secret_key")
    app.include_router(router)
    return app


@pytest.fixture
def client(app):
    """Create a test client for the FastAPI application."""
    return TestClient(app)


@pytest.fixture
def mock_templates():
    """Mock templates for testing."""
    mock = MagicMock()
    mock.TemplateResponse.return_value = "mocked template response"
    return mock


class TestLoginPage:
    """Tests for the login page endpoint."""

    @patch("local_newsifier.api.routers.auth.templates")
    def test_login_page(self, mock_templates, client):
        """Test the login page returns HTML content."""
        # Set up the mock to return a proper response
        mock_response = "Mock HTML Response"
        mock_templates.TemplateResponse.return_value = mock_response
        
        # Override the route handler to use our mock
        with patch("local_newsifier.api.routers.auth.router") as mock_router:
            # Create a mock endpoint function that uses our mocked templates
            async def mock_login_page(request):
                return mock_templates.TemplateResponse(
                    "login.html", 
                    {"request": request, "title": "Admin Login", "next_url": "/system/tables"}
                )
            
            # Attach our mock function to the router
            mock_router.routes = []
            mock_router.get.return_value = mock_login_page
            
            # Now test the login_page function directly
            from local_newsifier.api.routers.auth import login_page
            
            # Create a mock request
            mock_request = Mock()
            mock_request.query_params.get.return_value = "/system/tables"
            
            # Call the function directly
            result = login_page(mock_request)
            
            # Verify template was rendered with correct context
            mock_templates.TemplateResponse.assert_called_with(
                "login.html", 
                {"request": mock_request, "title": "Admin Login", "next_url": "/system/tables"}
            )

    @patch("local_newsifier.api.routers.auth.templates")
    def test_login_page_with_next_param(self, mock_templates, client):
        """Test the login page with a custom next parameter."""
        # Set up the mock to return a proper response
        mock_response = "Mock HTML Response"
        mock_templates.TemplateResponse.return_value = mock_response
        
        # Now test the login_page function directly
        from local_newsifier.api.routers.auth import login_page
        
        # Create a mock request with custom next parameter
        mock_request = Mock()
        mock_request.query_params.get.return_value = "/custom/path"
        
        # Call the function directly
        result = login_page(mock_request)
        
        # Verify template was rendered with correct context
        mock_templates.TemplateResponse.assert_called_with(
            "login.html", 
            {"request": mock_request, "title": "Admin Login", "next_url": "/custom/path"}
        )


class TestLoginSubmission:
    """Tests for the login form submission endpoint."""

    @patch("local_newsifier.api.routers.auth.settings")
    def test_login_success(self, mock_settings, client):
        """Test successful login with valid credentials."""
        # Set up mock settings
        mock_settings.ADMIN_USERNAME = "admin"
        mock_settings.ADMIN_PASSWORD = "password"
        
        # Test the login function directly
        from local_newsifier.api.routers.auth import login
        
        # Create a mock request
        mock_request = Mock()
        mock_request.session = {}
        
        # Call the function directly with valid credentials
        result = login(
            mock_request, 
            username="admin", 
            password="password", 
            next_url="/custom/redirect"
        )
        
        # Verify session was set
        assert mock_request.session["authenticated"] is True
        
        # Verify redirect response
        assert result.status_code == 302
        assert result.headers["location"] == "/custom/redirect"

    @patch("local_newsifier.api.routers.auth.settings")
    @patch("local_newsifier.api.routers.auth.templates")
    def test_login_invalid_credentials(self, mock_templates, mock_settings, client):
        """Test login with invalid credentials."""
        # Set up mock settings
        mock_settings.ADMIN_USERNAME = "admin"
        mock_settings.ADMIN_PASSWORD = "password"
        
        # Set up mock templates
        mock_response = "Mock HTML Response"
        mock_templates.TemplateResponse.return_value = mock_response
        
        # Test the login function directly
        from local_newsifier.api.routers.auth import login
        
        # Create a mock request
        mock_request = Mock()
        mock_request.session = {}
        
        # Call the function directly with invalid credentials
        result = login(
            mock_request, 
            username="admin", 
            password="wrong_password", 
            next_url="/custom/redirect"
        )
        
        # Verify template was rendered with error message
        mock_templates.TemplateResponse.assert_called_with(
            "login.html",
            {
                "request": mock_request,
                "title": "Admin Login",
                "error": "Invalid credentials",
                "next_url": "/custom/redirect",
            }
        )

    @patch("local_newsifier.api.routers.auth.settings")
    def test_login_default_redirect(self, mock_settings, client):
        """Test login with default redirect URL."""
        # Set up mock settings
        mock_settings.ADMIN_USERNAME = "admin"
        mock_settings.ADMIN_PASSWORD = "password"

        # Make the login request without specifying next_url
        response = client.post(
            "/login",
            data={
                "username": "admin",
                "password": "password"
            },
            allow_redirects=False
        )

        # Verify redirect to default URL
        assert response.status_code == 302
        assert response.headers["location"] == "/system/tables"


class TestLogout:
    """Tests for the logout endpoint."""

    def test_logout(self, client):
        """Test logout clears the session and redirects."""
        # Test the logout function directly
        from local_newsifier.api.routers.auth import logout
        
        # Create a mock request with an authenticated session
        mock_request = Mock()
        mock_request.session = {"authenticated": True}
        mock_request.session.clear = Mock()
        
        # Call the logout function
        result = logout(mock_request)
        
        # Verify session was cleared
        mock_request.session.clear.assert_called_once()
        
        # Verify redirect
        assert result.status_code == 302
        assert result.headers["location"] == "/"


class TestRequireAdmin:
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
        with pytest.raises(Exception) as excinfo:
            require_admin(mock_request)
        
        # Verify exception details
        assert excinfo.value.status_code == 302
        assert excinfo.value.headers["Location"] == "/login?next=/protected/path"

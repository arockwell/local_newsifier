"""Tests for the authentication router."""

import os
from unittest.mock import MagicMock, patch

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
        # Make the request
        response = client.get("/login")

        # Verify response
        assert response.status_code == 200

        # Verify template was rendered with correct context
        mock_templates.TemplateResponse.assert_called_once()
        template_name, context = mock_templates.TemplateResponse.call_args[0]
        assert template_name == "login.html"
        assert context["title"] == "Admin Login"
        assert context["next_url"] == "/system/tables"  # Default next URL

    @patch("local_newsifier.api.routers.auth.templates")
    def test_login_page_with_next_param(self, mock_templates, client):
        """Test the login page with a custom next parameter."""
        # Make the request with next parameter
        response = client.get("/login?next=/custom/path")

        # Verify response
        assert response.status_code == 200

        # Verify template was rendered with correct context
        mock_templates.TemplateResponse.assert_called_once()
        template_name, context = mock_templates.TemplateResponse.call_args[0]
        assert template_name == "login.html"
        assert context["next_url"] == "/custom/path"


class TestLoginSubmission:
    """Tests for the login form submission endpoint."""

    @patch("local_newsifier.api.routers.auth.settings")
    def test_login_success(self, mock_settings, client):
        """Test successful login with valid credentials."""
        # Set up mock settings
        mock_settings.ADMIN_USERNAME = "admin"
        mock_settings.ADMIN_PASSWORD = "password"

        # Make the login request
        response = client.post(
            "/login",
            data={
                "username": "admin",
                "password": "password",
                "next_url": "/custom/redirect"
            },
            allow_redirects=False  # Don't follow redirects to check status code
        )

        # Verify redirect response
        assert response.status_code == 302
        assert response.headers["location"] == "/custom/redirect"

        # Verify session was set
        assert "session" in response.cookies
        
        # Make a subsequent request to verify session persistence
        with client.session_transaction() as session:
            assert session["authenticated"] is True

    @patch("local_newsifier.api.routers.auth.settings")
    @patch("local_newsifier.api.routers.auth.templates")
    def test_login_invalid_credentials(self, mock_templates, mock_settings, client):
        """Test login with invalid credentials."""
        # Set up mock settings
        mock_settings.ADMIN_USERNAME = "admin"
        mock_settings.ADMIN_PASSWORD = "password"

        # Make the login request with invalid credentials
        response = client.post(
            "/login",
            data={
                "username": "admin",
                "password": "wrong_password",
                "next_url": "/custom/redirect"
            }
        )

        # Verify response
        assert response.status_code == 200  # Returns login page with error

        # Verify template was rendered with error message
        mock_templates.TemplateResponse.assert_called_once()
        template_name, context = mock_templates.TemplateResponse.call_args[0]
        assert template_name == "login.html"
        assert "error" in context
        assert context["error"] == "Invalid credentials"
        assert context["next_url"] == "/custom/redirect"

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
        # First login to set the session
        with patch("local_newsifier.api.routers.auth.settings") as mock_settings:
            mock_settings.ADMIN_USERNAME = "admin"
            mock_settings.ADMIN_PASSWORD = "password"
            
            client.post(
                "/login",
                data={"username": "admin", "password": "password"}
            )
        
        # Verify session is set
        with client.session_transaction() as session:
            session["authenticated"] = True
            
        # Now logout
        response = client.get("/logout", allow_redirects=False)
        
        # Verify redirect
        assert response.status_code == 302
        assert response.headers["location"] == "/"
        
        # Verify session was cleared
        with client.session_transaction() as session:
            assert "authenticated" not in session


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

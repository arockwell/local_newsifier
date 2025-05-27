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


class TestLoginSubmission:
    """Tests for the login form submission endpoint."""

    @patch("local_newsifier.api.routers.auth.settings")
    def test_login_default_redirect(self, mock_settings, client):
        """Test login with default redirect URL."""
        # Set up mock settings
        mock_settings.ADMIN_USERNAME = "admin"
        mock_settings.ADMIN_PASSWORD = "password"

        # Make the login request without specifying next_url
        response = client.post(
            "/login", data={"username": "admin", "password": "password"}, follow_redirects=False
        )

        # Verify redirect to default URL
        assert response.status_code == 302
        assert response.headers["location"] == "/system/tables"


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


class TestLoginPage:
    """Tests for the login page rendering."""

    def test_login_page_uses_next_query(self, client):
        """GET /login should render with provided next URL."""
        response = client.get("/login?next=/desired")
        assert response.status_code == 200
        assert "/desired" in response.text


class TestLogout:
    """Tests for the logout endpoint."""

    @patch("local_newsifier.api.routers.auth.settings")
    def test_logout_clears_session_and_redirects(self, mock_settings, client):
        """Logging out clears the session and redirects to home."""
        mock_settings.ADMIN_USERNAME = "admin"
        mock_settings.ADMIN_PASSWORD = "password"

        # Authenticate first to set session cookie
        client.post(
            "/login",
            data={"username": "admin", "password": "password"},
            follow_redirects=False,
        )

        assert client.cookies.get("session")

        # Perform logout
        response = client.get("/logout", follow_redirects=False)

        assert response.status_code == 302
        assert response.headers["location"] == "/"

        # Subsequent request should not be authenticated
        response2 = client.post(
            "/login",
            data={"username": "wrong", "password": "wrong"},
            follow_redirects=False,
        )
        assert response2.status_code == 200

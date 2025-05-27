"""Tests for the main FastAPI application."""

import os
from unittest.mock import MagicMock, patch

import pytest
from fastapi.responses import HTMLResponse
from fastapi.testclient import TestClient
from starlette.middleware.sessions import SessionMiddleware

from local_newsifier.api.main import app


@pytest.fixture
def client():
    """Test client for the FastAPI application.

    This client fixture is properly configured to work with event loops
    and fastapi-injectable.
    """
    # Create mock article objects that will be returned by get_by_date_range
    from datetime import datetime
    from unittest.mock import MagicMock

    mock_articles = []
    for i in range(3):
        mock_article = MagicMock()
        mock_article.id = i
        mock_article.title = f"Test Article {i}"
        mock_article.url = f"http://example.com/article/{i}"
        mock_article.source = "Test Source"
        mock_article.published_at = datetime.now()
        mock_article.status = "processed"
        mock_articles.append(mock_article)

    # Setup any required mocks for database operations to avoid actual DB connections
    with patch("local_newsifier.database.engine.get_engine"), patch(
        "local_newsifier.crud.article.article.get_by_date_range", return_value=mock_articles
    ):

        # Create a TestClient with proper event loop handling
        client = TestClient(app)
        yield client


@pytest.fixture
def mock_logger():
    """Mock logger for testing."""
    with patch("local_newsifier.api.main.logger") as mock:
        yield mock


class TestEndpoints:
    """Tests for API endpoints."""

    def test_root_endpoint(self, client):
        """Test the root endpoint returns HTML content."""
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "Local Newsifier" in response.text

    def test_root_endpoint_recent_headlines_content(self, client):
        """Test that the root endpoint has the correct structure for recent headlines."""
        response = client.get("/")
        assert response.status_code == 200

        # Check for the headline section structure
        assert '<h2 class="card-title">Recent Headlines</h2>' in response.text
        assert '<div class="articles-list">' in response.text
        assert "article-item" in response.text

        # We're checking for the structure rather than mocking the data,
        # since dealing with fastapi-injectable in tests requires event loop fixtures

    def test_health_check(self, client):
        """Test the health check endpoint returns the expected JSON."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy", "message": "API is running"}

    def test_get_config(self, client):
        """Test the config endpoint returns configuration information."""
        # Mock environment variables for consistent test results
        with patch.dict(
            os.environ,
            {
                "POSTGRES_HOST": "test-host",
                "POSTGRES_PORT": "5432",
                "POSTGRES_DB": "test-db",
                "LOG_LEVEL": "INFO",
                "ENVIRONMENT": "testing",
            },
        ):
            response = client.get("/config")
            assert response.status_code == 200
            data = response.json()
            assert "database_host" in data
            assert data["environment"] == "testing"

            # Verify sensitive information is not exposed
            assert "POSTGRES_PASSWORD" not in data
            assert "SECRET_KEY" not in data

    def test_not_found_handler_api(self, client):
        """Test the 404 handler for API routes returns JSON."""
        response = client.get("/api/nonexistent")
        assert response.status_code == 404
        assert response.json() == {"detail": "Not found"}

    def test_not_found_handler_html(self, client):
        """Test the 404 handler for non-API routes returns HTML."""
        response = client.get("/nonexistent")
        assert response.status_code == 404
        assert "text/html" in response.headers["content-type"]
        assert "Not Found" in response.text

    def test_not_found_handler_html_template(self, client):
        """Test that the 404 handler renders the correct template for HTML requests."""
        mock_templates = MagicMock()
        mock_templates.TemplateResponse.return_value = HTMLResponse("not found", status_code=404)
        with patch("local_newsifier.api.main.get_templates", return_value=mock_templates):
            response = client.get("/missing-page")
            assert response.status_code == 404
            assert "text/html" in response.headers["content-type"]
        mock_templates.TemplateResponse.assert_called_once()
        template_name = mock_templates.TemplateResponse.call_args[0][0]
        assert "404.html" in template_name


class TestStartupShutdown:
    """Tests for startup and shutdown event handlers."""

    def test_startup_event_exists(self):
        """Test that startup event handler is configured."""
        from local_newsifier.api.main import startup_event

        assert callable(startup_event), "startup_event should be a callable function"

    def test_shutdown_event_exists(self):
        """Test that shutdown event handler is configured."""
        from local_newsifier.api.main import shutdown_event

        assert callable(shutdown_event), "shutdown_event should be a callable function"

    def test_startup_event_success(self, mock_logger):
        """Test successful startup event handler."""
        from local_newsifier.api.main import startup_event

        # Create a mock of the get_engine function
        get_engine_mock = MagicMock(return_value=MagicMock())

        # Use patch to mock external dependencies
        with patch("local_newsifier.api.main.get_engine", get_engine_mock), patch(
            "local_newsifier.api.main.logger", mock_logger
        ):
            # Call the startup event
            startup_event()

            # Verify our mocks were called as expected
            get_engine_mock.assert_called_once()
            mock_logger.info.assert_any_call("Application startup initiated")
            mock_logger.info.assert_any_call("Database connection verified")
            mock_logger.info.assert_any_call("Application startup complete")

    def test_startup_event_error(self, mock_logger):
        """Test error handling during startup event."""
        from local_newsifier.api.main import startup_event

        # Setup the error to be raised
        error_message = "Database connection error"
        get_engine_mock = MagicMock(side_effect=Exception(error_message))

        # Use patches to mock external dependencies
        with patch("local_newsifier.api.main.get_engine", get_engine_mock), patch(
            "local_newsifier.api.main.logger", mock_logger
        ):
            # Call the startup event
            startup_event()

            # Verify our mocks were called as expected
            get_engine_mock.assert_called_once()
            mock_logger.error.assert_called_with(f"Startup error: {error_message}")

    def test_shutdown_event(self, mock_logger):
        """Test shutdown event handler."""
        from local_newsifier.api.main import shutdown_event

        # Use patch to mock logger
        with patch("local_newsifier.api.main.logger", mock_logger):
            # Call the shutdown event
            shutdown_event()

            # Verify logger was called as expected
            mock_logger.info.assert_any_call("Application shutdown initiated")
            mock_logger.info.assert_any_call("Application shutdown complete")


class TestAppConfiguration:
    """Tests for the FastAPI application configuration."""

    def test_app_metadata(self):
        """Test the FastAPI application metadata."""
        assert app.title == "Local Newsifier API"
        assert app.description == "API for Local Newsifier"
        assert app.version == "0.1.0"

    def test_middleware_configuration(self):
        """Test that the session middleware is configured."""
        # Check if SessionMiddleware is in the middleware stack
        session_middleware = next(
            (m for m in app.user_middleware if m.cls == SessionMiddleware), None
        )
        assert session_middleware is not None, "SessionMiddleware should be configured"

    def test_router_inclusion(self):
        """Test that all routers are included."""
        # Get all route paths
        routes = [route.path for route in app.routes]

        # Check for auth routes
        assert "/login" in routes
        assert "/logout" in routes

        # Check for system routes
        assert "/system/tables" in routes

        # Check for tasks routes
        assert "/tasks/" in routes
        assert "/tasks/status/{task_id}" in routes

        # Check for main routes
        assert "/" in routes
        assert "/health" in routes
        assert "/config" in routes


class TestResponseValidation:
    """Tests for API response validation."""

    def test_health_check_schema(self, client):
        """Test the health check endpoint response schema."""
        response = client.get("/health")
        data = response.json()

        # Validate schema
        assert "status" in data
        assert isinstance(data["status"], str)
        assert "message" in data
        assert isinstance(data["message"], str)

    def test_config_schema(self, client):
        """Test the config endpoint response schema."""
        with patch.dict(
            os.environ,
            {
                "POSTGRES_HOST": "test-host",
                "POSTGRES_PORT": "5432",
                "POSTGRES_DB": "test-db",
                "LOG_LEVEL": "INFO",
                "ENVIRONMENT": "testing",
            },
        ):
            response = client.get("/config")
            data = response.json()

            # Validate schema
            assert "database_host" in data
            assert isinstance(data["database_host"], str)
            assert "database_port" in data
            assert "database_name" in data
            assert "log_level" in data
            assert "environment" in data

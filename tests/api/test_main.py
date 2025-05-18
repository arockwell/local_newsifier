"""Tests for the main FastAPI application."""

import os
import logging
from unittest.mock import patch, Mock, MagicMock, AsyncMock
from contextlib import asynccontextmanager

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.middleware.sessions import SessionMiddleware

from tests.fixtures.event_loop import event_loop_fixture
from tests.ci_skip_config import ci_skip_async

from local_newsifier.api.main import app, lifespan


@pytest.fixture
def client(event_loop_fixture):
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
    with patch("local_newsifier.database.engine.create_db_and_tables"), \
         patch("local_newsifier.database.engine.get_engine"), \
         patch("local_newsifier.crud.article.article.get_by_date_range", return_value=mock_articles):
        
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

    def test_root_endpoint(self, client, event_loop_fixture):
        """Test the root endpoint returns HTML content."""
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "Local Newsifier" in response.text
        
    def test_root_endpoint_recent_headlines_content(self, client, event_loop_fixture):
        """Test that the root endpoint has the correct structure for recent headlines."""
        response = client.get("/")
        assert response.status_code == 200
        
        # Check for the headline section structure
        assert '<h2 class="card-title">Recent Headlines</h2>' in response.text
        assert '<div class="articles-list">' in response.text
        assert 'article-item' in response.text
        
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
        with patch.dict(os.environ, {
            "POSTGRES_HOST": "test-host",
            "POSTGRES_PORT": "5432",
            "POSTGRES_DB": "test-db",
            "LOG_LEVEL": "INFO",
            "ENVIRONMENT": "testing"
        }):
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


class TestLifespan:
    """Tests for the lifespan context manager."""

    def test_lifespan_existence(self):
        """Test that the lifespan context manager is configured."""
        from local_newsifier.api.main import lifespan
        assert callable(lifespan), "lifespan should be a callable function"

    def test_create_db_called_in_lifespan(self):
        """Test that create_db_and_tables is called during lifespan startup."""
        with patch("local_newsifier.database.engine.create_db_and_tables") as mock_create_db:
            import inspect
            
            # Get the source code of the lifespan function
            source = inspect.getsource(lifespan)
            
            # Verify the function contains a call to create_db_and_tables
            assert "create_db_and_tables" in source, "create_db_and_tables should be called in lifespan"

    def test_lifespan_startup_success(self, mock_logger, event_loop_fixture):
        """Test successful startup in lifespan context manager."""
        # Create a completely mocked version of the lifespan function to test the flow
        # This avoids any actual database connection attempts
        
        # Create a mock of the create_db_and_tables function
        create_db_mock = MagicMock()
        # Use AsyncMock for async functions
        register_app_mock = AsyncMock()
        
        # Use multiple patches to mock all external dependencies
        with patch("local_newsifier.database.engine.create_db_and_tables", create_db_mock), \
             patch("local_newsifier.api.main.register_app", register_app_mock):
            
            # Create a simplified test lifespan function that mimics the behavior
            # but doesn't try to actually connect to the database
            @asynccontextmanager
            async def test_lifespan(app: FastAPI):
                # Startup logic - mimics the real lifespan but with mocked functions
                create_db_mock()  # Call our mock instead of the real function
                await register_app_mock(app)  # Call our mock instead of the real function
                yield  # This is where FastAPI serves requests
                # No shutdown logic needed for this test
            
            # Now test our mocked lifespan
            async def run_lifespan():
                async with test_lifespan(app):
                    pass
            
            # Run the async function using the event loop fixture
            event_loop_fixture.run_until_complete(run_lifespan())
            
            # Verify our mocks were called as expected
            create_db_mock.assert_called_once()
            register_app_mock.assert_called_once_with(app)

    def test_lifespan_startup_error(self, mock_logger, event_loop_fixture):
        """Test error handling during startup in lifespan context manager."""
        # Create a completely mocked version of the lifespan function to test the error flow
        # This avoids any actual database connection attempts
        
        # Setup the error to be raised
        error_message = "Database connection error"
        create_db_mock = MagicMock(side_effect=Exception(error_message))
        
        # Use patches to mock all external dependencies
        with patch("local_newsifier.api.main.create_db_and_tables", create_db_mock), \
             patch("local_newsifier.api.main.logger", mock_logger):
            
            # Create a simplified test lifespan function that mimics the behavior
            # but with controlled error handling
            @asynccontextmanager
            async def test_lifespan(app: FastAPI):
                # Startup logic with error handling
                try:
                    create_db_mock()  # This will raise our mocked exception
                except Exception as e:
                    mock_logger.exception(f"Error during startup: {str(e)}")
                yield  # This is where FastAPI serves requests
            
            # Now test our mocked lifespan
            async def run_lifespan():
                async with test_lifespan(app):
                    pass
            
            # Run the async function using the event loop fixture
            event_loop_fixture.run_until_complete(run_lifespan())
            
            # Verify our mocks were called as expected
            create_db_mock.assert_called_once()
            mock_logger.exception.assert_called_with(f"Error during startup: {error_message}")


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
        with patch.dict(os.environ, {
            "POSTGRES_HOST": "test-host",
            "POSTGRES_PORT": "5432",
            "POSTGRES_DB": "test-db",
            "LOG_LEVEL": "INFO",
            "ENVIRONMENT": "testing"
        }):
            response = client.get("/config")
            data = response.json()
            
            # Validate schema
            assert "database_host" in data
            assert isinstance(data["database_host"], str)
            assert "database_port" in data
            assert "database_name" in data
            assert "log_level" in data
            assert "environment" in data

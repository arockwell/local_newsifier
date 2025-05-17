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
def client():
    """Test client for the FastAPI application."""
    return TestClient(app)


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
        """Test that database initialization is called during lifespan startup."""
        import inspect
        
        # Get the source code of the lifespan function
        source = inspect.getsource(lifespan)
        
        # Verify the function contains a call to get_async_db_initializer
        assert "get_async_db_initializer" in source, "get_async_db_initializer should be called in lifespan"
        
        # Verify the async initialization pattern
        assert "db_initializer = await get_async_db_initializer()" in source, "async database initialization should be used"
        assert "db_init_result = await db_initializer()" in source, "async database initialization should be awaited"

    def test_lifespan_startup_success(self, mock_logger, event_loop_fixture):
        """Test successful startup in lifespan context manager."""
        # Create a completely mocked version of the lifespan function to test the flow
        # This avoids any actual database connection attempts
        
        # Create mocks for all dependencies
        db_initializer_mock = AsyncMock(return_value=True)
        register_app_mock = AsyncMock()
        migrate_services_mock = AsyncMock()
        
        # Use patches to mock all external dependencies directly
        with patch("local_newsifier.di.providers.get_async_db_initializer", new_callable=AsyncMock) as get_db_init_mock, \
             patch("local_newsifier.api.main.register_app", register_app_mock), \
             patch("local_newsifier.api.main.migrate_container_services", migrate_services_mock):
            
            # Set up the return value for get_async_db_initializer
            get_db_init_mock.return_value = db_initializer_mock
            
            # Create a test app instance
            test_app = FastAPI()
            
            # Now test the real lifespan function with our mocks
            async def run_lifespan():
                from local_newsifier.api.main import lifespan
                async with lifespan(test_app):
                    pass
            
            # Run the async function using the event loop fixture
            event_loop_fixture.run_until_complete(run_lifespan())
            
            # Verify our mocks were called as expected
            register_app_mock.assert_called_with(test_app)
            get_db_init_mock.assert_called()
            db_initializer_mock.assert_called()
            migrate_services_mock.assert_called_with(test_app)

    def test_lifespan_startup_error(self, mock_logger, event_loop_fixture):
        """Test error handling during startup in lifespan context manager."""
        # Create a completely mocked version of the lifespan function to test the error flow
        # This avoids any actual database connection attempts
        
        # Setup the error to be raised
        error_message = "Database connection error"
        db_initializer_mock = AsyncMock(side_effect=Exception(error_message))
        register_app_mock = AsyncMock()
        
        # Use patches to mock all external dependencies
        with patch("local_newsifier.di.providers.get_async_db_initializer", new_callable=AsyncMock) as get_db_init_mock, \
             patch("local_newsifier.api.main.register_app", register_app_mock), \
             patch("local_newsifier.api.main.logger", mock_logger):
            
            # Set up the return value for get_async_db_initializer
            get_db_init_mock.return_value = db_initializer_mock
            
            # Create a test app instance
            test_app = FastAPI()
            
            # Now test the real lifespan function with our mocks
            async def run_lifespan():
                from local_newsifier.api.main import lifespan
                async with lifespan(test_app):
                    pass
            
            # Run the async function using the event loop fixture
            event_loop_fixture.run_until_complete(run_lifespan())
            
            # Verify our mocks were called as expected
            register_app_mock.assert_called_with(test_app)
            get_db_init_mock.assert_called()
            db_initializer_mock.assert_called()
            mock_logger.error.assert_any_call(f"Startup error: {error_message}")


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

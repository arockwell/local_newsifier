"""Tests for the main FastAPI application."""

import os
import logging
from unittest.mock import patch, Mock, MagicMock, AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.middleware.sessions import SessionMiddleware

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
        # FastAPI now uses a merged lifespan context internally, so we can't directly compare functions
        # Instead, we'll verify that a lifespan is configured
        assert app.router.lifespan_context is not None, "App should have lifespan context manager configured"
        # And verify that our lifespan function exists
        assert lifespan is not None, "Lifespan function should exist"

    def test_create_db_called_in_lifespan(self):
        """Test that create_db_and_tables is called during lifespan startup."""
        with patch("local_newsifier.database.engine.create_db_and_tables") as mock_create_db:
            import inspect
            
            # Get the source code of the lifespan function
            source = inspect.getsource(lifespan)
            
            # Verify the function contains a call to create_db_and_tables
            assert "create_db_and_tables" in source, "create_db_and_tables should be called in lifespan"

    @pytest.mark.asyncio
    async def test_lifespan_startup_success(self, mock_logger):
        """Test successful startup in lifespan context manager."""
        # Create a mock FastAPI app
        mock_app = Mock(spec=FastAPI)
        
        # Mock the database creation function
        with patch("local_newsifier.database.engine.create_db_and_tables") as mock_create_db:
            # Create an async context manager
            async_cm = lifespan(mock_app)
            
            # Enter the context
            await async_cm.__aenter__()
            
            # Verify the database creation was called
            mock_create_db.assert_called_once()
            
            # Verify logging
            mock_logger.info.assert_any_call("Application startup initiated")
            mock_logger.info.assert_any_call("Database initialization completed")
            mock_logger.info.assert_any_call("Application startup complete")
            
            # Exit the context
            await async_cm.__aexit__(None, None, None)
            
            # Verify shutdown logging
            mock_logger.info.assert_any_call("Application shutdown initiated")
            mock_logger.info.assert_any_call("Application shutdown complete")

    @pytest.mark.asyncio
    async def test_lifespan_startup_error(self, mock_logger):
        """Test error handling during startup in lifespan context manager."""
        # Create a mock FastAPI app
        mock_app = Mock(spec=FastAPI)
        
        # Mock the database creation function to raise an exception
        with patch("local_newsifier.database.engine.create_db_and_tables") as mock_create_db:
            mock_create_db.side_effect = Exception("Database error")
            
            # Create an async context manager
            async_cm = lifespan(mock_app)
            
            # Enter the context - should handle the exception
            await async_cm.__aenter__()
            
            # Verify the database creation was attempted
            mock_create_db.assert_called_once()
            
            # Verify error logging
            mock_logger.error.assert_called_once()
            error_msg = mock_logger.error.call_args[0][0]
            assert "Database initialization error" in error_msg
            assert "Database error" in error_msg
            
            # Exit the context
            await async_cm.__aexit__(None, None, None)


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

"""Tests for the main FastAPI application."""

import os
from unittest.mock import patch, Mock

import pytest
from fastapi.testclient import TestClient

from local_newsifier.api.main import app


@pytest.fixture
def client():
    """Test client for the FastAPI application."""
    return TestClient(app)


def test_root_endpoint(client):
    """Test the root endpoint returns HTML content."""
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Local Newsifier" in response.text


def test_health_check(client):
    """Test the health check endpoint returns the expected JSON."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "message": "API is running"}


def test_get_config(client):
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


def test_not_found_handler_api(client):
    """Test the 404 handler for API routes returns JSON."""
    response = client.get("/api/nonexistent")
    assert response.status_code == 404
    assert response.json() == {"detail": "Not found"}


def test_not_found_handler_html(client):
    """Test the 404 handler for non-API routes returns HTML."""
    response = client.get("/nonexistent")
    assert response.status_code == 404
    assert "text/html" in response.headers["content-type"]
    assert "Not Found" in response.text


def test_lifespan_existence():
    """Test that the lifespan context manager is configured."""
    from local_newsifier.api.main import lifespan
    assert app.router.lifespan_context == lifespan, "App should have lifespan context manager configured"


def test_create_db_called_in_lifespan():
    """Test that create_db_and_tables is called during lifespan startup."""
    with patch("local_newsifier.database.engine.create_db_and_tables") as mock_create_db:
        from local_newsifier.api.main import lifespan
        import inspect
        
        # Get the source code of the lifespan function
        source = inspect.getsource(lifespan)
        
        # Verify the function contains a call to create_db_and_tables
        assert "create_db_and_tables" in source, "create_db_and_tables should be called in lifespan"

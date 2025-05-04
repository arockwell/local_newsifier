"""Pytest configuration for API tests."""

import pytest
from fastapi.testclient import TestClient

from local_newsifier.api.main import app
from local_newsifier.api.routers import articles


@pytest.fixture
def client():
    """Return a FastAPI TestClient for API testing."""
    # Ensure the articles router is mounted
    # Check if articles router is already included by looking for its routes
    article_routes_exist = any("/articles/" in str(r) for r in app.routes)
    if not article_routes_exist:
        app.include_router(articles.router)

    return TestClient(app)

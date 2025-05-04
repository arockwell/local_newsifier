"""Pytest configuration for API tests."""

import pytest
from fastapi.testclient import TestClient

from local_newsifier.api.main import app
from local_newsifier.api.routers import articles


@pytest.fixture
def client():
    """Return a FastAPI TestClient for API testing."""
    # Ensure the articles router is mounted
    if not any(r.prefix == "/articles" for r in app.routes):
        app.include_router(articles.router)

    return TestClient(app)

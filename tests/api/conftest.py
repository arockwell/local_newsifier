"""Pytest configuration for API tests."""

import pytest
from fastapi.testclient import TestClient

from local_newsifier.api.main import app
from local_newsifier.api.routers import articles


@pytest.fixture
def client():
    """Return a FastAPI TestClient for API testing."""
    # Always include the articles router to ensure it's available
    # This is safer than trying to check if it's already included
    try:
        app.include_router(articles.router)
    except Exception:
        # Router might already be registered, that's fine
        pass

    return TestClient(app)

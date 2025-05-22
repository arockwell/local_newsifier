"""Pytest configuration for API tests."""

import os
import uuid
from typing import Generator
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from local_newsifier.api.main import app


@pytest.fixture
def mock_webhook_handler():
    """Mock the webhook handler for tests."""
    with patch("local_newsifier.services.webhook_service.ApifyWebhookHandler") as mock:
        yield mock


@pytest.fixture
def client():
    """Create a FastAPI test client."""
    with TestClient(app) as test_client:
        yield test_client

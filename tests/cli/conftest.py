"""Pytest fixtures for CLI tests."""

import pytest
from unittest.mock import MagicMock, patch
from sqlmodel import Session


@pytest.fixture
def mock_session():
    """Create a mock database session for testing."""
    mock_session = MagicMock(spec=Session)
    # Setup session as context manager
    mock_session.__enter__ = MagicMock(return_value=mock_session)
    mock_session.__exit__ = MagicMock(return_value=None)
    return mock_session


@pytest.fixture
def mock_rss_feed_service():
    """Create a mock RSSFeedService."""
    return MagicMock()
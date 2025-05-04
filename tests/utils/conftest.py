"""
Common test fixtures for dependency injection testing.

This module provides pytest fixtures that create test doubles for dependency injection.
"""

import pytest
from unittest.mock import MagicMock


@pytest.fixture
def mock_session():
    """Create a mock database session for testing."""
    session = MagicMock()
    
    # Set up session as context manager
    session.__enter__ = MagicMock(return_value=session)
    session.__exit__ = MagicMock(return_value=None)
    
    return session

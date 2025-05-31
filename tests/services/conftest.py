"""
Configuration for services tests.
This file sets up mocks to avoid the SQLite dependency chain.
"""

from unittest.mock import MagicMock, patch

import pytest


# Create a patch context to prevent SQLite-dependent imports when running tests
@pytest.fixture(autouse=True, scope="session")
def mock_flow_imports():
    """Mock the crewai Flow import to avoid SQLite dependency."""
    with patch.dict(
        "sys.modules",
        {
            "crewai": MagicMock(),
            "crewai.Flow": MagicMock(),
            "chromadb": MagicMock(),
        },
    ):
        yield

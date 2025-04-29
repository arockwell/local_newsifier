"""
Configuration for services tests.
This file sets up mocks to avoid the SQLite dependency chain.
"""

import sys
import pytest
from unittest.mock import patch, MagicMock

# Create a patch context to prevent SQLite-dependent imports when running tests
@pytest.fixture(autouse=True, scope="session")
def mock_flow_imports():
    """Mock the crewai Flow import to avoid SQLite dependency."""
    with patch.dict('sys.modules', {
        'crewai': MagicMock(),
        'crewai.Flow': MagicMock(),
        'chromadb': MagicMock(),
    }):
        yield

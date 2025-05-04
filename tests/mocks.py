"""Mock modules for testing purposes."""

import sys
from unittest.mock import MagicMock

# Create a simple mock object without recursive __getattr__
mock_flow = MagicMock()
mock_flow.__name__ = "Flow"

# Create a mock for crewai
mock_crewai = MagicMock()
mock_crewai.Flow = mock_flow

# Add the required mocks to sys.modules
sys.modules["crewai"] = mock_crewai
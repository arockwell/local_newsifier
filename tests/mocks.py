"""Mock modules for testing purposes."""

import sys
from unittest.mock import MagicMock

# Create a proper Flow mock that can be subclassed
class MockFlowBase:
    def __init__(self, *args, **kwargs):
        pass  # Do nothing in init, just provide the method

# Create a mock for crewai
mock_flow = MockFlowBase
mock_crewai = MagicMock()
mock_crewai.Flow = mock_flow

# Add the required mocks to sys.modules
sys.modules["crewai"] = mock_crewai
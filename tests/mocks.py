"""Mock modules for testing purposes."""

import sys
from unittest.mock import MagicMock

# Create a MockModule class that can handle attribute access at any depth
class MockModule(MagicMock):
    """Mock module that returns itself for any attribute access."""
    
    def __getattr__(self, name):
        return MockModule()
    
    def __call__(self, *args, **kwargs):
        return MockModule()

# Add mock modules for all our dependencies
mock_modules = [
    "crewai",
    "spacy",
    "textblob",
    "sqlmodel",
    "fastapi",
    "fastapi_injectable",
    "sqlalchemy",
    "openai",
    "pydantic",
    "celery",
    "tenacity",
    "fastapi.testclient",
]

for module_name in mock_modules:
    parts = module_name.split('.')
    
    # Mock the top-level module first
    if parts[0] not in sys.modules:
        sys.modules[parts[0]] = MockModule()
    
    # Handle submodules
    for i in range(1, len(parts)):
        parent_module = sys.modules['.'.join(parts[:i])]
        child_name = parts[i]
        child_module = MockModule()
        setattr(parent_module, child_name, child_module)
        sys.modules['.'.join(parts[:i+1])] = child_module

# Some special cases that need more specific mocking
mock_flow = MagicMock()
mock_flow.__name__ = "Flow"
sys.modules["crewai"].Flow = mock_flow
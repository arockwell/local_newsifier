"""Base classes and utilities for dependency injection.

This package provides standardized patterns for dependency injection in the Local Newsifier
project, including auto-injectable components, property injection, and test utilities.
"""

from .auto_injectable import (InjectableTool, PropertyInjectable,
                              auto_injectable)
from .test_utils import (create_mock_dependency, setup_injectable_for_test,
                         verify_fallback_behavior)

__all__ = [
    "auto_injectable",
    "PropertyInjectable",
    "InjectableTool",
    "create_mock_dependency",
    "setup_injectable_for_test",
    "verify_fallback_behavior",
]

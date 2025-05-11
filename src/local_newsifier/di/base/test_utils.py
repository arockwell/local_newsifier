"""Test utilities for injectable components.

This module provides utility functions and fixtures for testing
components that use the injectable pattern.
"""

import logging
from typing import Any, Optional, Type
from unittest.mock import MagicMock

import pytest

logger = logging.getLogger(__name__)


def create_mock_dependency(dependency_type: Optional[Type] = None) -> Any:
    """Create a mock dependency for testing.

    Args:
        dependency_type: Optional type of the dependency to mock

    Returns:
        A MagicMock with the optional type specification
    """
    if dependency_type:
        return MagicMock(spec=dependency_type)
    return MagicMock()


def setup_injectable_for_test(cls, **kwargs) -> Any:
    """Set up an injectable component for testing.

    Args:
        cls: The class to instantiate
        **kwargs: Dependencies to inject

    Returns:
        An instance of the class with dependencies injected
    """
    instance = cls()

    for name, dependency in kwargs.items():
        # Set dependency via property if it exists
        if hasattr(instance, name):
            setattr(instance, name, dependency)
        # Otherwise try the set_dependency method
        elif hasattr(instance, "set_dependency"):
            instance.set_dependency(name, dependency)

    return instance


@pytest.fixture
def injectable_instance():
    """Fixture for creating injectable instances with dependencies.

    This fixture is a function that creates an instance of a class
    with dependencies injected for testing.

    Example:
        ```
        def test_my_tool(injectable_instance):
            mock_dependency = MagicMock()
            instance = injectable_instance(
                MyTool,
                dependency_name=mock_dependency
            )
            # Test the instance
        ```
    """

    def _create_instance(cls, **dependencies):
        return setup_injectable_for_test(cls, **dependencies)

    return _create_instance


def verify_fallback_behavior(
    instance, method_name, dependency_name, args=None, kwargs=None
):
    """Verify that a method falls back properly when a dependency is missing.

    Args:
        instance: The instance to test
        method_name: The name of the method to test
        dependency_name: The name of the dependency to remove
        args: Arguments to pass to the method
        kwargs: Keyword arguments to pass to the method

    Returns:
        The result of calling the method with the dependency missing
    """
    args = args or ()
    kwargs = kwargs or {}

    # Store the original dependency
    original_dependency = None

    # Try getting the dependency as an attribute
    if hasattr(instance, dependency_name):
        original_dependency = getattr(instance, dependency_name)
        setattr(instance, dependency_name, None)
    # Otherwise try the dependency dict
    elif hasattr(instance, "_dependencies"):
        original_dependency = instance._dependencies.get(dependency_name)
        instance._dependencies[dependency_name] = None

    try:
        # Call the method without the dependency
        method = getattr(instance, method_name)
        return method(*args, **kwargs)
    finally:
        # Restore the original dependency
        if hasattr(instance, dependency_name):
            setattr(instance, dependency_name, original_dependency)
        elif hasattr(instance, "_dependencies"):
            instance._dependencies[dependency_name] = original_dependency

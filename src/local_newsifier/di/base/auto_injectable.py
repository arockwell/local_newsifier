"""Base class and decorator for auto-injectable components.

This module provides a standardized pattern for making components injectable
with proper handling of property injection, conditional decoration, and
event loop management.
"""

import logging
import os
import sys
from typing import Any, Callable, Type, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


def auto_injectable(use_cache: bool = False) -> Callable[[Type[T]], Type[T]]:
    """Decorator that makes a class auto-injectable with standardized patterns.

    This decorator wraps the class to:
    1. Skip application in test environments to avoid event loop issues
    2. Apply the @injectable decorator in non-test environments
    3. Catch and handle any import or application errors

    Args:
        use_cache: Whether to cache instances (default: False)

    Returns:
        The decorated class or the original class if in a test environment
    """

    def decorator(cls: Type[T]) -> Type[T]:
        # Check if we're in a test environment
        in_test_env = (
            "pytest" in sys.modules
            or os.environ.get("PYTEST_CURRENT_TEST") is not None
            or sys.argv[0].endswith("pytest")
        )

        if in_test_env:
            logger.debug(
                f"Skipping injectable decorator for {cls.__name__} in test environment"
            )
            return cls

        try:
            from fastapi_injectable import injectable

            # Apply the injectable decorator
            decorated_cls = injectable(use_cache=use_cache)(cls)
            logger.debug(f"Applied injectable decorator to {cls.__name__}")
            return decorated_cls
        except (ImportError, Exception) as e:
            logger.debug(f"Failed to apply injectable decorator to {cls.__name__}: {e}")
            return cls

    return decorator


class PropertyInjectable:
    """Base class for components using property injection.

    This class standardizes the pattern for property injection, allowing:
    1. Dependencies to be set after instantiation
    2. Methods to fall back to direct implementation when dependencies aren't set
    3. Multiple dependency injection strategies to work with the same component
    """

    def __init__(self) -> None:
        """Initialize with empty dependency properties."""
        self._dependencies = {}

    def set_dependency(self, name: str, dependency: Any) -> None:
        """Set a dependency by name.

        Args:
            name: The name of the dependency property
            dependency: The dependency instance to inject
        """
        self._dependencies[name] = dependency

    def get_dependency(self, name: str) -> Any:
        """Get a dependency by name.

        Args:
            name: The name of the dependency property

        Returns:
            The dependency instance or None if not set
        """
        return self._dependencies.get(name)

    def has_dependency(self, name: str) -> bool:
        """Check if a dependency is set.

        Args:
            name: The name of the dependency property

        Returns:
            True if the dependency is set, False otherwise
        """
        return name in self._dependencies and self._dependencies[name] is not None


class InjectableTool(PropertyInjectable):
    """Base class for tool components that use property injection.

    This class combines PropertyInjectable with auto_injectable to create
    a standardized pattern for injectable tools.
    """

    def __init__(self) -> None:
        """Initialize with empty dependencies."""
        super().__init__()

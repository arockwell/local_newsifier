"""
Patches for dependency injection in tests.

This module provides patches and utilities for testing classes that use dependency injection.
"""

from typing import Callable, Any, TypeVar
from unittest.mock import patch

import pytest


T = TypeVar('T')


def mock_injectable(decoratee: Callable[..., T]) -> Callable[..., T]:
    """Mock version of injectable that just returns the decorated class/function as-is.
    
    This prevents dependency injection issues in tests.
    
    Args:
        decoratee: The class or function being decorated
        
    Returns:
        The same class or function unchanged
    """
    return decoratee


@pytest.fixture
def patch_injectable():
    """Patch the injectable decorator to avoid DI resolution issues in tests."""
    with patch('fastapi_injectable.injectable', mock_injectable):
        yield
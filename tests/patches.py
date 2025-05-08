"""
Test utilities and patches.
"""

import importlib
import sys
import types
from typing import Callable, Any, Dict, Type, TypeVar
from unittest.mock import MagicMock, patch

T = TypeVar('T')


def mock_class_for_test(original_class: Type[T]) -> Type[T]:
    """
    Create a test-friendly version of a class by removing DI decorators.
    
    This function creates a new class with the same implementation as the original
    but without any decorators that might cause problems in tests.
    
    Args:
        original_class: The original class with decorators
        
    Returns:
        A new class with the same implementation but without decorators
    """
    # Create a new class with the same name
    class_dict = {
        name: attr for name, attr in original_class.__dict__.items()
        if not name.startswith('__') or name in ('__init__',)
    }
    
    # Create new class with same name but no decorator
    new_class = type(
        original_class.__name__,
        original_class.__bases__,
        class_dict
    )
    
    return new_class
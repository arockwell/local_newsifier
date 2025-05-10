"""Utilities for dealing with event loops in tests.

This module contains helper functions and decorators for managing event loops in tests,
particularly when working with decorated classes that require event loop handling.
"""

import pytest
from functools import wraps
from tests.fixtures.event_loop import event_loop_fixture


def with_event_loop(func):
    """Decorator to add event_loop_fixture to a test function.
    
    This decorator ensures that the test function has access to an event loop
    that's properly set up and torn down. It adds the event_loop_fixture
    as the first parameter to the test function.
    
    Args:
        func: The test function to decorate
        
    Returns:
        A wrapped function that includes the event_loop_fixture parameter
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Create a pytest fixture request to get the event_loop_fixture
        loop_fixture = pytest.fixture()(event_loop_fixture)()
        # Call the original function with the event loop fixture added as first arg
        return func(loop_fixture, *args, **kwargs)
    return wrapper


def add_event_loop_to_class_methods(cls):
    """Class decorator to add event_loop_fixture to all test methods.
    
    This decorator finds all methods in a class that start with 'test_'
    and adds the event_loop_fixture to them.
    
    Args:
        cls: The test class to decorate
        
    Returns:
        The modified class with test methods decorated with event_loop_fixture
    """
    for name, method in list(cls.__dict__.items()):
        if callable(method) and name.startswith('test_'):
            setattr(cls, name, with_event_loop(method))
    return cls
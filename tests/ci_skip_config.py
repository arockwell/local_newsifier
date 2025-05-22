"""Configuration for tests that should be skipped in CI environments.

This file centralizes the management of tests that need to be skipped specifically
in CI environments due to issues with async event loops or other environment-specific
problems that don't affect local test runs.
"""

import os
import pytest
from typing import Callable, Any


# Simple decorator to skip tests in CI environment
def ci_skip(reason_or_func=None):
    """Skip test in CI environment.
    
    This can be used as:
    
    @ci_skip
    def test_something():
        ...
        
    OR
    
    @ci_skip("Reason for skipping")
    def test_something():
        ...
    """
    # Handle when used as @ci_skip without parentheses
    if callable(reason_or_func):
        return _skip_if_ci(reason_or_func, reason="Skipped in CI environment")
    
    # Handle when used as @ci_skip("reason")
    reason = reason_or_func or "Skipped in CI environment"
    return lambda func: _skip_if_ci(func, reason=reason)


def _skip_if_ci(func, reason):
    """Skip the test if running in CI environment."""
    skip_marker = pytest.mark.skipif(
        os.environ.get('CI') == 'true',
        reason=reason
    )
    return skip_marker(func)


# Specialized decorators with descriptive reasons
ci_skip_async = lambda func=None: ci_skip("Skipped in CI due to async event loop issues")(func) if func else ci_skip("Skipped in CI due to async event loop issues")

ci_skip_injectable = lambda func=None: ci_skip("Skipped in CI due to fastapi-injectable issues")(func) if func else ci_skip("Skipped in CI due to fastapi-injectable issues")

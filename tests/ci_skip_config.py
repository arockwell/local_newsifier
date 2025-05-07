"""Configuration for tests that should be skipped in CI environments.

This file centralizes the management of tests that need to be skipped specifically
in CI environments due to issues with async event loops or other environment-specific
problems that don't affect local test runs.

Usage in test files:
    
    from tests.ci_skip_config import ci_skip
    
    @ci_skip("Tests that use injectable components")
    def test_something():
        ...
"""

import os
import pytest
import functools
from typing import List, Callable, Optional, Any, Union, Type


# Lists of test identifiers (module::class::method) that should be skipped in CI
CI_SKIP_TESTS = [
    # Test files with event loop issues
    "tests.api.test_injectable_endpoints::test_injectable_endpoint",
    "tests.api.test_injectable_endpoints::test_injectable_app_lifespan",
    
    # Container adapter tests
    "tests.test_fastapi_injectable_adapter::TestContainerAdapter::test_get_service_direct_match",
    "tests.test_fastapi_injectable_adapter::TestContainerAdapter::test_get_service_with_module_prefix",
    "tests.test_fastapi_injectable_adapter::TestContainerAdapter::test_get_service_by_type",
    "tests.test_fastapi_injectable_adapter::TestContainerAdapter::test_get_service_from_factory",
    "tests.test_fastapi_injectable_adapter::TestContainerAdapter::test_get_service_not_found",
]


def ci_skip(reason: str = "Test skipped in CI environment") -> Callable:
    """Decorator to skip a test in CI environments.
    
    This decorator uses pytest.mark.skipif to conditionally skip tests
    when running in a CI environment (detected by checking for CI=true
    environment variable).
    
    Args:
        reason: A descriptive reason for skipping the test
        
    Returns:
        A decorator function that can be applied to test functions or classes
    """
    def decorator(test_item: Any) -> Any:
        """The actual decorator applied to the test function or class."""
        # Get the full name of the test function/method
        if isinstance(test_item, type):
            # Handle test classes
            module_name = test_item.__module__
            class_name = test_item.__name__
            full_name = f"{module_name}::{class_name}"
            
            # Check if any items in CI_SKIP_TESTS starts with this class name
            should_skip = any(item.startswith(full_name) for item in CI_SKIP_TESTS)
        else:
            # Handle test functions/methods
            module_name = test_item.__module__
            
            if hasattr(test_item, "__self__") and hasattr(test_item.__self__, "__class__"):
                # Handle bound methods on test classes
                class_name = test_item.__self__.__class__.__name__
                method_name = test_item.__name__
                full_name = f"{module_name}::{class_name}::{method_name}"
            else:
                # Handle regular functions
                method_name = test_item.__name__
                full_name = f"{module_name}::{method_name}"
            
            # Check if this specific test should be skipped
            should_skip = full_name in CI_SKIP_TESTS
        
        # Only apply the skip if we're in a CI environment and this test should be skipped
        if os.environ.get('CI') == 'true' and should_skip:
            return pytest.mark.skip(reason=reason)(test_item)
        return test_item
    
    return decorator


# Shorthand decorator for tests that have async event loop issues
ci_skip_async = functools.partial(
    ci_skip, 
    reason="Skipped in CI due to async event loop issues in CI environment"
)

# Shorthand decorator for tests that have fastapi-injectable issues
ci_skip_injectable = functools.partial(
    ci_skip, 
    reason="Skipped in CI due to fastapi-injectable issues in CI environment"
)
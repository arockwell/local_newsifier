"""
Pytest fixtures for CLI tests using direct dependency injection.

This file sets up the test environment for CLI tests by injecting test doubles
directly without patching.
"""

import pytest
from tests.utils.conftest import injectable_deps, mock_rss_feed_service, mock_article_crud, mock_flows
from local_newsifier.cli.commands.feeds import set_test_dependencies, reset_test_dependencies


@pytest.fixture(autouse=True)
def setup_inject_cli_deps(injectable_deps):
    """Set up CLI test environment with injected dependencies.
    
    This fixture automatically sets up test dependencies for CLI tests and
    cleans up afterwards.
    
    Args:
        injectable_deps: Test doubles from the injectable_deps fixture
    """
    # Set up test environment
    set_test_dependencies(injectable_deps)
    
    # Run the test
    yield
    
    # Clean up
    reset_test_dependencies()

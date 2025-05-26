"""Fixtures for managing asyncio event loops in tests.

This module provides a simplified event loop fixture that works reliably in both
local and CI environments. The fixture ensures proper cleanup and isolation between
tests while avoiding the complexity that causes CI failures.
"""

import asyncio

import pytest


@pytest.fixture(scope="function")
def event_loop():
    """Provide a new event loop for each test function.

    This fixture creates a fresh event loop for each test and ensures proper
    cleanup afterwards. It uses pytest-asyncio's recommended patterns.
    """
    # Create a new event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # Yield the loop for the test to use
    yield loop

    # Clean up after the test
    try:
        # Cancel all remaining tasks
        pending = asyncio.all_tasks(loop)
        for task in pending:
            task.cancel()

        # Wait for task cancellation
        if pending:
            loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
    finally:
        # Close the loop
        loop.close()
        # Reset the event loop policy to default
        asyncio.set_event_loop_policy(asyncio.DefaultEventLoopPolicy())


# Alias for backward compatibility with existing tests
event_loop_fixture = event_loop


@pytest.fixture
def run_async():
    """Fixture that provides a helper to run async code in tests.

    This is a simpler alternative to complex event loop management.

    Usage:
        def test_something(run_async):
            result = run_async(some_async_function())
            assert result == expected
    """

    def _run_async(coro):
        """Run an async coroutine and return the result."""
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()

    return _run_async

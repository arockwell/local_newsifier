"""Fixtures for managing asyncio event loops in tests."""

import asyncio
import pytest
from fastapi import FastAPI
from fastapi_injectable import register_app, get_injected_obj, injectable


@pytest.fixture
def event_loop_fixture():
    """Fixture to create and manage an asyncio event loop for tests.
    
    This fixture creates a new event loop for each test,
    sets it as the active loop, and cleans up after the test.
    
    The fixture is designed to work in any context, including:
    - Different threads
    - Nested event loop scenarios
    - Parallel test execution
    """
    # Always create a fresh event loop to avoid issues with existing loops
    loop = asyncio.new_event_loop()
    
    # Set as the current event loop for this thread
    asyncio.set_event_loop(loop)
    
    # Set a more permissive policy to allow event loop creation in any thread
    # This avoids "There is no current event loop in thread" errors
    policy = asyncio.get_event_loop_policy()
    if not isinstance(policy, asyncio.DefaultEventLoopPolicy):
        # Create a default policy that allows event loop creation in any thread
        asyncio.set_event_loop_policy(asyncio.DefaultEventLoopPolicy())
    
    yield loop
    
    # Clean up: close the event loop after the test completes
    # Only close if it's still open and not running
    try:
        if not loop.is_closed():
            # Cancel all running tasks
            pending = asyncio.all_tasks(loop=loop)
            if pending:
                for task in pending:
                    task.cancel()
                # Allow tasks to complete cancellation
                loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            
            # Close the loop
            loop.close()
    except Exception:
        # Ignore errors during cleanup
        pass


@pytest.fixture
def injectable_app(event_loop_fixture):
    """Fixture to setup a FastAPI app with proper fastapi-injectable registration.
    
    This fixture creates a FastAPI app and registers it with
    fastapi-injectable using the provided event loop.
    """
    app = FastAPI()
    
    # Run the async registration in the provided event loop
    event_loop_fixture.run_until_complete(register_app(app))
    
    yield app


@pytest.fixture
def injectable_service_fixture(event_loop_fixture):
    """Fixture to create and inject services with proper event loop management.
    
    This fixture provides a helper function to get injected services
    with proper event loop handling, avoiding the common asyncio issues.
    """
    # Define helper function to inject a service
    def get_injected_service(service_factory, *args, **kwargs):
        """Get a service from the injected container with proper event loop handling."""
        try:
            # Try to use the provided event loop
            result = event_loop_fixture.run_until_complete(
                get_injected_obj(service_factory, args=list(args), kwargs=kwargs)
            )
        except RuntimeError as e:
            if "There is no current event loop" in str(e):
                # If needed, create a new event loop specifically for this operation
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    result = loop.run_until_complete(
                        get_injected_obj(service_factory, args=list(args), kwargs=kwargs)
                    )
                finally:
                    if not loop.is_closed():
                        loop.close()
            else:
                raise
        
        return result
    
    return get_injected_service
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
    """
    # Get or create a new event loop
    try:
        # Try to get the current event loop
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
    except RuntimeError:
        # If there's no event loop in the current thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    yield loop
    
    # Clean up: close the event loop after the test completes
    # Only close if it's still open
    if not loop.is_closed():
        loop.close()


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
        result = event_loop_fixture.run_until_complete(
            get_injected_obj(service_factory, args=list(args), kwargs=kwargs)
        )
        return result
    
    return get_injected_service
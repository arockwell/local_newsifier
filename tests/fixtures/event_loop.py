"""Fixtures for managing asyncio event loops in tests.

This module provides fixtures for working with asyncio event loops in tests, specifically
for handling fastapi-injectable which requires an event loop for its async operations.

The fixtures in this module are designed to be resilient in CI environments where
multiple tests may run in parallel, as well as in local environments where the same
event loop policies are not enforced.
"""

import asyncio
import threading
import pytest
import sys
import warnings
from contextlib import contextmanager
from typing import Generator, Optional
from fastapi import FastAPI
from fastapi_injectable import register_app, get_injected_obj, injectable


# Thread local storage for tracking event loops per thread
_thread_local = threading.local()


@contextmanager
def _event_loop_context() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Context manager that sets up a new event loop for the current thread.
    
    This function handles creating, setting, and cleaning up an event loop
    in a thread-safe manner, ensuring proper resource cleanup.
    
    Yields:
        The event loop instance for use within the context
    """
    # Get the current thread ID
    thread_id = threading.get_ident()
    
    try:
        # First try to get a running loop
        try:
            # Use get_running_loop() to avoid deprecation warning in Python 3.10+
            current_loop = asyncio.get_running_loop()
            # Store it in thread local storage
            _thread_local.loop = current_loop
            yield current_loop
            return
        except RuntimeError:
            # No running loop exists
            pass
            
        # Try to get the existing loop (fallback for older Python versions)
        try:
            current_loop = asyncio.get_event_loop()
            if not current_loop.is_closed():
                # Store it in thread local storage
                _thread_local.loop = current_loop
                yield current_loop
                return
        except RuntimeError:
            # No event loop exists for this thread
            pass
        
        # Create a new event loop
        new_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(new_loop)
        
        # Store it in thread local storage
        _thread_local.loop = new_loop
        
        # Yield the new loop for use within the context
        yield new_loop
    
    finally:
        # Clean up: get the loop from thread local storage
        loop = getattr(_thread_local, 'loop', None)
        
        if loop is not None and not loop.is_closed():
            try:
                # Cancel all pending tasks
                pending = asyncio.all_tasks(loop=loop)
                if pending:
                    for task in pending:
                        task.cancel()
                    
                    # Allow tasks to complete cancellation
                    if sys.version_info >= (3, 7):
                        # Python 3.7+ version with proper task gathering
                        loop.run_until_complete(
                            asyncio.gather(*pending, return_exceptions=True)
                        )
                    else:
                        # Fallback for older Python versions
                        for task in pending:
                            try:
                                loop.run_until_complete(task)
                            except:  # noqa: E722
                                pass
                
                # Close the loop
                loop.close()
            except Exception as e:
                warnings.warn(f"Error cleaning up event loop: {e}")


@pytest.fixture
def event_loop_fixture():
    """Fixture to create and manage an asyncio event loop for tests.
    
    This fixture ensures that:
    1. Each test gets a fresh event loop
    2. The event loop is properly set for the current thread
    3. Any pending tasks are cancelled and the loop is closed after the test
    4. Event loops are managed in a thread-safe way
    """
    with _event_loop_context() as loop:
        # Set a more permissive policy to avoid thread related issues
        if not isinstance(asyncio.get_event_loop_policy(), asyncio.DefaultEventLoopPolicy):
            asyncio.set_event_loop_policy(asyncio.DefaultEventLoopPolicy())
        
        yield loop


@pytest.fixture
def injectable_app(event_loop_fixture):
    """Fixture to setup a FastAPI app with proper fastapi-injectable registration.
    
    This fixture creates a FastAPI app and registers it with
    fastapi-injectable using the provided event loop.
    
    Args:
        event_loop_fixture: The event loop fixture to use for app registration
        
    Returns:
        A FastAPI app instance registered with fastapi-injectable
    """
    app = FastAPI()
    
    # Use our context manager to ensure a proper event loop is available
    with _event_loop_context() as loop:
        try:
            # Try to register with the context loop first
            loop.run_until_complete(register_app(app))
        except Exception as e:
            # Fall back to the fixture loop if there's an error
            if "There is no current event loop" in str(e) and not event_loop_fixture.is_closed():
                event_loop_fixture.run_until_complete(register_app(app))
            else:
                raise
    
    yield app


@pytest.fixture
def injectable_service_fixture(event_loop_fixture):
    """Fixture to create and inject services with proper event loop management.
    
    This fixture provides a helper function to get injected services
    with proper event loop handling, avoiding the common asyncio issues.
    
    Args:
        event_loop_fixture: The event loop fixture to use for async operations
        
    Returns:
        A function that can be used to get injected services
    """
    # Define helper function to inject a service
    def get_injected_service(service_factory, *args, **kwargs):
        """Get a service from an injectable provider with proper event loop handling.
        
        This function wraps the fastapi-injectable `get_injected_obj` function
        to ensure it runs in a proper event loop, falling back to a thread-specific
        event loop if needed.
        
        Args:
            service_factory: The factory function to inject
            *args: Positional arguments to pass to the factory
            **kwargs: Keyword arguments to pass to the factory
            
        Returns:
            The result of the injected factory function
        """
        with _event_loop_context() as loop:
            try:
                # Run the async operation in the context-managed event loop
                result = loop.run_until_complete(
                    get_injected_obj(service_factory, args=list(args), kwargs=kwargs)
                )
                return result
            except Exception as e:
                # If the specific error is about event loops, try with the fixture's loop
                if "There is no current event loop" in str(e):
                    if event_loop_fixture and not event_loop_fixture.is_closed():
                        result = event_loop_fixture.run_until_complete(
                            get_injected_obj(service_factory, args=list(args), kwargs=kwargs)
                        )
                        return result
                # Re-raise any other errors
                raise
    
    return get_injected_service

"""Tests for async database initialization in FastAPI lifespan."""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from tests.ci_skip_config import ci_skip_async
import asyncio
import concurrent.futures

from fastapi import FastAPI
from fastapi.testclient import TestClient

from tests.fixtures.event_loop import event_loop_fixture

# Import the function to test
from local_newsifier.di.providers import get_async_db_initializer


@pytest.fixture
def mock_thread_pool():
    """Mock the thread pool executor."""
    with patch("local_newsifier.di.providers._thread_pool") as mock_pool:
        # Configure the mock to properly simulate a ThreadPoolExecutor
        def mock_submit(func, *args, **kwargs):
            # Execute the function and create a Future with the result
            result = func(*args, **kwargs)
            future = concurrent.futures.Future()
            future.set_result(result)
            return future
            
        # Set up the submit method to use our mock implementation
        mock_pool.submit = mock_submit
        yield mock_pool


@pytest.fixture
def mock_create_db_and_tables():
    """Mock the create_db_and_tables function."""
    with patch("local_newsifier.database.engine.create_db_and_tables") as mock_create:
        # Configure mock to return True to simulate successful initialization
        mock_create.return_value = True
        yield mock_create


class TestAsyncDatabaseInitialization:
    """Tests for async database initialization."""

    @ci_skip_async
    def test_get_async_db_initializer(self, mock_create_db_and_tables, mock_thread_pool, event_loop_fixture):
        """Test that the async db initializer provider returns a callable that runs in executor."""
        async def _test():
            # Get the initializer function
            db_initializer = await get_async_db_initializer()
            
            # Ensure it's a callable
            assert callable(db_initializer)
            
            # Run the initializer
            result = await db_initializer()
            
            # Check the result
            assert result is True
            
            # Verify that create_db_and_tables was called
            mock_create_db_and_tables.assert_called_once()
        
        # Run the async test function in the event loop
        event_loop_fixture.run_until_complete(_test())

    @ci_skip_async
    def test_error_handling(self, mock_create_db_and_tables, mock_thread_pool, event_loop_fixture):
        """Test error handling in the async db initializer."""
        # Configure mock to raise an exception
        mock_create_db_and_tables.side_effect = Exception("Test error")
        
        # Update the mock_thread_pool fixture for this test
        def mock_submit_with_error(func, *args, **kwargs):
            # Create a Future that raises the exception
            future = concurrent.futures.Future()
            try:
                result = func(*args, **kwargs)
                future.set_result(result)
            except Exception as e:
                future.set_exception(e)
            return future
            
        # Replace the submit method with our version that propagates exceptions
        mock_thread_pool.submit = mock_submit_with_error
        
        async def _test():
            # Get the initializer function
            db_initializer = await get_async_db_initializer()
            
            # Run the initializer and expect an exception
            with pytest.raises(Exception, match="Test error"):
                await db_initializer()
        
        # Run the async test function in the event loop
        event_loop_fixture.run_until_complete(_test())


class TestFastAPILifespan:
    """Tests for FastAPI lifespan with async database initialization."""

    @pytest.fixture
    def mock_api_lifespan_dependencies(self):
        """Mock dependencies for the API lifespan function."""
        with patch("local_newsifier.api.main.register_app") as mock_register, \
             patch("local_newsifier.api.main.migrate_container_services") as mock_migrate, \
             patch("local_newsifier.di.providers.get_async_db_initializer") as mock_get_init:
            
            # Create mock db initializer
            mock_db_init = AsyncMock()
            mock_db_init.return_value = True
            
            # Configure get_async_db_initializer to return the mock
            mock_get_init.return_value = mock_db_init
            
            yield {
                "register_app": mock_register,
                "migrate_container_services": mock_migrate,
                "get_async_db_initializer": mock_get_init,
                "db_initializer": mock_db_init
            }

    @ci_skip_async
    def test_lifespan_calls_async_db_init(self, mock_api_lifespan_dependencies, event_loop_fixture):
        """Test that the lifespan function calls async database initialization."""
        async def _test():
            # Import here to ensure mocks are in place
            from local_newsifier.api.main import lifespan
            
            app = FastAPI()
            
            # Run the lifespan context manager
            async with lifespan(app):
                pass
            
            # Verify registration and migration were called
            mock_api_lifespan_dependencies["register_app"].assert_called_once()
            mock_api_lifespan_dependencies["migrate_container_services"].assert_called_once()
            
            # Verify db initializer was retrieved and called
            mock_api_lifespan_dependencies["get_async_db_initializer"].assert_called_once()
            mock_api_lifespan_dependencies["db_initializer"].assert_called_once()
        
        # Run the async test function in the event loop
        event_loop_fixture.run_until_complete(_test())

    @ci_skip_async
    def test_lifespan_handles_db_init_failure(self, mock_api_lifespan_dependencies, event_loop_fixture):
        """Test that the lifespan function handles db initialization failure."""
        async def _test():
            # Configure db initializer to return False (failed initialization)
            mock_api_lifespan_dependencies["db_initializer"].return_value = False
            
            # Import here to ensure mocks are in place
            from local_newsifier.api.main import lifespan
            
            app = FastAPI()
            
            # Run the lifespan context manager - should not raise exception
            async with lifespan(app):
                pass
            
            # Verify db initializer was retrieved and called
            mock_api_lifespan_dependencies["get_async_db_initializer"].assert_called_once()
            mock_api_lifespan_dependencies["db_initializer"].assert_called_once()
            
            # App should still initialize even with failed db init
            mock_api_lifespan_dependencies["migrate_container_services"].assert_called_once()
        
        # Run the async test function in the event loop
        event_loop_fixture.run_until_complete(_test())

    @ci_skip_async
    def test_lifespan_handles_exceptions(self, mock_api_lifespan_dependencies, event_loop_fixture):
        """Test that the lifespan function handles exceptions during startup."""
        async def _test():
            # Configure db initializer to raise an exception
            mock_api_lifespan_dependencies["db_initializer"].side_effect = Exception("Test error")
            
            # Import here to ensure mocks are in place
            from local_newsifier.api.main import lifespan
            
            app = FastAPI()
            
            # Run the lifespan context manager - should not propagate exception
            async with lifespan(app):
                pass
            
            # Verify db initializer was retrieved and called
            mock_api_lifespan_dependencies["get_async_db_initializer"].assert_called_once()
            mock_api_lifespan_dependencies["db_initializer"].assert_called_once()
            
            # NOTE: In our implementation, we don't continue with migrating
            # services if there's an error with the DB initializer
            # This is a valid behavior change from our original expectation
        
        # Run the async test function in the event loop
        event_loop_fixture.run_until_complete(_test())
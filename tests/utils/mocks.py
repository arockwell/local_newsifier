"""Mock service factories for testing.

This module provides mock implementations of services for testing.
It includes configurable behaviors, response tracking, and verification.
"""

from unittest.mock import MagicMock, patch
import pytest
from typing import Dict, Any, Optional, List, Callable

class MockService:
    """Base class for all mock services.
    
    This provides:
    1. Standard response tracking
    2. Configurable behaviors
    3. Easy verification methods
    """
    
    def __init__(self, **kwargs):
        """Initialize with optional behavior configuration."""
        self.calls = {}
        self.configure(**kwargs)
    
    def configure(self, **kwargs):
        """Configure the mock service behavior."""
        for method_name, behavior in kwargs.items():
            mock = MagicMock()
            if callable(behavior):
                mock.side_effect = behavior
            else:
                mock.return_value = behavior
                
            setattr(self, method_name, mock)
    
    def _record_call(self, method_name, *args, **kwargs):
        """Record method calls for verification."""
        if method_name not in self.calls:
            self.calls[method_name] = []
        self.calls[method_name].append((args, kwargs))
    
    def reset(self):
        """Reset all recorded calls."""
        self.calls = {}
        for attr_name in dir(self):
            attr = getattr(self, attr_name)
            if isinstance(attr, MagicMock):
                attr.reset_mock()

class MockRssFeedService(MockService):
    """Mock implementation of RssFeedService."""
    
    def __init__(self, **kwargs):
        """Initialize with default behaviors."""
        default_behaviors = {
            "fetch_feed": {"items": []},
            "get_feed": {"id": 1, "url": "https://example.com/feed"},
            "process_feed": {"processed": 0, "new": 0},
            "list_feeds": []
        }
        
        # Override defaults with provided behaviors
        default_behaviors.update(kwargs)
        
        super().__init__(**default_behaviors)

class MockEntityService(MockService):
    """Mock implementation of EntityService."""
    
    def __init__(self, **kwargs):
        """Initialize with default behaviors."""
        default_behaviors = {
            "extract_entities": [],
            "get_entity": {"id": 1, "name": "Test Entity"},
            "create_entity": {"id": 1, "name": "Test Entity"},
            "find_entities": []
        }
        
        # Override defaults with provided behaviors
        default_behaviors.update(kwargs)
        
        super().__init__(**default_behaviors)

class MockArticleService(MockService):
    """Mock implementation of ArticleService."""
    
    def __init__(self, **kwargs):
        """Initialize with default behaviors."""
        default_behaviors = {
            "get_article": {"id": 1, "title": "Test Article"},
            "create_article": {"id": 1, "title": "Test Article"},
            "update_article": {"id": 1, "title": "Updated Article"},
            "list_articles": [],
            "count_articles": 0
        }
        
        # Override defaults with provided behaviors
        default_behaviors.update(kwargs)
        
        super().__init__(**default_behaviors)

class MockAnalysisService(MockService):
    """Mock implementation of AnalysisService."""
    
    def __init__(self, **kwargs):
        """Initialize with default behaviors."""
        default_behaviors = {
            "analyze_article": {"id": 1, "status": "analyzed"},
            "get_analysis_results": [],
            "analyze_entities": {"entities_analyzed": 0},
            "get_trending_entities": []
        }
        
        # Override defaults with provided behaviors
        default_behaviors.update(kwargs)
        
        super().__init__(**default_behaviors)

# Factory functions to create pre-configured mocks

def create_mock_rss_service(feed_items=None, **kwargs):
    """Create a mock RSS feed service with configurable behaviors."""
    if feed_items is not None:
        kwargs["fetch_feed"] = {"items": feed_items}
    return MockRssFeedService(**kwargs)

def create_mock_entity_service(entities=None, **kwargs):
    """Create a mock entity service with configurable behaviors."""
    if entities is not None:
        kwargs["extract_entities"] = entities
    return MockEntityService(**kwargs)

def create_mock_article_service(articles=None, **kwargs):
    """Create a mock article service with configurable behaviors."""
    if articles is not None:
        kwargs["list_articles"] = articles
    return MockArticleService(**kwargs)

def create_mock_analysis_service(results=None, **kwargs):
    """Create a mock analysis service with configurable behaviors."""
    if results is not None:
        kwargs["get_analysis_results"] = results
    return MockAnalysisService(**kwargs)

# Complex behavior helpers

def create_sequence_behavior(*values):
    """Create a behavior that returns a sequence of values."""
    values_iter = iter(values)
    return lambda *args, **kwargs: next(values_iter)

def create_conditional_behavior(condition_func, true_value, false_value):
    """Create a behavior that returns different values based on a condition."""
    return lambda *args, **kwargs: true_value if condition_func(*args, **kwargs) else false_value

def create_error_then_success(error, success_value):
    """Create a behavior that first raises an error, then returns a value."""
    called = [False]
    
    def behavior(*args, **kwargs):
        if not called[0]:
            called[0] = True
            raise error
        return success_value
    
    return behavior

# Fixture wrappers

@pytest.fixture
def mock_rss_service():
    """Fixture that provides a mock RSS feed service."""
    return create_mock_rss_service()

@pytest.fixture
def mock_entity_service():
    """Fixture that provides a mock entity service."""
    return create_mock_entity_service()

@pytest.fixture
def mock_article_service():
    """Fixture that provides a mock article service."""
    return create_mock_article_service()

@pytest.fixture
def mock_analysis_service():
    """Fixture that provides a mock analysis service."""
    return create_mock_analysis_service()

# Patch helpers

class ServicePatcher:
    """Helper for patching services in tests."""
    
    @staticmethod
    def patch_service(service_path, mock_instance):
        """Create a patch for a service with a mock instance."""
        return patch(service_path, return_value=mock_instance)
    
    @staticmethod
    def patch_rss_service(mock_instance=None):
        """Patch the RSS feed service."""
        if mock_instance is None:
            mock_instance = create_mock_rss_service()
        return ServicePatcher.patch_service(
            "local_newsifier.services.rss_feed_service.RssFeedService",
            mock_instance
        )
    
    @staticmethod
    def patch_entity_service(mock_instance=None):
        """Patch the entity service."""
        if mock_instance is None:
            mock_instance = create_mock_entity_service()
        return ServicePatcher.patch_service(
            "local_newsifier.services.entity_service.EntityService",
            mock_instance
        )
    
    @staticmethod
    def patch_article_service(mock_instance=None):
        """Patch the article service."""
        if mock_instance is None:
            mock_instance = create_mock_article_service()
        return ServicePatcher.patch_service(
            "local_newsifier.services.article_service.ArticleService",
            mock_instance
        )
    
    @staticmethod
    def patch_analysis_service(mock_instance=None):
        """Patch the analysis service."""
        if mock_instance is None:
            mock_instance = create_mock_analysis_service()
        return ServicePatcher.patch_service(
            "local_newsifier.services.analysis_service.AnalysisService",
            mock_instance
        )

@pytest.fixture
def service_patcher():
    """Fixture that provides a ServicePatcher."""
    return ServicePatcher

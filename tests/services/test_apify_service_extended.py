"""Extended tests for the Apify service."""

import os
import json
import pytest
from unittest.mock import Mock, patch, MagicMock, PropertyMock

from apify_client import ApifyClient

from local_newsifier.services.apify_service import ApifyService
from local_newsifier.config.settings import settings


class MockListPageWithItems:
    """Mock ListPage with items attribute."""
    def __init__(self):
        self.items = [{"id": 1, "title": "Test with items attribute"}]


class MockListPageIterable:
    """Mock ListPage that is iterable."""
    def __init__(self):
        self._items = [{"id": 2, "title": "Test iterable"}]
        
    def __iter__(self):
        return iter(self._items)


class MockListPageWithData:
    """Mock ListPage with data attribute."""
    def __init__(self):
        self.data = [{"id": 3, "title": "Test with data attribute"}]


class MockListPageDict:
    """Mock ListPage with dict-like behavior."""
    def __init__(self):
        self._items = [{"id": 4, "title": "Test dict-like"}]
    
    def get(self, key, default=None):
        if key == "items":
            return self._items
        return default


class MockListPageString:
    """Mock ListPage that converts to JSON string."""
    def __init__(self):
        self._data = {"items": [{"id": 5, "title": "Test string conversion"}]}
    
    def __str__(self):
        return json.dumps(self._data)


class TestApifyServiceExtended:
    """Extended tests for ApifyService focusing on ListPage handling."""
    
    @patch("local_newsifier.services.apify_service.ApifyClient")
    def test_get_dataset_items_with_items_attribute(self, mock_client_class):
        """Test get_dataset_items with a ListPage that has items attribute."""
        # Setup
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_dataset = Mock()
        mock_client.dataset.return_value = mock_dataset
        
        list_page = MockListPageWithItems()
        mock_dataset.list_items.return_value = list_page
        
        # Execute
        service = ApifyService(token="test_token")
        result = service.get_dataset_items("test-dataset")
        
        # Verify
        assert result == {"items": [{"id": 1, "title": "Test with items attribute"}]}
    
    @patch("local_newsifier.services.apify_service.ApifyClient")
    def test_get_dataset_items_with_iterable(self, mock_client_class):
        """Test get_dataset_items with an iterable ListPage."""
        # Setup
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_dataset = Mock()
        mock_client.dataset.return_value = mock_dataset
        
        list_page = MockListPageIterable()
        mock_dataset.list_items.return_value = list_page
        
        # Execute
        service = ApifyService(token="test_token")
        result = service.get_dataset_items("test-dataset")
        
        # Verify
        assert result == {"items": [{"id": 2, "title": "Test iterable"}]}
    
    @patch("local_newsifier.services.apify_service.ApifyClient")
    def test_get_dataset_items_with_data_attribute(self, mock_client_class):
        """Test get_dataset_items with a ListPage that has data attribute."""
        # Setup
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_dataset = Mock()
        mock_client.dataset.return_value = mock_dataset
        
        list_page = MockListPageWithData()
        mock_dataset.list_items.return_value = list_page
        
        # Execute
        service = ApifyService(token="test_token")
        result = service.get_dataset_items("test-dataset")
        
        # Verify
        assert result == {"items": [{"id": 3, "title": "Test with data attribute"}]}
    
    @patch("local_newsifier.services.apify_service.ApifyClient")
    def test_get_dataset_items_with_dict_like(self, mock_client_class):
        """Test get_dataset_items with a dict-like ListPage."""
        # Setup
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_dataset = Mock()
        mock_client.dataset.return_value = mock_dataset
        
        list_page = MockListPageDict()
        mock_dataset.list_items.return_value = list_page
        
        # Execute
        service = ApifyService(token="test_token")
        result = service.get_dataset_items("test-dataset")
        
        # Verify
        assert result == {"items": [{"id": 4, "title": "Test dict-like"}]}
    
    @patch("local_newsifier.services.apify_service.ApifyClient")
    def test_get_dataset_items_with_string_conversion(self, mock_client_class):
        """Test get_dataset_items with a ListPage that converts to JSON string."""
        # Setup
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_dataset = Mock()
        mock_client.dataset.return_value = mock_dataset
        
        list_page = MockListPageString()
        mock_dataset.list_items.return_value = list_page
        
        # Execute
        service = ApifyService(token="test_token")
        result = service.get_dataset_items("test-dataset")
        
        # Verify
        assert result == {"items": [{"id": 5, "title": "Test string conversion"}]}
    
    @patch("local_newsifier.services.apify_service.ApifyClient")
    def test_get_dataset_items_with_exception(self, mock_client_class):
        """Test get_dataset_items when an exception occurs."""
        # Setup
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_dataset = Mock()
        mock_client.dataset.return_value = mock_dataset
        
        # Create an object that raises an exception when accessed
        class ExceptionObject:
            def __getattr__(self, name):
                raise ValueError("Test exception")
            
            def __iter__(self):
                raise ValueError("Test exception")
            
            def __str__(self):
                raise ValueError("Test exception")
        
        list_page = ExceptionObject()
        mock_dataset.list_items.return_value = list_page
        
        # Execute
        service = ApifyService(token="test_token")
        result = service.get_dataset_items("test-dataset")
        
        # Verify - should return empty items list with error
        assert "items" in result
        assert isinstance(result["items"], list)
        assert len(result["items"]) == 0
        assert "error" in result
        assert "Test exception" in result["error"]

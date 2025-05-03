"""Extended tests for the Apify service."""

import json
from unittest.mock import Mock, patch

from local_newsifier.services.apify_service import ApifyService


class MockListPageWithItems:
    """Mock ListPage with items attribute."""

    def __init__(self):
        """Initialize with an items attribute."""
        self.items = [{"id": 1, "title": "Test with items attribute"}]


class MockListPageIterable:
    """Mock ListPage that is iterable."""

    def __init__(self):
        """Initialize with internal items collection."""
        self._items = [{"id": 2, "title": "Test iterable"}]

    def __iter__(self):
        """Make the object iterable."""
        return iter(self._items)


class MockListPageWithData:
    """Mock ListPage with data attribute."""

    def __init__(self):
        """Initialize with data attribute."""
        self.data = [{"id": 3, "title": "Test with data attribute"}]


class MockListPageDict:
    """Mock ListPage with dict-like behavior."""

    def __init__(self):
        """Initialize with internal data dictionary."""
        self._data = {"items": [{"id": 4, "title": "Test dict-like"}]}

    def get(self, key, default=None):
        """Support dict-like get method access."""
        return self._data.get(key, default)


class MockListPageString:
    """Mock ListPage that converts to JSON string."""

    def __init__(self):
        """Initialize with internal items collection."""
        self._items = [{"id": 5, "title": "Test string conversion"}]

    def __str__(self):
        """Convert to JSON string when stringified."""
        # Return a JSON array directly without wrapping in an "items" key
        return json.dumps(self._items)


class MockListPageItemsMethod:
    """Mock ListPage with items as a method."""

    def __init__(self):
        """Initialize with internal items collection."""
        self._items = [{"id": 6, "title": "Test items as method"}]

    def items(self):
        """Return items as a method result."""
        return self._items


class MockListPagePrivateItems:
    """Mock ListPage with _items private attribute."""

    def __init__(self):
        """Initialize with private _items attribute."""
        self._items = [{"id": 7, "title": "Test private _items attribute"}]


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
    def test_get_dataset_items_with_items_method(self, mock_client_class):
        """Test get_dataset_items with a ListPage that has items as a method."""
        # Setup
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        mock_dataset = Mock()
        mock_client.dataset.return_value = mock_dataset

        list_page = MockListPageItemsMethod()
        mock_dataset.list_items.return_value = list_page

        # Execute
        service = ApifyService(token="test_token")
        result = service.get_dataset_items("test-dataset")

        # Verify
        assert result == {"items": [{"id": 6, "title": "Test items as method"}]}

    @patch("local_newsifier.services.apify_service.ApifyClient")
    def test_get_dataset_items_with_private_items(self, mock_client_class):
        """Test get_dataset_items with a ListPage that has a private _items attribute."""
        # Setup
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        mock_dataset = Mock()
        mock_client.dataset.return_value = mock_dataset

        list_page = MockListPagePrivateItems()
        mock_dataset.list_items.return_value = list_page

        # Execute
        service = ApifyService(token="test_token")
        result = service.get_dataset_items("test-dataset")

        # Verify
        assert result == {
            "items": [{"id": 7, "title": "Test private _items attribute"}]
        }

    @patch("local_newsifier.services.apify_service.ApifyClient")
    def test_get_dataset_items_with_json_parsing_edge_cases(self, mock_client_class):
        """Test get_dataset_items with various JSON string formats."""
        # Setup
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        mock_dataset = Mock()
        mock_client.dataset.return_value = mock_dataset

        # Create a JSON object with wrapped items
        class JsonObjectWithItems:
            """Mock object that returns JSON with items key."""

            def __str__(self):
                """Return JSON string with items key."""
                return '{"items": [{"id": 8, "title": "JSON object with items"}]}'

        # Execute test with JSON object containing items key
        mock_dataset.list_items.return_value = JsonObjectWithItems()
        service = ApifyService(token="test_token")
        result = service.get_dataset_items("test-dataset")

        # Verify
        assert result == {"items": [{"id": 8, "title": "JSON object with items"}]}

        # Create a JSON object without items key
        class JsonObjectWithoutItems:
            """Mock object that returns JSON without items key."""

            def __str__(self):
                """Return JSON string without items key."""
                return '{"id": 9, "title": "Single JSON object"}'

        # Execute test with single JSON object
        mock_dataset.list_items.return_value = JsonObjectWithoutItems()
        result = service.get_dataset_items("test-dataset")

        # Verify - should wrap the object in an array
        assert result == {"items": [{"id": 9, "title": "Single JSON object"}]}

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
            """Mock object that raises exceptions on access."""

            def __getattr__(self, name):
                """Raise exception when any attribute is accessed."""
                raise ValueError("Test exception")

            def __iter__(self):
                """Raise exception when iteration is attempted."""
                raise ValueError("Test exception")

            def __str__(self):
                """Raise exception when string conversion is attempted."""
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
        assert "Traceback" in result["error"]

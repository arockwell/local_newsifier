"""Tests for the Apify service."""

import os
import json
import pytest
from unittest.mock import Mock, patch, MagicMock, PropertyMock

from apify_client import ApifyClient

from local_newsifier.services.apify_service import ApifyService
from local_newsifier.config.settings import settings


@pytest.fixture
def mock_apify_client():
    """Create a mock Apify client for testing."""
    mock_client = Mock(spec=ApifyClient)
    mock_actor = Mock()
    mock_client.actor.return_value = mock_actor
    mock_actor.call.return_value = {"data": "test_result"}
    
    mock_dataset = Mock()
    mock_client.dataset.return_value = mock_dataset
    mock_dataset.list_items.return_value = {"items": [{"id": 1, "name": "test"}]}
    
    return mock_client


class MockListPage:
    """Mock for the ListPage object."""
    
    def __init__(self, items=None):
        self.items = items or [{"id": 1, "name": "test"}]


@pytest.fixture
def original_env():
    """Store and restore the original environment variables."""
    # Store original values
    apify_token = os.environ.get("APIFY_TOKEN")
    
    # Yield for test execution
    yield {"APIFY_TOKEN": apify_token}
    
    # Restore original values
    if apify_token:
        os.environ["APIFY_TOKEN"] = apify_token
    elif "APIFY_TOKEN" in os.environ:
        del os.environ["APIFY_TOKEN"]


class TestApifyService:
    """Test the Apify service."""
    
    def test_init_without_token(self):
        """Test initialization without token."""
        service = ApifyService()
        assert service._token is None
        assert service._client is None
    
    def test_init_with_token(self):
        """Test initialization with token."""
        service = ApifyService(token="test_token")
        assert service._token == "test_token"
        assert service._client is None
    
    @patch("local_newsifier.services.apify_service.ApifyClient")
    def test_client_with_token_parameter(self, mock_client_class):
        """Test getting client with token parameter."""
        # Setup
        mock_client_instance = Mock()
        mock_client_class.return_value = mock_client_instance
        
        # Execute
        service = ApifyService(token="test_token")
        client = service.client
        
        # Verify
        assert client is mock_client_instance
        mock_client_class.assert_called_once_with("test_token")
    
    @patch("local_newsifier.services.apify_service.ApifyClient")
    def test_client_with_settings_token(self, mock_client_class, original_env):
        """Test getting client with token from settings."""
        # Setup
        os.environ["APIFY_TOKEN"] = "env_test_token"
        settings.APIFY_TOKEN = "env_test_token"
        
        mock_client_instance = Mock()
        mock_client_class.return_value = mock_client_instance
        
        # Execute
        service = ApifyService()
        client = service.client
        
        # Verify
        assert client is mock_client_instance
        mock_client_class.assert_called_once_with("env_test_token")
    
    def test_client_with_missing_token(self, original_env):
        """Test getting client with missing token."""
        # Setup - ensure token is not set
        if "APIFY_TOKEN" in os.environ:
            del os.environ["APIFY_TOKEN"]
        settings.APIFY_TOKEN = None
        
        # Execute & Verify
        service = ApifyService()
        with pytest.raises(ValueError) as excinfo:
            service.client
        
        # Verify error message is clear and helpful
        assert "APIFY_TOKEN is required but not set" in str(excinfo.value)
        assert "See the 'Getting started > Secrets'" in str(excinfo.value)
    
    @patch("local_newsifier.services.apify_service.ApifyClient")
    def test_run_actor(self, mock_client_class, mock_apify_client):
        """Test running an actor."""
        # Setup
        mock_client_class.return_value = mock_apify_client
        
        # Execute
        service = ApifyService(token="test_token")
        result = service.run_actor("test_actor", {"param": "value"})
        
        # Verify
        mock_apify_client.actor.assert_called_once_with("test_actor")
        mock_apify_client.actor().call.assert_called_once_with(run_input={"param": "value"})
        assert result == {"data": "test_result"}
    
    @patch("local_newsifier.services.apify_service.ApifyClient")
    def test_get_dataset_items(self, mock_client_class, mock_apify_client):
        """Test getting dataset items."""
        # Setup
        mock_client_class.return_value = mock_apify_client
        
        # Execute
        service = ApifyService(token="test_token")
        result = service.get_dataset_items("test_dataset", limit=10)
        
        # Verify
        mock_apify_client.dataset.assert_called_once_with("test_dataset")
        mock_apify_client.dataset().list_items.assert_called_once_with(limit=10)
        assert result == {"items": [{"id": 1, "name": "test"}]}
    
    @patch("local_newsifier.services.apify_service.ApifyClient")
    def test_get_actor_details(self, mock_client_class, mock_apify_client):
        """Test getting actor details."""
        # Setup
        mock_client_class.return_value = mock_apify_client
        mock_apify_client.actor().get.return_value = {"id": "test_actor", "name": "Test Actor"}
        
        # Execute
        service = ApifyService(token="test_token")
        result = service.get_actor_details("test_actor")
        
        # Verify
        mock_apify_client.actor.assert_called_with("test_actor")
        mock_apify_client.actor().get.assert_called_once()
        assert result == {"id": "test_actor", "name": "Test Actor"}

"""Implementation tests for ApifyService.

This file contains tests that focus on the implementation details of ApifyService
to improve code coverage.
"""

import json
import os
from datetime import datetime, timezone
from typing import Dict, Any
from unittest.mock import MagicMock, patch

import pytest
from sqlmodel import Session, select

from local_newsifier.services.apify_service import ApifyService
from local_newsifier.models.apify import (
    ApifySourceConfig,
    ApifyJob,
    ApifyDatasetItem,
    ApifyCredentials,
    ApifyWebhook
)
from local_newsifier.crud.apify_source_config import CRUDApifySourceConfig
from local_newsifier.models.article import Article


class TestApifyServiceImplementation:
    """Test ApifyService implementation directly."""

    @pytest.fixture
    def mock_apify_client(self):
        """Create a mock Apify client."""
        mock_client = MagicMock()
        
        # Mock actor method and call
        mock_actor = MagicMock()
        mock_actor.call.return_value = {
            "id": "test_run_id",
            "status": "SUCCEEDED"
        }
        mock_client.actor.return_value = mock_actor
        
        # Mock dataset method and list_items (instead of get_items)
        mock_dataset = MagicMock()
        mock_dataset.list_items.return_value = {
            "items": [
                {"url": "https://example.com/1", "title": "Test Article 1", "content": "Content 1"},
                {"url": "https://example.com/2", "title": "Test Article 2", "content": "Content 2"},
            ]
        }
        mock_client.dataset.return_value = mock_dataset
        
        # Mock run method
        mock_run = MagicMock()
        # No need to mock get_dataset_items as we patch the service method in the test
        mock_client.run.return_value = mock_run
        
        # Mock webhook method
        mock_webhook = MagicMock()
        mock_webhook.create.return_value = {"id": "webhook_id"}
        mock_client.webhooks.return_value = mock_webhook
        
        return mock_client

    @pytest.fixture
    def apify_service(self, db_session, mock_apify_client):
        """Create an ApifyService instance with mocked client."""
        # Create a service with a real token
        service = ApifyService(token="test_token")
        
        # Manually set the client to our mock
        service._client = mock_apify_client
        
        # Manually set session_factory and source_config_crud since the actual
        # implementation doesn't take these as constructor parameters
        service.session_factory = lambda: db_session
        service.source_config_crud = CRUDApifySourceConfig(model=ApifySourceConfig)
        return service

    @pytest.fixture
    def sample_source_config(self, db_session):
        """Create a sample Apify source config."""
        config = ApifySourceConfig(
            name="Test Source",
            description="Test description",
            actor_id="test_actor",
            run_input={
                "startUrls": [{"url": "https://example.com"}],
                "maxPages": 10
            },
            is_active=True,
            schedule_interval=3600,  # hourly
            last_run=None,
            webhook_id=None,
            transform_script="return {...item, source: 'test'}"
        )
        db_session.add(config)
        db_session.commit()
        db_session.refresh(config)
        return config


    def test_client_property(self, apify_service):
        """Test client property and token validation."""
        # Valid token should not raise an error when accessing client
        client = apify_service.client
        assert client is not None
        
        # Invalid token should raise a ValueError when trying to access client
        apify_service._token = None
        apify_service._client = None
        with pytest.raises(ValueError):
            client = apify_service.client

    def test_run_actor(self, apify_service, mock_apify_client):
        """Test running an actor."""
        # Run the actor
        run_input = {"startUrls": [{"url": "https://example.com"}]}
        result = apify_service.run_actor("test_actor", run_input)
        
        # Verify the actor was called
        mock_apify_client.actor.assert_called_once_with("test_actor")
        mock_apify_client.actor().call.assert_called_once_with(run_input=run_input)
        
        # Verify result
        assert result["id"] == "test_run_id"
        assert result["status"] == "SUCCEEDED"

    def test_get_dataset_items(self, apify_service, mock_apify_client):
        """Test getting dataset items."""
        # Get dataset items
        items = apify_service.get_dataset_items("test_dataset_id")
        
        # Verify dataset was fetched
        mock_apify_client.dataset.assert_called_once_with("test_dataset_id")
        mock_apify_client.dataset().list_items.assert_called_once()  # Changed from get_items to list_items
        
        # Verify items
        assert "items" in items
        assert len(items["items"]) == 2
        assert items["items"][0]["url"] == "https://example.com/1"




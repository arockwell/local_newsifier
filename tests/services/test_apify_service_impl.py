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
        
        # Mock dataset method and get_items
        mock_dataset = MagicMock()
        mock_dataset.get_items.return_value = {
            "items": [
                {"url": "https://example.com/1", "title": "Test Article 1", "content": "Content 1"},
                {"url": "https://example.com/2", "title": "Test Article 2", "content": "Content 2"},
            ]
        }
        mock_client.dataset.return_value = mock_dataset
        
        # Mock run method and get_dataset_items
        mock_run = MagicMock()
        mock_run.get_dataset_items.return_value = mock_dataset.get_items.return_value
        mock_client.run.return_value = mock_run
        
        # Mock webhook method
        mock_webhook = MagicMock()
        mock_webhook.create.return_value = {"id": "webhook_id"}
        mock_client.webhooks.return_value = mock_webhook
        
        return mock_client

    @pytest.fixture
    def apify_service(self, db_session, mock_apify_client):
        """Create an ApifyService instance with mocked client."""
        with patch('local_newsifier.services.apify_service.ApifyClient', return_value=mock_apify_client):
            service = ApifyService(
                token="test_token",
                session_factory=lambda: db_session,
                source_config_crud=CRUDApifySourceConfig()
            )
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

    def test_initialize_client(self, apify_service):
        """Test client initialization."""
        # Client should already be initialized by the fixture
        client = apify_service.client
        assert client is not None
        
        # Reinitialize with different token
        apify_service._token = "new_token"
        apify_service._client = None
        client = apify_service.client
        assert client is not None

    def test_validate_token(self, apify_service):
        """Test token validation."""
        # Valid token should not raise an error
        apify_service.validate_token()
        
        # Invalid token should raise a ValueError
        apify_service._token = None
        with pytest.raises(ValueError):
            apify_service.validate_token()

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
        mock_apify_client.dataset().get_items.assert_called_once()
        
        # Verify items
        assert len(items) == 2
        assert items[0]["url"] == "https://example.com/1"

    def test_get_run_dataset_items(self, apify_service, mock_apify_client):
        """Test getting dataset items from a run."""
        # Get dataset items from run
        items = apify_service.get_run_dataset_items("test_run_id")
        
        # Verify run was fetched
        mock_apify_client.run.assert_called_once_with("test_run_id")
        mock_apify_client.run().get_dataset_items.assert_called_once()
        
        # Verify items
        assert len(items) == 2
        assert items[0]["url"] == "https://example.com/1"

    def test_create_source_config(self, apify_service, db_session):
        """Test creating a source config."""
        # Create config
        config_data = {
            "name": "New Test Source",
            "description": "New test description",
            "actor_id": "new_test_actor",
            "run_input": {
                "startUrls": [{"url": "https://example.com/new"}],
                "maxPages": 5
            },
            "is_active": True,
            "schedule_interval": 86400,  # daily
            "transform_script": "return item;"
        }
        
        config = apify_service.create_source_config(**config_data)
        
        # Verify config was created
        assert config.id is not None
        assert config.name == "New Test Source"
        
        # Verify config in database
        db_config = db_session.exec(
            select(ApifySourceConfig).where(ApifySourceConfig.id == config.id)
        ).first()
        assert db_config is not None
        assert db_config.name == "New Test Source"

    def test_run_source_config(self, apify_service, sample_source_config, mock_apify_client, db_session):
        """Test running a source config."""
        # Run the config
        run_result = apify_service.run_source_config(sample_source_config.id)
        
        # Verify actor was called with correct input
        mock_apify_client.actor.assert_called_with("test_actor")
        mock_apify_client.actor().call.assert_called_once()
        
        # Verify job was created
        jobs = db_session.exec(select(ApifyJob).where(ApifyJob.source_config_id == sample_source_config.id)).all()
        assert len(jobs) > 0
        
        # Verify config was updated
        db_session.refresh(sample_source_config)
        assert sample_source_config.last_run is not None
        
        # Verify result
        assert run_result["job_id"] is not None
        assert run_result["run_id"] == "test_run_id"
        assert run_result["status"] == "SUCCEEDED"

    def test_process_run_results(self, apify_service, sample_source_config, mock_apify_client, db_session):
        """Test processing run results."""
        # Create a job first
        job = ApifyJob(
            source_config_id=sample_source_config.id,
            run_id="test_run_id",
            status="SUCCEEDED",
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
            items_count=2
        )
        db_session.add(job)
        db_session.commit()
        db_session.refresh(job)
        
        # Process the run results
        result = apify_service.process_run_results(job.id)
        
        # Verify run data was fetched
        mock_apify_client.run.assert_called_with("test_run_id")
        
        # Verify dataset items
        items = db_session.exec(select(ApifyDatasetItem).where(ApifyDatasetItem.job_id == job.id)).all()
        assert len(items) > 0
        
        # Verify result
        assert result["processed_count"] == 2
        assert len(result["items"]) == 2

    def test_get_source_configs(self, apify_service, sample_source_config, db_session):
        """Test getting source configs."""
        # Get configs
        configs = apify_service.get_source_configs()
        
        # Verify configs
        assert len(configs) > 0
        assert configs[0].id == sample_source_config.id
        
        # Get specific config
        config = apify_service.get_source_config(sample_source_config.id)
        assert config.id == sample_source_config.id
        
        # Get with invalid ID
        with pytest.raises(ValueError):
            apify_service.get_source_config(999999)

    def test_update_source_config(self, apify_service, sample_source_config, db_session):
        """Test updating a source config."""
        # Update config
        updated_config = apify_service.update_source_config(
            config_id=sample_source_config.id,
            name="Updated Test Source",
            description="Updated description",
            is_active=False
        )
        
        # Verify config was updated
        assert updated_config.name == "Updated Test Source"
        assert updated_config.description == "Updated description"
        assert not updated_config.is_active
        
        # Verify in database
        db_session.refresh(sample_source_config)
        assert sample_source_config.name == "Updated Test Source"

    def test_create_webhook(self, apify_service, sample_source_config, mock_apify_client, db_session):
        """Test creating a webhook."""
        # Create webhook
        webhook = apify_service.create_webhook(
            source_config_id=sample_source_config.id,
            event_types=["ACTOR.RUN.SUCCEEDED"],
            callback_url="https://example.com/webhook"
        )
        
        # Verify webhook API was called
        mock_apify_client.webhooks.assert_called_once()
        mock_apify_client.webhooks().create.assert_called_once()
        
        # Verify webhook was created
        assert webhook["id"] == "webhook_id"
        
        # Verify source config was updated
        db_session.refresh(sample_source_config)
        assert sample_source_config.webhook_id == "webhook_id"

    def test_process_webhook_event(self, apify_service, sample_source_config, mock_apify_client, db_session):
        """Test processing a webhook event."""
        # Create test webhook data
        webhook_data = {
            "eventType": "ACTOR.RUN.SUCCEEDED",
            "createdAt": datetime.now(timezone.utc).isoformat(),
            "data": {
                "actorId": "test_actor",
                "actorRunId": "test_run_id",
                "defaultDatasetId": "test_dataset_id"
            }
        }
        
        # Create a webhook record
        webhook = ApifyWebhook(
            webhook_id="webhook_id",
            source_config_id=sample_source_config.id,
            event_types=["ACTOR.RUN.SUCCEEDED"],
            callback_url="https://example.com/webhook",
            payload_template="{}"
        )
        db_session.add(webhook)
        db_session.commit()
        db_session.refresh(webhook)
        
        # Process webhook event
        result = apify_service.process_webhook_event(webhook_data)
        
        # Verify job was created
        jobs = db_session.exec(select(ApifyJob).where(ApifyJob.run_id == "test_run_id")).all()
        assert len(jobs) > 0
        
        # Verify run data was fetched
        mock_apify_client.run.assert_called_with("test_run_id")
        
        # Verify result
        assert result["status"] == "success"
        assert "job_id" in result
"""Tests for the Apify schedule CLI commands."""

import json
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner
from sqlmodel import Session

from local_newsifier.cli.commands.apify import (_get_schedule_manager, create_schedule,
                                                delete_schedule, list_schedules, schedule_status,
                                                sync_schedules, update_schedule)
from local_newsifier.models.apify import ApifySourceConfig
from local_newsifier.services.apify_schedule_manager import ApifyScheduleManager


@pytest.fixture
def mock_schedule_manager():
    """Create a mock ApifyScheduleManager."""
    mock_manager = MagicMock(spec=ApifyScheduleManager)
    
    # Mock sync_schedules
    mock_manager.sync_schedules.return_value = {
        "created": 1,
        "updated": 2,
        "deleted": 0,
        "unchanged": 3,
        "errors": []
    }
    
    # Mock verify_schedule_status
    mock_manager.verify_schedule_status.return_value = {
        "exists": True,
        "synced": True,
        "config_details": {
            "name": "Test Config",
            "schedule": "0 0 * * *",
            "is_active": True,
            "schedule_id": "test_schedule_id"
        }
    }
    
    # Mock create_schedule_for_config
    mock_manager.create_schedule_for_config.return_value = True
    
    # Mock update_schedule_for_config
    mock_manager.update_schedule_for_config.return_value = True
    
    # Mock delete_schedule_for_config
    mock_manager.delete_schedule_for_config.return_value = True
    
    return mock_manager


@pytest.fixture
def mock_configs():
    """Create mock configs for testing."""
    class MockApifyConfig:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
        
        def model_dump(self):
            return {k: v for k, v in self.__dict__.items()}

    return [
        MockApifyConfig(
            id=1,
            name="Daily News Scraper",
            actor_id="actor1",
            schedule="0 0 * * *",
            schedule_id="sched1",
            is_active=True,
            last_run_at=datetime(2023, 1, 1, 12, 0, 0),
            source_type="web"
        ),
        MockApifyConfig(
            id=2,
            name="Weekly Blog Scraper",
            actor_id="actor2",
            schedule="0 0 * * 0",
            schedule_id="sched2",
            is_active=False,
            last_run_at=None,
            source_type="web"
        )
    ]


@pytest.fixture
def runner():
    """Create a CLI runner."""
    return CliRunner()


class TestApifyScheduleCommands:
    """Test the Apify schedule CLI commands."""

    @patch("local_newsifier.cli.commands.apify._get_schedule_manager")
    @patch("local_newsifier.cli.commands.apify._ensure_token")
    @patch("local_newsifier.cli.commands.apify.config_crud.get_scheduled_configs")
    @patch("local_newsifier.cli.commands.apify.get_session")
    def test_list_schedules(
        self, mock_get_session, mock_get_configs, mock_ensure_token,
        mock_get_schedule_manager, runner, mock_configs
    ):
        """Test the list schedules command."""
        # Setup
        mock_ensure_token.return_value = True
        mock_session = MagicMock(spec=Session)
        mock_get_session.return_value = mock_session
        mock_get_configs.return_value = mock_configs
        
        # Run the command
        result = runner.invoke(list_schedules)
        
        # Verify
        assert result.exit_code == 0
        assert "Daily News Scraper" in result.output
        assert "Weekly Blog Scraper" in result.output
        assert "0 0 * * *" in result.output
        assert "0 0 * * 0" in result.output
        assert "Active" in result.output
        assert "Inactive" in result.output
        
    @patch("local_newsifier.cli.commands.apify._get_schedule_manager")
    @patch("local_newsifier.cli.commands.apify._ensure_token")
    @patch("local_newsifier.cli.commands.apify.config_crud.get_scheduled_configs")
    @patch("local_newsifier.cli.commands.apify.get_session")
    def test_list_schedules_with_apify(
        self, mock_get_session, mock_get_configs, mock_ensure_token,
        mock_get_schedule_manager, runner, mock_configs, mock_schedule_manager
    ):
        """Test the list schedules command with Apify details."""
        # Setup
        mock_ensure_token.return_value = True
        mock_session = MagicMock(spec=Session)
        mock_get_session.return_value = mock_session
        mock_get_configs.return_value = mock_configs
        mock_get_schedule_manager.return_value = mock_schedule_manager
        
        # Run the command
        result = runner.invoke(list_schedules, ["--with-apify"])
        
        # Verify
        assert result.exit_code == 0
        assert "Daily News Scraper" in result.output
        assert "Weekly Blog Scraper" in result.output
        assert "Exists" in result.output
        assert "Synced" in result.output

    @patch("local_newsifier.cli.commands.apify._get_schedule_manager")
    @patch("local_newsifier.cli.commands.apify._ensure_token")
    @patch("local_newsifier.cli.commands.apify.config_crud.get_scheduled_configs")
    @patch("local_newsifier.cli.commands.apify.get_session")
    def test_list_schedules_json_format(
        self, mock_get_session, mock_get_configs, mock_ensure_token,
        mock_get_schedule_manager, runner, mock_configs
    ):
        """Test the list schedules command with JSON output."""
        # Setup
        mock_ensure_token.return_value = True
        mock_session = MagicMock(spec=Session)
        mock_get_session.return_value = mock_session
        
        # Use our mock configs directly
        mock_get_configs.return_value = mock_configs
        
        # Run the command
        result = runner.invoke(list_schedules, ["--format", "json"])
        
        # Verify basic success first
        assert result.exit_code == 0
        
        # For JSON tests, check that the output contains the expected strings
        assert "Daily News Scraper" in result.output
        assert "Weekly Blog Scraper" in result.output
        assert "0 0 * * *" in result.output
        assert "0 0 * * 0" in result.output

    @patch("local_newsifier.cli.commands.apify._get_schedule_manager")
    @patch("local_newsifier.cli.commands.apify._ensure_token")
    def test_sync_schedules(
        self, mock_ensure_token, mock_get_schedule_manager, 
        runner, mock_schedule_manager
    ):
        """Test the sync schedules command."""
        # Setup
        mock_ensure_token.return_value = True
        mock_get_schedule_manager.return_value = mock_schedule_manager
        
        # Run the command
        result = runner.invoke(sync_schedules)
        
        # Verify
        assert result.exit_code == 0
        assert "Synchronizing schedules with Apify" in result.output
        assert "Schedules synchronized successfully" in result.output
        assert "Created: 1" in result.output
        assert "Updated: 2" in result.output
        assert "Deleted: 0" in result.output
        assert "Unchanged: 3" in result.output
        mock_schedule_manager.sync_schedules.assert_called_once()

    @patch("local_newsifier.cli.commands.apify._get_schedule_manager")
    @patch("local_newsifier.cli.commands.apify._ensure_token")
    def test_create_schedule(
        self, mock_ensure_token, mock_get_schedule_manager, 
        runner, mock_schedule_manager
    ):
        """Test the create schedule command."""
        # Setup
        mock_ensure_token.return_value = True
        mock_get_schedule_manager.return_value = mock_schedule_manager
        
        # Run the command
        result = runner.invoke(create_schedule, ["1"])
        
        # Verify
        assert result.exit_code == 0
        assert "Creating schedule for config 1" in result.output
        assert "Schedule created successfully" in result.output
        mock_schedule_manager.create_schedule_for_config.assert_called_once_with(1)

    @patch("local_newsifier.cli.commands.apify._get_schedule_manager")
    @patch("local_newsifier.cli.commands.apify._ensure_token")
    def test_update_schedule(
        self, mock_ensure_token, mock_get_schedule_manager, 
        runner, mock_schedule_manager
    ):
        """Test the update schedule command."""
        # Setup
        mock_ensure_token.return_value = True
        mock_get_schedule_manager.return_value = mock_schedule_manager
        
        # Run the command
        result = runner.invoke(update_schedule, ["1"])
        
        # Verify
        assert result.exit_code == 0
        assert "Updating schedule for config 1" in result.output
        assert "Schedule updated successfully" in result.output
        mock_schedule_manager.update_schedule_for_config.assert_called_once_with(1)

    @patch("local_newsifier.cli.commands.apify._get_schedule_manager")
    @patch("local_newsifier.cli.commands.apify._ensure_token")
    def test_delete_schedule(
        self, mock_ensure_token, mock_get_schedule_manager, 
        runner, mock_schedule_manager
    ):
        """Test the delete schedule command."""
        # Setup
        mock_ensure_token.return_value = True
        mock_get_schedule_manager.return_value = mock_schedule_manager
        
        # Run the command
        result = runner.invoke(delete_schedule, ["1"])
        
        # Verify
        assert result.exit_code == 0
        assert "Deleting schedule for config 1" in result.output
        assert "Schedule deleted successfully" in result.output
        mock_schedule_manager.delete_schedule_for_config.assert_called_once_with(1)

    @patch("local_newsifier.cli.commands.apify._get_schedule_manager")
    @patch("local_newsifier.cli.commands.apify._ensure_token")
    def test_schedule_status(
        self, mock_ensure_token, mock_get_schedule_manager, 
        runner, mock_schedule_manager
    ):
        """Test the schedule status command."""
        # Setup
        mock_ensure_token.return_value = True
        mock_get_schedule_manager.return_value = mock_schedule_manager
        
        # Run the command
        result = runner.invoke(schedule_status, ["1"])
        
        # Verify
        assert result.exit_code == 0
        assert "Checking schedule status for config 1" in result.output
        assert "Schedule Status:" in result.output
        assert "Config ID: 1" in result.output
        assert "Name: Test Config" in result.output
        assert "Schedule: 0 0 * * *" in result.output
        assert "Schedule exists in Apify" in result.output
        assert "Schedule is in sync with config" in result.output
        mock_schedule_manager.verify_schedule_status.assert_called_once_with(1)

    @patch("local_newsifier.cli.commands.apify._get_schedule_manager")
    @patch("local_newsifier.cli.commands.apify._ensure_token")
    def test_schedule_status_not_synced(
        self, mock_ensure_token, mock_get_schedule_manager, 
        runner, mock_schedule_manager
    ):
        """Test the schedule status command with out of sync schedule."""
        # Setup
        mock_ensure_token.return_value = True
        mock_get_schedule_manager.return_value = mock_schedule_manager
        
        # Override the mock to return not synced
        mock_schedule_manager.verify_schedule_status.return_value = {
            "exists": True,
            "synced": False,
            "config_details": {
                "name": "Test Config",
                "schedule": "0 0 * * *",
                "is_active": True,
                "schedule_id": "test_schedule_id"
            }
        }
        
        # Run the command
        result = runner.invoke(schedule_status, ["1"])
        
        # Verify
        assert result.exit_code == 0
        assert "Schedule is out of sync with config" in result.output
        assert "Run 'nf apify schedules update CONFIG_ID' to synchronize" in result.output

    @patch("local_newsifier.cli.commands.apify._get_schedule_manager")
    @patch("local_newsifier.cli.commands.apify._ensure_token")
    def test_schedule_status_not_exists(
        self, mock_ensure_token, mock_get_schedule_manager, 
        runner, mock_schedule_manager
    ):
        """Test the schedule status command with non-existent schedule."""
        # Setup
        mock_ensure_token.return_value = True
        mock_get_schedule_manager.return_value = mock_schedule_manager
        
        # Override the mock to return not exists
        mock_schedule_manager.verify_schedule_status.return_value = {
            "exists": False,
            "synced": False,
            "config_details": {
                "name": "Test Config",
                "schedule": "0 0 * * *",
                "is_active": True,
                "schedule_id": "test_schedule_id"
            }
        }
        
        # Run the command
        result = runner.invoke(schedule_status, ["1"])
        
        # Verify
        assert result.exit_code == 0
        assert "Schedule does not exist in Apify" in result.output
        assert "Schedule ID exists in config but not in Apify" in result.output
        assert "Run 'nf apify schedules create CONFIG_ID' to create the schedule" in result.output

    def test_get_schedule_manager(self):
        """Test the _get_schedule_manager helper function."""
        # Use patch instead of calling directly to avoid actual dependencies
        with patch("local_newsifier.cli.commands.apify.ApifyService") as mock_apify_service, \
             patch("local_newsifier.cli.commands.apify.get_session") as mock_get_session, \
             patch("local_newsifier.cli.commands.apify.ApifyScheduleManager") as mock_manager_class:

            mock_get_session.return_value = MagicMock(spec=Session)
            
            # Call the function
            _get_schedule_manager("test_token")
            
            # Verify
            mock_apify_service.assert_called_once_with("test_token")
            mock_manager_class.assert_called_once()
            
            # Verify constructor args
            call_args = mock_manager_class.call_args[1]
            assert "apify_service" in call_args
            assert "apify_source_config_crud" in call_args
            assert "session_factory" in call_args
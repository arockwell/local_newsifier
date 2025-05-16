"""
Tests for Apify configuration CLI commands.

This module tests the CLI commands in apify_config.py for managing Apify source configurations.
"""

import json
import os
import io
import pytest
from unittest.mock import patch, MagicMock
from click.testing import CliRunner
from datetime import datetime

from local_newsifier.cli.commands.apify_config import (
    apify_config_group,
    list_configs,
    add_config,
    show_config,
    remove_config,
    update_config,
    run_config,
)


class TestApifyConfigCommands:
    """Tests for Apify configuration CLI commands."""
    
    @pytest.fixture
    def mock_apify_source_config_service(self):
        """Mock the ApifySourceConfigService."""
        with patch("local_newsifier.cli.commands.apify_config.get_apify_source_config_service") as mock_get_service:
            mock_service = MagicMock()
            mock_get_service.return_value = mock_service
            yield mock_service

    @pytest.fixture
    def sample_config(self):
        """Sample configuration for testing."""
        return {
            "id": 1,
            "name": "Test Config",
            "actor_id": "test/actor",
            "source_type": "test",
            "source_url": "https://example.com",
            "is_active": True,
            "schedule": "* * * * *",
            "input_configuration": {"url": "https://example.com", "max_pages": 5},
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "last_run_at": datetime.now().isoformat(),
            "schedule_id": "abc123"
        }

    @pytest.fixture
    def runner(self):
        """Click test runner."""
        return CliRunner()

    # List configs tests
    def test_list_configs_empty(self, runner, mock_apify_source_config_service):
        """Test listing configs when none exist."""
        mock_apify_source_config_service.list_configs.return_value = []
        
        result = runner.invoke(list_configs)
        
        assert result.exit_code == 0
        assert "No Apify source configurations found." in result.output
        mock_apify_source_config_service.list_configs.assert_called_once_with(
            skip=0, limit=100, active_only=False, source_type=None
        )

    def test_list_configs_with_data(self, runner, mock_apify_source_config_service, sample_config):
        """Test listing configs with data."""
        mock_apify_source_config_service.list_configs.return_value = [sample_config]
        
        result = runner.invoke(list_configs)
        
        assert result.exit_code == 0
        assert "Test Config" in result.output
        assert "test/actor" in result.output
        assert "test" in result.output

    def test_list_configs_json_output(self, runner, mock_apify_source_config_service, sample_config):
        """Test listing configs with JSON output."""
        mock_apify_source_config_service.list_configs.return_value = [sample_config]
        
        result = runner.invoke(list_configs, ["--json"])
        
        assert result.exit_code == 0
        # Verify that the output can be parsed as JSON
        data = json.loads(result.output)
        assert isinstance(data, list)
        assert data[0]["name"] == "Test Config"

    def test_list_configs_with_filters(self, runner, mock_apify_source_config_service):
        """Test listing configs with filters."""
        mock_apify_source_config_service.list_configs.return_value = []
        
        result = runner.invoke(list_configs, [
            "--active-only", 
            "--limit", "10", 
            "--skip", "5", 
            "--source-type", "news"
        ])
        
        assert result.exit_code == 0
        mock_apify_source_config_service.list_configs.assert_called_once_with(
            skip=5, limit=10, active_only=True, source_type="news"
        )

    # Add config tests
    def test_add_config_basic(self, runner, mock_apify_source_config_service, sample_config):
        """Test adding a basic configuration."""
        mock_apify_source_config_service.create_config.return_value = sample_config
        
        result = runner.invoke(add_config, [
            "--name", "Test Config",
            "--actor-id", "test/actor",
            "--source-type", "test"
        ])
        
        assert result.exit_code == 0
        assert "added successfully" in result.output
        mock_apify_source_config_service.create_config.assert_called_once_with(
            name="Test Config",
            actor_id="test/actor",
            source_type="test",
            source_url=None,
            schedule=None,
            input_configuration=None
        )

    def test_add_config_with_options(self, runner, mock_apify_source_config_service, sample_config):
        """Test adding a configuration with all options."""
        mock_apify_source_config_service.create_config.return_value = sample_config
        
        result = runner.invoke(add_config, [
            "--name", "Test Config",
            "--actor-id", "test/actor",
            "--source-type", "test",
            "--source-url", "https://example.com",
            "--schedule", "* * * * *",
            "--input", '{"url": "https://example.com", "max_pages": 5}'
        ])
        
        assert result.exit_code == 0
        assert "added successfully" in result.output
        mock_apify_source_config_service.create_config.assert_called_once()
        call_args = mock_apify_source_config_service.create_config.call_args[1]
        assert call_args["input_configuration"] == {"url": "https://example.com", "max_pages": 5}

    def test_add_config_with_input_file(self, runner, mock_apify_source_config_service, sample_config):
        """Test adding a configuration with input from a file."""
        mock_apify_source_config_service.create_config.return_value = sample_config
        
        try:
            # Create a temporary input file
            with open("test_input.json", "r") as f:
                input_config = json.load(f)
            
            result = runner.invoke(add_config, [
                "--name", "Test Config",
                "--actor-id", "test/actor",
                "--source-type", "test",
                "--input", "test_input.json"
            ])
            
            assert result.exit_code == 0
            assert "added successfully" in result.output
            mock_apify_source_config_service.create_config.assert_called_once()
            call_args = mock_apify_source_config_service.create_config.call_args[1]
            assert "input_configuration" in call_args
            assert call_args["input_configuration"] == input_config["input_configuration"]
            
        except FileNotFoundError:
            pytest.skip("Test file not found. Skipping test.")

    def test_add_config_invalid_json(self, runner, mock_apify_source_config_service):
        """Test adding a configuration with invalid JSON input."""
        result = runner.invoke(add_config, [
            "--name", "Test Config",
            "--actor-id", "test/actor",
            "--source-type", "test",
            "--input", '{"invalid: json'
        ])
        
        assert result.exit_code != 0
        assert "Error: Input must be valid JSON" in result.output
        mock_apify_source_config_service.create_config.assert_not_called()

    def test_add_config_error(self, runner, mock_apify_source_config_service):
        """Test adding a configuration with error."""
        mock_apify_source_config_service.create_config.side_effect = ValueError("Configuration already exists")
        
        result = runner.invoke(add_config, [
            "--name", "Test Config",
            "--actor-id", "test/actor",
            "--source-type", "test"
        ])
        
        assert result.exit_code != 0
        assert "Error adding configuration" in result.output

    # Show config tests
    def test_show_config(self, runner, mock_apify_source_config_service, sample_config):
        """Test showing a configuration."""
        mock_apify_source_config_service.get_config.return_value = sample_config
        
        result = runner.invoke(show_config, ["1"])
        
        assert result.exit_code == 0
        assert "Test Config" in result.output
        assert "test/actor" in result.output
        assert "https://example.com" in result.output
        mock_apify_source_config_service.get_config.assert_called_once_with(1)

    def test_show_config_json(self, runner, mock_apify_source_config_service, sample_config):
        """Test showing a configuration in JSON format."""
        mock_apify_source_config_service.get_config.return_value = sample_config
        
        result = runner.invoke(show_config, ["1", "--json"])
        
        assert result.exit_code == 0
        # Verify that the output can be parsed as JSON
        data = json.loads(result.output)
        assert data["name"] == "Test Config"
        assert data["actor_id"] == "test/actor"

    def test_show_config_not_found(self, runner, mock_apify_source_config_service):
        """Test showing a configuration that doesn't exist."""
        mock_apify_source_config_service.get_config.return_value = None
        
        result = runner.invoke(show_config, ["1"])
        
        assert result.exit_code != 0
        assert "not found" in result.output

    def test_show_config_error(self, runner, mock_apify_source_config_service):
        """Test showing a configuration with error."""
        mock_apify_source_config_service.get_config.side_effect = Exception("Database error")
        
        result = runner.invoke(show_config, ["1"])
        
        assert result.exit_code != 0
        assert "Error retrieving configuration" in result.output

    # Remove config tests
    def test_remove_config_confirmed(self, runner, mock_apify_source_config_service, sample_config):
        """Test removing a configuration with confirmation."""
        mock_apify_source_config_service.get_config.return_value = sample_config
        mock_apify_source_config_service.remove_config.return_value = True
        
        # Pass 'y' to the confirmation prompt
        result = runner.invoke(remove_config, ["1"], input="y\n")
        
        assert result.exit_code == 0
        assert "removed successfully" in result.output
        mock_apify_source_config_service.get_config.assert_called_once_with(1)
        mock_apify_source_config_service.remove_config.assert_called_once_with(1)

    def test_remove_config_cancelled(self, runner, mock_apify_source_config_service, sample_config):
        """Test canceling a configuration removal."""
        mock_apify_source_config_service.get_config.return_value = sample_config
        
        # Pass 'n' to the confirmation prompt
        result = runner.invoke(remove_config, ["1"], input="n\n")
        
        assert result.exit_code == 0
        assert "Operation canceled" in result.output
        mock_apify_source_config_service.remove_config.assert_not_called()

    def test_remove_config_force(self, runner, mock_apify_source_config_service, sample_config):
        """Test removing a configuration with force option."""
        mock_apify_source_config_service.get_config.return_value = sample_config
        mock_apify_source_config_service.remove_config.return_value = True
        
        result = runner.invoke(remove_config, ["1", "--force"])
        
        assert result.exit_code == 0
        assert "removed successfully" in result.output
        # Should not prompt for confirmation
        assert "Are you sure" not in result.output
        mock_apify_source_config_service.remove_config.assert_called_once_with(1)

    def test_remove_config_not_found(self, runner, mock_apify_source_config_service):
        """Test removing a configuration that doesn't exist."""
        mock_apify_source_config_service.get_config.return_value = None
        
        result = runner.invoke(remove_config, ["1"])
        
        assert result.exit_code != 0
        assert "not found" in result.output
        mock_apify_source_config_service.remove_config.assert_not_called()

    def test_remove_config_error(self, runner, mock_apify_source_config_service, sample_config):
        """Test removing a configuration with error."""
        mock_apify_source_config_service.get_config.return_value = sample_config
        mock_apify_source_config_service.remove_config.side_effect = Exception("Database error")
        
        result = runner.invoke(remove_config, ["1", "--force"])
        
        assert result.exit_code != 0
        assert "Error removing configuration" in result.output

    # Update config tests
    def test_update_config_name(self, runner, mock_apify_source_config_service, sample_config):
        """Test updating a configuration's name."""
        updated_config = sample_config.copy()
        updated_config["name"] = "Updated Name"
        mock_apify_source_config_service.update_config.return_value = updated_config
        
        result = runner.invoke(update_config, ["1", "--name", "Updated Name"])
        
        assert result.exit_code == 0
        assert "updated successfully" in result.output
        mock_apify_source_config_service.update_config.assert_called_once_with(
            config_id=1,
            name="Updated Name",
            actor_id=None,
            source_type=None,
            source_url=None,
            schedule=None,
            is_active=None,
            input_configuration=None
        )

    def test_update_config_multiple_properties(self, runner, mock_apify_source_config_service, sample_config):
        """Test updating multiple properties of a configuration."""
        mock_apify_source_config_service.update_config.return_value = sample_config
        
        result = runner.invoke(update_config, [
            "1",
            "--name", "Updated Name",
            "--actor-id", "updated/actor",
            "--active"
        ])
        
        assert result.exit_code == 0
        assert "updated successfully" in result.output
        mock_apify_source_config_service.update_config.assert_called_once()
        call_args = mock_apify_source_config_service.update_config.call_args[1]
        assert call_args["name"] == "Updated Name"
        assert call_args["actor_id"] == "updated/actor"
        assert call_args["is_active"] is True

    def test_update_config_input_json(self, runner, mock_apify_source_config_service, sample_config):
        """Test updating a configuration's input with JSON."""
        mock_apify_source_config_service.update_config.return_value = sample_config
        
        result = runner.invoke(update_config, [
            "1",
            "--input", '{"url": "https://new-example.com", "max_pages": 10}'
        ])
        
        assert result.exit_code == 0
        assert "updated successfully" in result.output
        mock_apify_source_config_service.update_config.assert_called_once()
        call_args = mock_apify_source_config_service.update_config.call_args[1]
        assert call_args["input_configuration"] == {"url": "https://new-example.com", "max_pages": 10}

    def test_update_config_input_file(self, runner, mock_apify_source_config_service, sample_config):
        """Test updating a configuration's input from a file."""
        mock_apify_source_config_service.update_config.return_value = sample_config
        
        try:
            # Use the existing test input file
            with open("test_input.json", "r") as f:
                input_config = json.load(f)
            
            result = runner.invoke(update_config, [
                "1",
                "--input", "test_input.json"
            ])
            
            assert result.exit_code == 0
            assert "updated successfully" in result.output
            mock_apify_source_config_service.update_config.assert_called_once()
            call_args = mock_apify_source_config_service.update_config.call_args[1]
            assert "input_configuration" in call_args
            assert call_args["input_configuration"] == input_config["input_configuration"]
            
        except FileNotFoundError:
            pytest.skip("Test file not found. Skipping test.")

    def test_update_config_invalid_json(self, runner, mock_apify_source_config_service):
        """Test updating a configuration with invalid JSON input."""
        result = runner.invoke(update_config, [
            "1",
            "--input", '{"invalid: json'
        ])
        
        assert result.exit_code != 0
        assert "Error: Input must be valid JSON" in result.output
        mock_apify_source_config_service.update_config.assert_not_called()

    def test_update_config_no_properties(self, runner, mock_apify_source_config_service):
        """Test updating a configuration without specifying any properties."""
        result = runner.invoke(update_config, ["1"])
        
        assert result.exit_code == 0
        assert "No properties specified for update" in result.output
        mock_apify_source_config_service.update_config.assert_not_called()

    def test_update_config_not_found(self, runner, mock_apify_source_config_service):
        """Test updating a configuration that doesn't exist."""
        mock_apify_source_config_service.update_config.return_value = None
        
        result = runner.invoke(update_config, ["1", "--name", "Updated Name"])
        
        assert result.exit_code != 0
        assert "not found" in result.output

    def test_update_config_error(self, runner, mock_apify_source_config_service):
        """Test updating a configuration with error."""
        mock_apify_source_config_service.update_config.side_effect = Exception("Database error")
        
        result = runner.invoke(update_config, ["1", "--name", "Updated Name"])
        
        assert result.exit_code != 0
        assert "Error updating configuration" in result.output

    # Run config tests
    def test_run_config_success(self, runner, mock_apify_source_config_service):
        """Test running a configuration successfully."""
        mock_apify_source_config_service.run_configuration.return_value = {
            "status": "success",
            "config_id": 1,
            "config_name": "Test Config",
            "actor_id": "test/actor",
            "run_id": "run123",
            "dataset_id": "dataset123"
        }
        
        result = runner.invoke(run_config, ["1"])
        
        assert result.exit_code == 0
        assert "Actor run completed successfully" in result.output
        assert "Test Config" in result.output
        assert "run123" in result.output
        assert "dataset123" in result.output
        mock_apify_source_config_service.run_configuration.assert_called_once_with(1)

    def test_run_config_with_output(self, runner, mock_apify_source_config_service, tmp_path):
        """Test running a configuration with output to file."""
        mock_apify_source_config_service.run_configuration.return_value = {
            "status": "success",
            "config_id": 1,
            "config_name": "Test Config",
            "actor_id": "test/actor",
            "run_id": "run123",
            "dataset_id": "dataset123"
        }
        
        output_file = tmp_path / "output.json"
        
        with runner.isolated_filesystem():
            result = runner.invoke(run_config, ["1", "--output", str(output_file)])
            
            assert result.exit_code == 0
            assert "Actor run completed successfully" in result.output
            assert f"Output saved to {output_file}" in result.output
            
            # Verify the file was created with the expected content
            assert os.path.exists(output_file)
            with open(output_file, "r") as f:
                data = json.load(f)
                assert data["status"] == "success"
                assert data["config_id"] == 1
                assert data["run_id"] == "run123"

    def test_run_config_failure(self, runner, mock_apify_source_config_service):
        """Test running a configuration with failure."""
        mock_apify_source_config_service.run_configuration.return_value = {
            "status": "error",
            "message": "Actor run failed"
        }
        
        result = runner.invoke(run_config, ["1"])
        
        assert result.exit_code != 0
        assert "Actor run failed" in result.output

    def test_run_config_error(self, runner, mock_apify_source_config_service):
        """Test running a configuration with error."""
        mock_apify_source_config_service.run_configuration.side_effect = Exception("API error")
        
        result = runner.invoke(run_config, ["1"])
        
        assert result.exit_code != 0
        assert "Error running configuration" in result.output
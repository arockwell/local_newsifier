"""Tests for the Apify CLI commands."""

import os
import json
import tempfile
from unittest.mock import patch, MagicMock

import pytest
from click.testing import CliRunner

from local_newsifier.cli.commands.apify import (
    apify_group, _ensure_token, test_connection,
    run_actor, get_dataset, get_actor, scrape_content
)
from local_newsifier.config.settings import settings
from local_newsifier.services.apify_service import ApifyService


@pytest.fixture
def mock_apify_service():
    """Create a mock ApifyService."""
    mock_service = MagicMock(spec=ApifyService)
    
    # Mock client property
    mock_client = MagicMock()
    type(mock_service).client = mock_client
    
    # Mock user info
    mock_client.user().get.return_value = {"username": "test_user"}
    
    # Mock actor run
    mock_service.run_actor.return_value = {
        "id": "test_run",
        "status": "SUCCEEDED",
        "defaultDatasetId": "test_dataset"
    }
    
    # Mock dataset items
    mock_service.get_dataset_items.return_value = {
        "items": [{"id": 1, "title": "Test Article", "url": "https://example.com"}]
    }
    
    # Mock actor details
    mock_service.get_actor_details.return_value = {
        "id": "test_actor",
        "name": "Test Actor",
        "title": "Test Actor Title",
        "description": "Test actor description",
        "version": {"versionNumber": "1.0.0"},
        "defaultRunInput": {"field1": "value1"}
    }
    
    return mock_service


@pytest.fixture
def runner():
    """Create a CLI runner."""
    return CliRunner()


@pytest.fixture
def original_token():
    """Store and restore the original token."""
    original = os.environ.get("APIFY_TOKEN")
    original_settings = settings.APIFY_TOKEN
    
    yield
    
    # Restore the original token
    if original:
        os.environ["APIFY_TOKEN"] = original
    elif "APIFY_TOKEN" in os.environ:
        del os.environ["APIFY_TOKEN"]
        
    settings.APIFY_TOKEN = original_settings


class TestApifyCommands:
    """Test the Apify CLI commands."""
    
    def test_ensure_token_with_env_var(self, original_token):
        """Test ensuring the token with the env var."""
        os.environ["APIFY_TOKEN"] = "test_token"
        assert _ensure_token() is True
        assert settings.APIFY_TOKEN == "test_token"
    
    def test_ensure_token_with_settings(self, original_token):
        """Test ensuring the token with settings."""
        if "APIFY_TOKEN" in os.environ:
            del os.environ["APIFY_TOKEN"]
        settings.APIFY_TOKEN = "settings_token"
        assert _ensure_token() is True
        
    def test_ensure_token_missing(self, runner, original_token):
        """Test ensuring the token when it's missing."""
        if "APIFY_TOKEN" in os.environ:
            del os.environ["APIFY_TOKEN"]
        settings.APIFY_TOKEN = None
        assert _ensure_token() is False
    
    @patch("local_newsifier.cli.commands.apify.ApifyService")
    def test_test_connection(self, mock_service_class, mock_apify_service, runner, original_token):
        """Test the test connection command."""
        # Setup
        mock_service_class.return_value = mock_apify_service
        os.environ["APIFY_TOKEN"] = "test_token"
        
        # Run the command
        result = runner.invoke(test_connection)
        
        # Verify
        assert result.exit_code == 0
        assert "Connection to Apify API successful" in result.output
        assert "Connected as: test_user" in result.output
    
    @patch("local_newsifier.cli.commands.apify.ApifyService")
    def test_test_connection_with_token_param(self, mock_service_class, mock_apify_service, runner, original_token):
        """Test the test connection command with token parameter."""
        # Setup
        mock_service_class.return_value = mock_apify_service
        
        # Run the command
        result = runner.invoke(test_connection, ["--token", "param_token"])
        
        # Verify
        assert result.exit_code == 0
        assert "Connection to Apify API successful" in result.output
        mock_service_class.assert_called_once_with("param_token")
    
    @patch("local_newsifier.cli.commands.apify.ApifyService")
    def test_run_actor(self, mock_service_class, mock_apify_service, runner, original_token):
        """Test the run actor command."""
        # Setup
        mock_service_class.return_value = mock_apify_service
        os.environ["APIFY_TOKEN"] = "test_token"
        
        # Run the command
        result = runner.invoke(run_actor, ["test_actor", "--input", '{"param":"value"}'])
        
        # Verify
        assert result.exit_code == 0
        assert "Running actor test_actor" in result.output
        assert "Actor run completed" in result.output
        assert "Default dataset ID: test_dataset" in result.output
        mock_apify_service.run_actor.assert_called_once_with("test_actor", {"param": "value"})
    
    @patch("local_newsifier.cli.commands.apify.ApifyService")
    def test_run_actor_with_input_file(self, mock_service_class, mock_apify_service, runner, original_token):
        """Test the run actor command with input file."""
        # Setup
        mock_service_class.return_value = mock_apify_service
        os.environ["APIFY_TOKEN"] = "test_token"
        
        # Create a temporary file with input
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            json.dump({"param": "file_value"}, f)
            input_file = f.name
        
        try:
            # Run the command
            result = runner.invoke(run_actor, ["test_actor", "--input", input_file])
            
            # Verify
            assert result.exit_code == 0
            assert "Loaded input from file" in result.output
            assert "Running actor test_actor" in result.output
            mock_apify_service.run_actor.assert_called_once_with("test_actor", {"param": "file_value"})
        finally:
            # Clean up
            os.unlink(input_file)
    
    @patch("local_newsifier.cli.commands.apify.ApifyService")
    def test_run_actor_with_output_file(self, mock_service_class, mock_apify_service, runner, original_token):
        """Test the run actor command with output to file."""
        # Setup
        mock_service_class.return_value = mock_apify_service
        os.environ["APIFY_TOKEN"] = "test_token"
        
        with tempfile.NamedTemporaryFile(delete=False) as f:
            output_file = f.name
        
        try:
            # Run the command
            result = runner.invoke(run_actor, [
                "test_actor", 
                "--input", '{"param":"value"}',
                "--output", output_file
            ])
            
            # Verify
            assert result.exit_code == 0
            assert f"Output saved to {output_file}" in result.output
            
            # Check the output file contents
            with open(output_file, 'r') as f:
                output_content = json.load(f)
                assert output_content["id"] == "test_run"
        finally:
            # Clean up
            os.unlink(output_file)
    
    @patch("local_newsifier.cli.commands.apify.ApifyService")
    def test_get_dataset(self, mock_service_class, mock_apify_service, runner, original_token):
        """Test the get dataset command."""
        # Setup
        mock_service_class.return_value = mock_apify_service
        os.environ["APIFY_TOKEN"] = "test_token"
        
        # Run the command
        result = runner.invoke(get_dataset, ["test_dataset"])
        
        # Verify
        assert result.exit_code == 0
        assert "Retrieving items from dataset test_dataset" in result.output
        assert "Retrieved 1 items" in result.output
        mock_apify_service.get_dataset_items.assert_called_once_with("test_dataset", limit=10, offset=0)
    
    @patch("local_newsifier.cli.commands.apify.ApifyService")
    def test_get_dataset_with_table_format(self, mock_service_class, mock_apify_service, runner, original_token):
        """Test the get dataset command with table format."""
        # Setup
        mock_service_class.return_value = mock_apify_service
        os.environ["APIFY_TOKEN"] = "test_token"
        
        # Run the command
        result = runner.invoke(get_dataset, ["test_dataset", "--format", "table"])
        
        # Verify
        assert result.exit_code == 0
        assert "Retrieving items from dataset test_dataset" in result.output
        assert "Retrieved 1 items" in result.output
        # Table output should have headers - lowercase column names
        assert "title" in result.output
        
    @patch("local_newsifier.cli.commands.apify.ApifyService")
    def test_get_actor(self, mock_service_class, mock_apify_service, runner, original_token):
        """Test the get actor command."""
        # Setup
        mock_service_class.return_value = mock_apify_service
        os.environ["APIFY_TOKEN"] = "test_token"
        
        # Run the command
        result = runner.invoke(get_actor, ["test_actor"])
        
        # Verify
        assert result.exit_code == 0
        assert "Retrieving details for actor test_actor" in result.output
        assert "Actor details retrieved" in result.output
        assert "Name: Test Actor" in result.output
        assert "Description: Test actor description" in result.output
        assert "Input Schema" in result.output
        mock_apify_service.get_actor_details.assert_called_once_with("test_actor")
    
    @patch("local_newsifier.cli.commands.apify.ApifyService")
    def test_scrape_content(self, mock_service_class, mock_apify_service, runner, original_token):
        """Test the scrape content command."""
        # Setup
        mock_service_class.return_value = mock_apify_service
        os.environ["APIFY_TOKEN"] = "test_token"
        
        # Run the command
        result = runner.invoke(scrape_content, ["https://example.com"])
        
        # Verify
        assert result.exit_code == 0
        assert "Scraping content from https://example.com" in result.output
        assert "Using max pages: 5, max depth: 1" in result.output
        assert "Scraping complete!" in result.output
        assert "Retrieved 1 pages of content" in result.output
        
        # Check the actor input
        expected_input = {
            "startUrls": [{"url": "https://example.com"}],
            "maxCrawlPages": 5,
            "maxCrawlDepth": 1,
            "maxPagesPerCrawl": 5
        }
        mock_apify_service.run_actor.assert_called_once_with("apify/website-content-crawler", expected_input)
        
    @patch("local_newsifier.cli.commands.apify.ApifyService")
    def test_scrape_content_with_output(self, mock_service_class, mock_apify_service, runner, original_token):
        """Test the scrape content command with output to file."""
        # Setup
        mock_service_class.return_value = mock_apify_service
        os.environ["APIFY_TOKEN"] = "test_token"
        
        with tempfile.NamedTemporaryFile(delete=False) as f:
            output_file = f.name
        
        try:
            # Run the command
            result = runner.invoke(scrape_content, [
                "https://example.com",
                "--output", output_file
            ])
            
            # Verify
            assert result.exit_code == 0
            assert f"Output saved to {output_file}" in result.output
            
            # Check the output file contents
            with open(output_file, 'r') as f:
                output_content = json.load(f)
                assert len(output_content) == 1
                assert output_content[0]["id"] == 1
        finally:
            # Clean up
            os.unlink(output_file)

"""Tests for the improved Apify CLI commands with proper dependency injection."""

import json
import os
import tempfile
import io
from unittest.mock import MagicMock, patch
from contextlib import redirect_stdout

import pytest
from click.testing import CliRunner

from local_newsifier.cli.commands.apify import (ApifyCommands, apify_group,
                                                test_connection, get_actor,
                                                get_dataset, run_actor,
                                                scrape_content, web_scraper)
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
        "defaultDatasetId": "test_dataset",
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
        "defaultRunInput": {"field1": "value1"},
    }

    return mock_service


@pytest.fixture
def mock_apify_commands(mock_apify_service):
    """Create a mock ApifyCommands instance with injected test doubles."""
    return ApifyCommands(apify_service=mock_apify_service)


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
    """Test the Apify commands class with direct method calls."""

    def test_ensure_token_with_env_var(self, mock_apify_commands, original_token):
        """Test ensuring the token with the env var."""
        os.environ["APIFY_TOKEN"] = "test_token"
        assert mock_apify_commands._ensure_token() is True
        assert settings.APIFY_TOKEN == "test_token"

    def test_ensure_token_with_settings(self, mock_apify_commands, original_token):
        """Test ensuring the token with settings."""
        if "APIFY_TOKEN" in os.environ:
            del os.environ["APIFY_TOKEN"]
        settings.APIFY_TOKEN = "settings_token"
        assert mock_apify_commands._ensure_token() is True

    def test_ensure_token_missing(self, mock_apify_commands, original_token):
        """Test ensuring the token when it's missing."""
        if "APIFY_TOKEN" in os.environ:
            del os.environ["APIFY_TOKEN"]
        settings.APIFY_TOKEN = None
        # Capture stdout to avoid polluting the test output
        f = io.StringIO()
        with redirect_stdout(f):
            assert mock_apify_commands._ensure_token() is False

    def test_test_connection(self, mock_apify_commands, original_token):
        """Test the test_connection method directly."""
        # Setup
        os.environ["APIFY_TOKEN"] = "test_token"
        
        # Capture stdout
        f = io.StringIO()
        with redirect_stdout(f):
            # Call the method directly
            mock_apify_commands.test_connection()
        
        output = f.getvalue()
        
        # Verify output
        assert "Connection to Apify API successful" in output
        assert "Connected as: test_user" in output

    def test_test_connection_with_token_param(self, mock_apify_commands, original_token):
        """Test the test_connection method with token parameter."""
        # Capture stdout
        f = io.StringIO()
        with redirect_stdout(f):
            # Call the method directly with token
            mock_apify_commands.test_connection(token="param_token")
        
        output = f.getvalue()
        
        # Verify output
        assert "Connection to Apify API successful" in output

    def test_run_actor(self, mock_apify_commands, original_token):
        """Test the run_actor method directly."""
        # Setup
        os.environ["APIFY_TOKEN"] = "test_token"
        
        # Capture stdout
        f = io.StringIO()
        with redirect_stdout(f):
            # Call the method directly
            mock_apify_commands.run_actor(
                actor_id="test_actor", 
                input_data='{"param":"value"}',
                wait=True
            )
        
        output = f.getvalue()
        
        # Verify output
        assert "Running actor test_actor" in output
        assert "Actor run completed" in output
        assert "Default dataset ID: test_dataset" in output
        
        # Verify method calls
        mock_apify_commands.apify_service.run_actor.assert_called_once_with(
            "test_actor", {"param": "value"}
        )

    def test_run_actor_with_input_file(self, mock_apify_commands, original_token):
        """Test the run_actor method with input file."""
        # Setup
        os.environ["APIFY_TOKEN"] = "test_token"

        # Create a temporary file with input
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            json.dump({"param": "file_value"}, f)
            input_file = f.name

        try:
            # Capture stdout
            f = io.StringIO()
            with redirect_stdout(f):
                # Call the method directly
                mock_apify_commands.run_actor(
                    actor_id="test_actor", 
                    input_data=input_file
                )
            
            output = f.getvalue()
            
            # Verify output
            assert "Loaded input from file" in output
            assert "Running actor test_actor" in output
            
            # Verify method calls
            mock_apify_commands.apify_service.run_actor.assert_called_once_with(
                "test_actor", {"param": "file_value"}
            )
        finally:
            # Clean up
            os.unlink(input_file)

    def test_run_actor_with_output_file(self, mock_apify_commands, original_token):
        """Test the run_actor method with output to file."""
        # Setup
        os.environ["APIFY_TOKEN"] = "test_token"

        with tempfile.NamedTemporaryFile(delete=False) as f:
            output_file = f.name

        try:
            # Capture stdout
            f = io.StringIO()
            with redirect_stdout(f):
                # Call the method directly
                mock_apify_commands.run_actor(
                    actor_id="test_actor", 
                    input_data='{"param":"value"}', 
                    output=output_file
                )
            
            output = f.getvalue()
            
            # Verify output
            assert f"Output saved to {output_file}" in output

            # Check the output file contents
            with open(output_file, "r") as f:
                output_content = json.load(f)
                assert output_content["id"] == "test_run"
        finally:
            # Clean up
            os.unlink(output_file)

    def test_get_dataset(self, mock_apify_commands, original_token):
        """Test the get_dataset method directly."""
        # Setup
        os.environ["APIFY_TOKEN"] = "test_token"
        
        # Capture stdout
        f = io.StringIO()
        with redirect_stdout(f):
            # Call the method directly
            mock_apify_commands.get_dataset("test_dataset")
        
        output = f.getvalue()
        
        # Verify output
        assert "Retrieving items from dataset test_dataset" in output
        assert "Retrieved 1 items" in output
        
        # Verify method calls
        mock_apify_commands.apify_service.get_dataset_items.assert_called_once_with(
            "test_dataset", limit=10, offset=0
        )

    def test_get_dataset_with_table_format(self, mock_apify_commands, original_token):
        """Test the get_dataset method with table format."""
        # Setup
        os.environ["APIFY_TOKEN"] = "test_token"
        
        # Capture stdout
        f = io.StringIO()
        with redirect_stdout(f):
            # Call the method directly
            mock_apify_commands.get_dataset(
                dataset_id="test_dataset",
                format_type="table"
            )
        
        output = f.getvalue()
        
        # Verify output
        assert "Retrieving items from dataset test_dataset" in output
        assert "Retrieved 1 items" in output
        # Table output requires tabulate so just verify key aspects
        assert "title" in output.lower() or "id" in output.lower()

    def test_get_actor(self, mock_apify_commands, original_token):
        """Test the get_actor method directly."""
        # Setup
        os.environ["APIFY_TOKEN"] = "test_token"
        
        # Capture stdout
        f = io.StringIO()
        with redirect_stdout(f):
            # Call the method directly
            mock_apify_commands.get_actor("test_actor")
        
        output = f.getvalue()
        
        # Verify output
        assert "Retrieving details for actor test_actor" in output
        assert "Actor details retrieved" in output
        assert "Name: Test Actor" in output
        assert "Description: Test actor description" in output
        assert "Input Schema" in output
        
        # Verify method calls
        mock_apify_commands.apify_service.get_actor_details.assert_called_once_with("test_actor")

    def test_scrape_content(self, mock_apify_commands, original_token):
        """Test the scrape_content method directly."""
        # Setup
        os.environ["APIFY_TOKEN"] = "test_token"
        
        # Capture stdout
        f = io.StringIO()
        with redirect_stdout(f):
            # Call the method directly
            mock_apify_commands.scrape_content("https://example.com")
        
        output = f.getvalue()
        
        # Verify output
        assert "Scraping content from https://example.com" in output
        assert "Using max pages: 5, max depth: 1" in output
        assert "Scraping complete!" in output
        assert "Retrieved 1 pages of content" in output
        
        # Check the actor input
        expected_input = {
            "startUrls": [{"url": "https://example.com"}],
            "maxCrawlPages": 5,
            "maxCrawlDepth": 1,
            "maxPagesPerCrawl": 5,
        }
        mock_apify_commands.apify_service.run_actor.assert_called_once_with(
            "apify/website-content-crawler", expected_input
        )

    def test_scrape_content_with_output(self, mock_apify_commands, original_token):
        """Test the scrape_content method with output to file."""
        # Setup
        os.environ["APIFY_TOKEN"] = "test_token"

        with tempfile.NamedTemporaryFile(delete=False) as f:
            output_file = f.name

        try:
            # Capture stdout
            f = io.StringIO()
            with redirect_stdout(f):
                # Call the method directly
                mock_apify_commands.scrape_content(
                    url="https://example.com", 
                    output=output_file
                )
            
            output = f.getvalue()
            
            # Verify output
            assert f"Output saved to {output_file}" in output

            # Check the output file contents
            with open(output_file, "r") as f:
                output_content = json.load(f)
                assert len(output_content) == 1
                assert output_content[0]["id"] == 1
        finally:
            # Clean up
            os.unlink(output_file)

    def test_web_scraper(self, mock_apify_commands, original_token):
        """Test the web_scraper method directly."""
        # Setup
        os.environ["APIFY_TOKEN"] = "test_token"
        
        # Capture stdout
        f = io.StringIO()
        with redirect_stdout(f):
            # Call the method directly
            mock_apify_commands.web_scraper("https://example.com")
        
        output = f.getvalue()
        
        # Verify output
        assert "Scraping website from https://example.com" in output
        assert "Using selector: a, max pages: 5" in output
        assert "Retrieved 1 pages of data" in output
        
        # Check the correct actor was called with required fields
        mock_apify_commands.apify_service.run_actor.assert_called_once()
        call_args = mock_apify_commands.apify_service.run_actor.call_args[0]
        assert call_args[0] == "apify/web-scraper"
        assert "startUrls" in call_args[1]
        assert "linkSelector" in call_args[1]
        assert "pageFunction" in call_args[1]
        assert "maxPagesPerCrawl" in call_args[1]

    def test_web_scraper_with_options(self, mock_apify_commands, original_token):
        """Test the web_scraper method with custom options."""
        # Setup
        os.environ["APIFY_TOKEN"] = "test_token"
        
        # Custom page function
        custom_page_function = "async function pageFunction(context) { return {custom: true}; }"
        
        # Capture stdout
        f = io.StringIO()
        with redirect_stdout(f):
            # Call the method directly with options
            mock_apify_commands.web_scraper(
                url="https://example.com",
                selector="article a",
                max_pages=10,
                wait_for="#content",
                page_function=custom_page_function
            )
        
        output = f.getvalue()
        
        # Verify output
        assert "Scraping website from https://example.com" in output
        assert "Using selector: article a, max pages: 10" in output
        
        # Check the correct options were passed
        mock_apify_commands.apify_service.run_actor.assert_called_once()
        call_args = mock_apify_commands.apify_service.run_actor.call_args[0]
        input_config = call_args[1]
        assert input_config["startUrls"][0]["url"] == "https://example.com"
        assert input_config["linkSelector"] == "article a"
        assert input_config["maxPagesPerCrawl"] == 10
        assert input_config["waitFor"] == "#content"
        assert custom_page_function in input_config["pageFunction"]

    def test_web_scraper_with_output(self, mock_apify_commands, original_token):
        """Test the web_scraper method with output to file."""
        # Setup
        os.environ["APIFY_TOKEN"] = "test_token"

        with tempfile.NamedTemporaryFile(delete=False) as f:
            output_file = f.name

        try:
            # Capture stdout
            f = io.StringIO()
            with redirect_stdout(f):
                # Call the method directly
                mock_apify_commands.web_scraper(
                    url="https://example.com",
                    output=output_file
                )
            
            output = f.getvalue()
            
            # Verify output
            assert f"Output saved to {output_file}" in output

            # Check the output file contents
            with open(output_file, "r") as f:
                output_content = json.load(f)
                assert len(output_content) == 1
                assert output_content[0]["id"] == 1
        finally:
            # Clean up
            os.unlink(output_file)

"""Tests for the Apify CLI commands."""

import json
import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from local_newsifier.cli.commands.apify import (_ensure_token, _get_apify_client,
                                                get_actor, get_dataset, run_actor,
                                                scrape_content, test_connection, 
                                                web_scraper)
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


# This test has been moved to test_injectable_cli.py
# We're commenting it out here to avoid duplicate tests
# @patch('local_newsifier.di.providers.get_apify_client')
# def test_get_apify_client_with_injectable(mock_get_injectable_client):
#     """Test the _get_apify_client helper function with injectable client."""
#     # Set up mock injectable client
#     mock_client = MagicMock()
#     mock_get_injectable_client.return_value = mock_client
#     
#     # Call the helper function
#     client = _get_apify_client(token="test_token")
#     
#     # Verify the injectable client was used
#     assert client == mock_client
#     mock_get_injectable_client.assert_called_once_with(token="test_token")


# This test has been moved to test_injectable_cli.py
# We're commenting it out here to avoid duplicate tests
# @patch('local_newsifier.di.providers.get_apify_client', side_effect=ImportError)
# @patch('local_newsifier.services.apify_service.ApifyService')
# def test_get_apify_client_fallback(mock_apify_service, mock_get_injectable_client):
#     """Test the _get_apify_client helper function with fallback."""
#     # Set up mock service and client
#     mock_service = MagicMock()
#     mock_client = MagicMock()
#     mock_service.client = mock_client
#     mock_apify_service.return_value = mock_service
#     
#     # Call the helper function
#     client = _get_apify_client(token="test_token")
#     
#     # Verify fallback was used
#     assert client == mock_client
#     mock_get_injectable_client.assert_called_once()
#     mock_apify_service.assert_called_once_with("test_token")


# This test has been moved to test_injectable_cli.py
# We're commenting it out here to avoid duplicate tests
# @patch('local_newsifier.di.providers.get_apify_client', side_effect=Exception("Test error"))
# @patch('local_newsifier.services.apify_service.ApifyService')
# def test_get_apify_client_error_fallback(mock_apify_service, mock_get_injectable_client):
#     """Test the _get_apify_client helper function handles errors and falls back."""
#     # Set up mock service and client
#     mock_service = MagicMock()
#     mock_client = MagicMock()
#     mock_service.client = mock_client
#     mock_apify_service.return_value = mock_service
#     
#     # Call the helper function
#     client = _get_apify_client(token="test_token")
#     
#     # Verify fallback was used after exception
#     assert client == mock_client
#     mock_get_injectable_client.assert_called_once()
#     mock_apify_service.assert_called_once_with("test_token")


class TestApifyCommands:
    """Test the Apify CLI commands."""

    @patch('os.environ.get')
    def test_ensure_token_with_env_var(self, mock_environ_get, original_token):
        """Test ensuring the token with the env var."""
        # Mock environment to not detect pytest
        mock_environ_get.side_effect = lambda key, default=None: {
            'PYTEST_CURRENT_TEST': None,
            'APIFY_TOKEN': 'test_token'
        }.get(key, default)
        
        # Ensure token is set for the test
        os.environ["APIFY_TOKEN"] = "test_token"
        assert _ensure_token() is True
        assert settings.APIFY_TOKEN == "test_token"

    @patch('os.environ.get')
    def test_ensure_token_with_settings(self, mock_environ_get, original_token):
        """Test ensuring the token with settings."""
        # Mock environment to not detect pytest
        mock_environ_get.side_effect = lambda key, default=None: {
            'PYTEST_CURRENT_TEST': None,
            'APIFY_TOKEN': None 
        }.get(key, default)
        
        if "APIFY_TOKEN" in os.environ:
            del os.environ["APIFY_TOKEN"]
        settings.APIFY_TOKEN = "settings_token"
        assert _ensure_token() is True

    @patch('os.environ.get')
    def test_ensure_token_missing(self, mock_environ_get, runner, original_token):
        """Test ensuring the token when it's missing."""
        # Mock environment to not detect pytest
        mock_environ_get.side_effect = lambda key, default=None: {
            'PYTEST_CURRENT_TEST': None,
            'APIFY_TOKEN': None
        }.get(key, default)
        
        if "APIFY_TOKEN" in os.environ:
            del os.environ["APIFY_TOKEN"]
        settings.APIFY_TOKEN = None
        assert _ensure_token() is False

    @patch("local_newsifier.cli.commands.apify._get_apify_client")
    def test_test_connection(
        self, mock_get_client, mock_apify_service, runner, original_token
    ):
        """Test the test connection command."""
        # Setup
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.user().get.return_value = {"username": "test_user"}
        os.environ["APIFY_TOKEN"] = "test_token"

        # Run the command
        result = runner.invoke(test_connection)

        # Verify
        assert result.exit_code == 0
        assert "Connection to Apify API successful" in result.output
        assert "Connected as: test_user" in result.output
        
        # Verify client was obtained without a token parameter (default)
        mock_get_client.assert_called_once_with(None)

    @patch("local_newsifier.cli.commands.apify._get_apify_client")
    def test_test_connection_with_token_param(
        self, mock_get_client, mock_apify_service, runner, original_token
    ):
        """Test the test connection command with token parameter."""
        # Setup
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.user().get.return_value = {"username": "test_user_param"}

        # Run the command
        result = runner.invoke(test_connection, ["--token", "param_token"])

        # Verify
        assert result.exit_code == 0
        assert "Connection to Apify API successful" in result.output
        assert "Connected as: test_user_param" in result.output
        
        # Verify client was obtained with the specified token
        mock_get_client.assert_called_once_with("param_token")

    @patch("local_newsifier.cli.commands.apify._get_apify_client")
    def test_run_actor(
        self, mock_get_client, mock_apify_service, runner, original_token
    ):
        """Test the run actor command."""
        # Setup
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        # Simulate actor run
        mock_actor = MagicMock()
        mock_client.actor.return_value = mock_actor
        mock_actor.call.return_value = {
            "id": "test_run",
            "status": "SUCCEEDED",
            "defaultDatasetId": "test_dataset",
        }
        os.environ["APIFY_TOKEN"] = "test_token"

        # Run the command
        result = runner.invoke(
            run_actor, ["test_actor", "--input", '{"param":"value"}']
        )

        # Verify
        assert result.exit_code == 0
        assert "Running actor test_actor" in result.output
        assert "Actor run completed" in result.output
        assert "Default dataset ID: test_dataset" in result.output
        
        # Verify client was obtained without specific token
        mock_get_client.assert_called_once_with(None)
        # Verify actor was called correctly
        mock_client.actor.assert_called_once_with("test_actor")
        # Updated to include wait_secs=None which is now passed by the actual code
        mock_actor.call.assert_called_once_with(run_input={"param":"value"}, wait_secs=None)

    @patch("local_newsifier.cli.commands.apify._get_apify_client")
    def test_run_actor_with_input_file(
        self, mock_get_client, runner, original_token
    ):
        """Test the run actor command with input file."""
        # Setup
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        # Simulate actor run
        mock_actor = MagicMock()
        mock_client.actor.return_value = mock_actor
        mock_actor.call.return_value = {
            "id": "test_run",
            "status": "SUCCEEDED",
            "defaultDatasetId": "test_dataset",
        }
        os.environ["APIFY_TOKEN"] = "test_token"

        # Create a temporary file with input
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            json.dump({"param": "file_value"}, f)
            input_file = f.name

        try:
            # Run the command
            result = runner.invoke(run_actor, ["test_actor", "--input", input_file])

            # Verify
            assert result.exit_code == 0
            assert "Loaded input from file" in result.output
            assert "Running actor test_actor" in result.output
            
            # Verify client was obtained without specific token
            mock_get_client.assert_called_once_with(None)
            # Verify actor was called correctly with the file input
            mock_client.actor.assert_called_once_with("test_actor")
            # Should include wait_secs=None which is passed by the actual code
            mock_actor.call.assert_called_once_with(run_input={"param": "file_value"}, wait_secs=None)
        finally:
            # Clean up
            os.unlink(input_file)

    @patch("local_newsifier.cli.commands.apify._get_apify_client")
    def test_run_actor_with_output_file(
        self, mock_get_client, runner, original_token
    ):
        """Test the run actor command with output to file."""
        # Setup
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        # Simulate actor run
        mock_actor = MagicMock()
        mock_client.actor.return_value = mock_actor
        mock_actor.call.return_value = {
            "id": "test_run",
            "status": "SUCCEEDED",
            "defaultDatasetId": "test_dataset",
        }
        os.environ["APIFY_TOKEN"] = "test_token"

        with tempfile.NamedTemporaryFile(delete=False) as f:
            output_file = f.name

        try:
            # Run the command
            result = runner.invoke(
                run_actor,
                ["test_actor", "--input", '{"param":"value"}', "--output", output_file],
            )

            # Verify
            assert result.exit_code == 0
            assert f"Output saved to {output_file}" in result.output

            # Check the output file contents
            with open(output_file, "r") as f:
                output_content = json.load(f)
                assert output_content["id"] == "test_run"
                
            # Verify client was obtained without specific token
            mock_get_client.assert_called_once_with(None)
            # Verify actor was called correctly
            mock_client.actor.assert_called_once_with("test_actor")
            # Should include wait_secs=None which is passed by the actual code
            mock_actor.call.assert_called_once_with(run_input={"param":"value"}, wait_secs=None)
        finally:
            # Clean up
            os.unlink(output_file)

    @patch("local_newsifier.cli.commands.apify._get_apify_client")
    def test_get_dataset(
        self, mock_get_client, runner, original_token
    ):
        """Test the get dataset command."""
        # Setup
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        # Mock dataset client
        mock_dataset = MagicMock()
        mock_client.dataset.return_value = mock_dataset
        
        # Mock items list
        mock_dataset.list_items.return_value = {
            "items": [{"id": 1, "title": "Test Article", "url": "https://example.com"}]
        }
        
        os.environ["APIFY_TOKEN"] = "test_token"

        # Run the command
        result = runner.invoke(get_dataset, ["test_dataset"])

        # Verify
        assert result.exit_code == 0
        assert "Retrieving items from dataset test_dataset" in result.output
        assert "Retrieved 1 items" in result.output
        
        # Verify client was used correctly
        mock_get_client.assert_called_once_with(None)
        mock_client.dataset.assert_called_once_with("test_dataset")
        mock_dataset.list_items.assert_called_once_with(limit=10, offset=0)

    @patch("local_newsifier.cli.commands.apify._get_apify_client")
    def test_get_dataset_with_table_format(
        self, mock_get_client, runner, original_token
    ):
        """Test the get dataset command with table format."""
        # Setup
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        # Mock dataset client
        mock_dataset = MagicMock()
        mock_client.dataset.return_value = mock_dataset
        
        # Mock items list
        mock_dataset.list_items.return_value = {
            "items": [{"id": 1, "title": "Test Article", "url": "https://example.com"}]
        }
        
        os.environ["APIFY_TOKEN"] = "test_token"

        # Run the command
        result = runner.invoke(get_dataset, ["test_dataset", "--format", "table"])

        # Verify
        assert result.exit_code == 0
        assert "Retrieving items from dataset test_dataset" in result.output
        assert "Retrieved 1 items" in result.output
        # Table output should have headers - lowercase column names
        assert "title" in result.output
        
        # Verify client was used correctly
        mock_get_client.assert_called_once_with(None)
        mock_client.dataset.assert_called_once_with("test_dataset")
        mock_dataset.list_items.assert_called_once_with(limit=10, offset=0)

    @patch("local_newsifier.cli.commands.apify._get_apify_client")
    def test_get_actor(
        self, mock_get_client, runner, original_token
    ):
        """Test the get actor command."""
        # Setup
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        # Mock actor client
        mock_actor = MagicMock()
        mock_client.actor.return_value = mock_actor
        
        # Mock actor details
        mock_actor.get.return_value = {
            "id": "test_actor",
            "name": "Test Actor",
            "title": "Test Actor Title",
            "description": "Test actor description",
            "version": {"versionNumber": "1.0.0"},
            "defaultRunInput": {"field1": "value1"},
        }
        
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
        
        # Verify client was used correctly
        mock_get_client.assert_called_once_with(None)
        mock_client.actor.assert_called_once_with("test_actor")
        mock_actor.get.assert_called_once()

    @patch("local_newsifier.cli.commands.apify._get_apify_client")
    def test_scrape_content(
        self, mock_get_client, runner, original_token
    ):
        """Test the scrape content command."""
        # Setup
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        # Mock actor client
        mock_actor = MagicMock()
        mock_client.actor.return_value = mock_actor
        
        # Mock actor run
        mock_actor.call.return_value = {
            "id": "test_run",
            "status": "SUCCEEDED",
            "defaultDatasetId": "test_dataset",
        }
        
        # Mock dataset client for getting results
        mock_dataset = MagicMock()
        mock_client.dataset.return_value = mock_dataset
        
        # Mock items list - one page of content
        mock_dataset.list_items.return_value = {
            "items": [{"id": 1, "url": "https://example.com", "html": "<html></html>"}]
        }
        
        os.environ["APIFY_TOKEN"] = "test_token"

        # Run the command
        result = runner.invoke(scrape_content, ["https://example.com"])

        # Verify
        assert result.exit_code == 0
        assert "Scraping content from https://example.com" in result.output
        assert "Using max pages: 5, max depth: 1" in result.output
        assert "Scraping complete!" in result.output
        assert "Retrieved 1 pages of content" in result.output

        # Check that actor was called with the correct input
        mock_get_client.assert_called_once_with(None)
        mock_client.actor.assert_called_once_with("apify/website-content-crawler")
        
        # Verify the actor call had the expected input
        actor_call_args = mock_actor.call.call_args[1]["run_input"]
        assert actor_call_args["startUrls"] == [{"url": "https://example.com"}]
        assert actor_call_args["maxCrawlPages"] == 5
        assert actor_call_args["maxCrawlDepth"] == 1
        assert actor_call_args["maxPagesPerCrawl"] == 5

    @patch("local_newsifier.cli.commands.apify._get_apify_client")
    def test_scrape_content_with_output(
        self, mock_get_client, runner, original_token
    ):
        """Test the scrape content command with output to file."""
        # Setup
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        # Mock actor client
        mock_actor = MagicMock()
        mock_client.actor.return_value = mock_actor
        
        # Mock actor run
        mock_actor.call.return_value = {
            "id": "test_run",
            "status": "SUCCEEDED",
            "defaultDatasetId": "test_dataset",
        }
        
        # Mock dataset client for getting results
        mock_dataset = MagicMock()
        mock_client.dataset.return_value = mock_dataset
        
        # Mock items list - one page of content
        mock_dataset.list_items.return_value = {
            "items": [{"id": 1, "url": "https://example.com", "html": "<html></html>"}]
        }
        
        os.environ["APIFY_TOKEN"] = "test_token"

        with tempfile.NamedTemporaryFile(delete=False) as f:
            output_file = f.name

        try:
            # Run the command
            result = runner.invoke(
                scrape_content, ["https://example.com", "--output", output_file]
            )

            # Verify
            assert result.exit_code == 0
            assert f"Output saved to {output_file}" in result.output

            # Check the output file contents
            with open(output_file, "r") as f:
                output_content = json.load(f)
                assert len(output_content) == 1
                assert output_content[0]["id"] == 1
                
            # Check that actor was called with the correct input
            mock_get_client.assert_called_once_with(None)
            mock_client.actor.assert_called_once_with("apify/website-content-crawler")
        finally:
            # Clean up
            os.unlink(output_file)

    @patch("local_newsifier.cli.commands.apify._get_apify_client")
    def test_web_scraper(
        self, mock_get_client, runner, original_token
    ):
        """Test the web-scraper command."""
        # Setup
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        # Mock actor client
        mock_actor = MagicMock()
        mock_client.actor.return_value = mock_actor
        
        # Mock actor run
        mock_actor.call.return_value = {
            "id": "test_run",
            "status": "SUCCEEDED",
            "defaultDatasetId": "test_dataset",
        }
        
        # Mock dataset client for getting results
        mock_dataset = MagicMock()
        mock_client.dataset.return_value = mock_dataset
        
        # Mock items list - one page of content
        mock_dataset.list_items.return_value = {
            "items": [{"id": 1, "url": "https://example.com", "html": "<html></html>"}]
        }
        
        os.environ["APIFY_TOKEN"] = "test_token"

        # Run the command
        result = runner.invoke(web_scraper, ["https://example.com"])

        # Verify
        assert result.exit_code == 0
        assert "Scraping website from https://example.com" in result.output
        assert "Using selector: a, max pages: 5" in result.output
        assert "Retrieved 1 pages of data" in result.output

        # Check that actor was called with the correct input
        mock_get_client.assert_called_once_with(None)
        mock_client.actor.assert_called_once_with("apify/web-scraper")
        
        # Verify the actor input fields
        actor_call_args = mock_actor.call.call_args[1]["run_input"]
        assert "startUrls" in actor_call_args
        assert "linkSelector" in actor_call_args
        assert "pageFunction" in actor_call_args
        assert "maxPagesPerCrawl" in actor_call_args
        assert actor_call_args["startUrls"][0]["url"] == "https://example.com"

    @patch("local_newsifier.cli.commands.apify._get_apify_client")
    def test_web_scraper_with_options(
        self, mock_get_client, runner, original_token
    ):
        """Test the web-scraper command with custom options."""
        # Setup
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        # Mock actor client
        mock_actor = MagicMock()
        mock_client.actor.return_value = mock_actor
        
        # Mock actor run
        mock_actor.call.return_value = {
            "id": "test_run",
            "status": "SUCCEEDED",
            "defaultDatasetId": "test_dataset",
        }
        
        # Mock dataset client for getting results
        mock_dataset = MagicMock()
        mock_client.dataset.return_value = mock_dataset
        
        # Mock items list - one page of content
        mock_dataset.list_items.return_value = {
            "items": [{"id": 1, "url": "https://example.com", "html": "<html></html>"}]
        }
        
        os.environ["APIFY_TOKEN"] = "test_token"

        # Run the command with options
        result = runner.invoke(
            web_scraper,
            [
                "https://example.com",
                "--selector",
                "article a",
                "--max-pages",
                "10",
                "--wait-for",
                "#content",
                "--page-function",
                "async function pageFunction(context) { return {custom: true}; }",
            ],
        )

        # Verify
        assert result.exit_code == 0
        assert "Scraping website from https://example.com" in result.output
        assert "Using selector: article a, max pages: 10" in result.output

        # Check that actor was called with the correct input
        mock_get_client.assert_called_once_with(None)
        mock_client.actor.assert_called_once_with("apify/web-scraper")
        
        # Verify the actor input fields
        actor_call_args = mock_actor.call.call_args[1]["run_input"]
        assert actor_call_args["startUrls"][0]["url"] == "https://example.com"
        assert actor_call_args["linkSelector"] == "article a"
        assert actor_call_args["maxPagesPerCrawl"] == 10
        assert actor_call_args["waitFor"] == "#content"
        assert "async function pageFunction" in actor_call_args["pageFunction"]

    @patch("local_newsifier.cli.commands.apify._get_apify_client")
    def test_web_scraper_with_output(
        self, mock_get_client, runner, original_token
    ):
        """Test the web-scraper command with output to file."""
        # Setup
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        # Mock actor client
        mock_actor = MagicMock()
        mock_client.actor.return_value = mock_actor
        
        # Mock actor run
        mock_actor.call.return_value = {
            "id": "test_run",
            "status": "SUCCEEDED",
            "defaultDatasetId": "test_dataset",
        }
        
        # Mock dataset client for getting results
        mock_dataset = MagicMock()
        mock_client.dataset.return_value = mock_dataset
        
        # Mock items list - one page of content
        mock_dataset.list_items.return_value = {
            "items": [{"id": 1, "url": "https://example.com", "html": "<html></html>"}]
        }
        
        os.environ["APIFY_TOKEN"] = "test_token"

        with tempfile.NamedTemporaryFile(delete=False) as f:
            output_file = f.name

        try:
            # Run the command
            result = runner.invoke(
                web_scraper, ["https://example.com", "--output", output_file]
            )

            # Verify
            assert result.exit_code == 0
            assert f"Output saved to {output_file}" in result.output

            # Check the output file contents
            with open(output_file, "r") as f:
                output_content = json.load(f)
                assert len(output_content) == 1
                assert output_content[0]["id"] == 1
                
            # Check that actor was called with the correct input
            mock_get_client.assert_called_once_with(None)
            mock_client.actor.assert_called_once_with("apify/web-scraper")
        finally:
            # Clean up
            os.unlink(output_file)

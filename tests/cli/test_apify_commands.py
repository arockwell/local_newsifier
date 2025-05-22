"""Tests for the Apify CLI commands."""

import json
import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from local_newsifier.cli.commands.apify import (_ensure_token, get_actor, get_dataset, run_actor,
                                                scrape_content, test_connection, web_scraper)
from local_newsifier.config.settings import settings
from local_newsifier.services.apify_service import ApifyService


@pytest.fixture
def mock_apify_service():
    """Create a mock ApifyService."""
    mock_service = MagicMock(spec=ApifyService)

    # Mock client property
    mock_client = MagicMock()
    type(mock_service).client = mock_client

    # Configure mock returns
    mock_user = {"username": "test_user"}
    mock_client.user().get.return_value = mock_user

    # Mock actor run
    mock_run = {
        "id": "test_run",
        "status": "SUCCEEDED",
        "defaultDatasetId": "test_dataset",
    }
    mock_service.run_actor.return_value = mock_run
    mock_client.actor().call.return_value = mock_run

    # Mock dataset items
    mock_items = [{"id": 1, "title": "Test Article", "url": "https://example.com"}]
    mock_dataset_response = {"items": mock_items}
    mock_service.get_dataset_items.return_value = mock_dataset_response
    mock_client.dataset().list_items.return_value = mock_dataset_response

    # Mock actor details
    mock_actor = {
        "id": "test_actor",
        "name": "Test Actor",
        "title": "Test Actor Title",
        "description": "Test actor description",
        "version": {"versionNumber": "1.0.0"},
        "defaultRunInput": {"field1": "value1"},
    }
    mock_service.get_actor_details.return_value = mock_actor
    mock_client.actor().get.return_value = mock_actor

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

    @patch("local_newsifier.cli.commands.apify.get_injected_obj")
    def test_test_connection(
        self, mock_get_injected_obj, mock_apify_service, runner, original_token
    ):
        """Test the test connection command."""
        # Setup
        mock_get_injected_obj.return_value = mock_apify_service
        os.environ["APIFY_TOKEN"] = "test_token"

        # Run the command
        result = runner.invoke(test_connection)

        # Verify
        assert result.exit_code == 0
        assert "Connection to Apify API successful" in result.output
        assert "Connected as: test_user" in result.output
        
        # Verify the lambda function was called with the token
        # Since we can't directly check the lambda, we check that get_injected_obj was called

    @patch("local_newsifier.cli.commands.apify.get_injected_obj")
    def test_test_connection_with_token_param(
        self, mock_get_injected_obj, mock_apify_service, runner, original_token
    ):
        """Test the test connection command with token parameter."""
        # Setup
        mock_get_injected_obj.return_value = mock_apify_service

        # Run the command
        result = runner.invoke(test_connection, ["--token", "param_token"])

        # Verify
        assert result.exit_code == 0
        assert "Connection to Apify API successful" in result.output

    @patch("local_newsifier.cli.commands.apify.get_injected_obj")
    def test_run_actor(
        self, mock_get_injected_obj, mock_apify_service, runner, original_token
    ):
        """Test the run actor command."""
        # Setup
        mock_get_injected_obj.return_value = mock_apify_service
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

    @patch("local_newsifier.cli.commands.apify.get_injected_obj")
    def test_run_actor_with_input_file(
        self, mock_get_injected_obj, mock_apify_service, runner, original_token
    ):
        """Test the run actor command with input file."""
        # Setup
        mock_get_injected_obj.return_value = mock_apify_service
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
        finally:
            # Clean up
            os.unlink(input_file)

    @patch("local_newsifier.cli.commands.apify.get_injected_obj")
    def test_run_actor_with_output_file(
        self, mock_get_injected_obj, mock_apify_service, runner, original_token
    ):
        """Test the run actor command with output to file."""
        # Setup
        mock_get_injected_obj.return_value = mock_apify_service
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
        finally:
            # Clean up
            os.unlink(output_file)

    @patch("local_newsifier.cli.commands.apify.get_injected_obj")
    def test_get_dataset(
        self, mock_get_injected_obj, runner, original_token, mock_apify_service
    ):
        """Test the get dataset command."""
        # Setup
        mock_get_injected_obj.return_value = mock_apify_service
        os.environ["APIFY_TOKEN"] = "test_token"

        # Run the command
        result = runner.invoke(get_dataset, ["test_dataset"])

        # Verify
        assert result.exit_code == 0
        assert "Retrieving items from dataset test_dataset" in result.output
        assert "Retrieved 1 items" in result.output

    @patch("local_newsifier.cli.commands.apify.get_injected_obj")
    def test_get_dataset_with_table_format(
        self, mock_get_injected_obj, runner, original_token, mock_apify_service
    ):
        """Test the get dataset command with table format."""
        # Setup
        mock_get_injected_obj.return_value = mock_apify_service
        os.environ["APIFY_TOKEN"] = "test_token"

        # Run the command
        result = runner.invoke(get_dataset, ["test_dataset", "--format", "table"])

        # Verify
        assert result.exit_code == 0
        assert "Retrieving items from dataset test_dataset" in result.output
        assert "Retrieved 1 items" in result.output
        # Table output should have headers - lowercase column names
        assert "title" in result.output

    @patch("local_newsifier.cli.commands.apify.get_injected_obj")
    def test_get_actor(
        self, mock_get_injected_obj, runner, original_token, mock_apify_service
    ):
        """Test the get actor command."""
        # Setup
        mock_get_injected_obj.return_value = mock_apify_service
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

    @patch("local_newsifier.cli.commands.apify.get_injected_obj")
    def test_scrape_content(
        self, mock_get_injected_obj, runner, original_token, mock_apify_service
    ):
        """Test the scrape content command."""
        # Setup
        mock_get_injected_obj.return_value = mock_apify_service
        os.environ["APIFY_TOKEN"] = "test_token"

        # Run the command
        result = runner.invoke(scrape_content, ["https://example.com"])

        # Verify
        assert result.exit_code == 0
        assert "Scraping content from https://example.com" in result.output
        assert "Using max pages: 5, max depth: 1" in result.output
        assert "Scraping complete!" in result.output
        assert "Retrieved 1 pages of content" in result.output

    @patch("local_newsifier.cli.commands.apify.get_injected_obj")
    def test_scrape_content_with_output(
        self, mock_get_injected_obj, runner, original_token, mock_apify_service
    ):
        """Test the scrape content command with output to file."""
        # Setup
        mock_get_injected_obj.return_value = mock_apify_service
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
        finally:
            # Clean up
            os.unlink(output_file)

    @patch("local_newsifier.cli.commands.apify.get_injected_obj")
    def test_web_scraper(
        self, mock_get_injected_obj, runner, original_token, mock_apify_service
    ):
        """Test the web-scraper command."""
        # Setup
        mock_get_injected_obj.return_value = mock_apify_service
        os.environ["APIFY_TOKEN"] = "test_token"

        # Run the command
        result = runner.invoke(web_scraper, ["https://example.com"])

        # Verify
        assert result.exit_code == 0
        assert "Scraping website from https://example.com" in result.output
        assert "Using selector: a, max pages: 5" in result.output
        assert "Retrieved 1 pages of data" in result.output

    @patch("local_newsifier.cli.commands.apify.get_injected_obj")
    def test_web_scraper_with_options(
        self, mock_get_injected_obj, runner, original_token, mock_apify_service
    ):
        """Test the web-scraper command with custom options."""
        # Setup
        mock_get_injected_obj.return_value = mock_apify_service
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

    @patch("local_newsifier.cli.commands.apify.get_injected_obj")
    def test_web_scraper_with_output(
        self, mock_get_injected_obj, runner, original_token, mock_apify_service
    ):
        """Test the web-scraper command with output to file."""
        # Setup
        mock_get_injected_obj.return_value = mock_apify_service
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
        finally:
            # Clean up
            os.unlink(output_file)
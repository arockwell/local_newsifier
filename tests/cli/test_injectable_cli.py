"""Tests for the CLI commands with injectable dependencies."""

import pytest
from unittest.mock import MagicMock, patch
from click.testing import CliRunner

from local_newsifier.cli.main import cli
from local_newsifier.cli.commands.db import db_group
from local_newsifier.cli.commands.apify import apify_group, test_connection
from local_newsifier.di.providers import get_apify_service_cli
from local_newsifier.services.apify_service import ApifyService


@patch('local_newsifier.cli.commands.apify.get_injected_obj')
def test_apify_service_injection(mock_get_injected_obj):
    """Test the Apify service injection in CLI commands."""
    # Set up mock apify service
    mock_service = MagicMock(spec=ApifyService)
    mock_client = MagicMock()
    type(mock_service).client = mock_client
    mock_client.user().get.return_value = {"username": "test_user"}
    
    # Configure the mock to return our service
    mock_get_injected_obj.return_value = mock_service
    
    # Call the command through the CLI
    runner = CliRunner()
    result = runner.invoke(cli, ["apify", "test", "--token", "test_token"])
    
    # Verify result
    assert result.exit_code == 0
    assert "Connection to Apify API successful" in result.output
    assert "Connected as: test_user" in result.output
    
    # Verify get_injected_obj was called (can't verify the lambda directly)
    mock_get_injected_obj.assert_called_once()


@patch('local_newsifier.cli.commands.db.get_injected_obj')
def test_db_stats_integration(mock_get_injected_obj):
    """Test the db stats command with injectable dependencies."""
    # Create a side effect to handle different calls to get_injected_obj
    def side_effect_func(provider):
        # For session provider
        mock_session = MagicMock()
        
        # For article_crud and other CRUDs
        mock_crud = MagicMock()
        
        # Set up count results
        mock_crud.count.return_value = 5
        
        # Create proper mock objects for articles that have a strftime method
        latest_article = MagicMock()
        latest_article.created_at.strftime.return_value = "2025-05-01 12:30:45"
        
        oldest_article = MagicMock()
        oldest_article.created_at.strftime.return_value = "2025-04-01 10:15:30"
        
        # Set up article query results
        mock_crud.get_latest.return_value = latest_article
        mock_crud.get_oldest.return_value = oldest_article
        
        return mock_session if "session" in str(provider) else mock_crud
    
    # Set up the side effect
    mock_get_injected_obj.side_effect = side_effect_func
    
    # Call the command through the CLI
    runner = CliRunner()
    result = runner.invoke(cli, ["db", "stats"])
    
    # Verify result
    assert result.exit_code == 0
    assert "Database Statistics" in result.output


@patch('local_newsifier.cli.commands.db.get_injected_obj')
def test_db_articles_integration(mock_get_injected_obj):
    """Test the db articles command with injectable dependencies."""
    # Set up mock session and article crud
    mock_session = MagicMock()
    mock_article_crud = MagicMock()
    
    # Configure side effect to return appropriate objects based on the provider
    def side_effect(provider):
        from local_newsifier.di.providers import get_session, get_article_crud
        if provider == get_session:
            return mock_session
        elif "article_crud" in str(provider):
            return mock_article_crud
        return MagicMock()
    
    mock_get_injected_obj.side_effect = side_effect
    
    # Mock empty result for the query
    mock_article_crud.get_all.return_value = []

    # Call the command through the CLI
    runner = CliRunner()
    result = runner.invoke(cli, ["db", "articles"])

    # Verify result
    assert result.exit_code == 0
    # The actual output format uses tabulate, so check for table format instead
    assert "Articles (0 results)" in result.output
    # Verify the get_injected_obj was called
    assert mock_get_injected_obj.call_count > 0

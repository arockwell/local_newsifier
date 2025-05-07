"""Tests for the CLI commands with injectable dependencies."""

import pytest
from unittest.mock import MagicMock, patch
from click.testing import CliRunner

from local_newsifier.cli.main import cli
from local_newsifier.cli.commands.db import db_group
from local_newsifier.cli.commands.apify import apify_group
from local_newsifier.cli.commands.apify import _get_apify_client, test_connection


@patch('local_newsifier.cli.commands.apify.get_apify_client')
def test_get_apify_client_integration(mock_get_injectable_client):
    """Test the get_apify_client helper function directly."""
    # Set up mock injectable client
    mock_client = MagicMock()
    mock_get_injectable_client.return_value = mock_client
    
    # Call the helper function
    result = _get_apify_client(token="test_token")
    
    # Verify that injectable client was used
    assert result == mock_client
    mock_get_injectable_client.assert_called_once_with(token="test_token")


@patch('local_newsifier.services.apify_service.ApifyService')
@patch('local_newsifier.cli.commands.apify.get_apify_client', side_effect=ImportError)
def test_get_apify_client_integration_fallback(mock_get_injectable_client, mock_apify_service):
    """Test the get_apify_client helper function's fallback mechanism."""
    # Set up mock service and client
    mock_service = MagicMock()
    mock_client = MagicMock()
    mock_service.client = mock_client
    mock_apify_service.return_value = mock_service
    
    # Call the helper function
    result = _get_apify_client(token="test_token")
    
    # Verify fallback was used
    assert result == mock_client
    mock_get_injectable_client.assert_called_once()
    mock_apify_service.assert_called_once_with("test_token")


@patch('local_newsifier.cli.commands.db.get_db_stats')
def test_db_stats_integration(mock_get_db_stats):
    """Test the db stats command with injectable dependencies."""
    # Create proper mock objects for articles that have a strftime method
    latest_article = MagicMock()
    latest_article.created_at.strftime.return_value = "2025-05-01 12:30:45"
    
    oldest_article = MagicMock()
    oldest_article.created_at.strftime.return_value = "2025-04-01 10:15:30"
    
    # Set up mock statistics return value
    mock_get_db_stats.return_value = (
        5,  # article_count
        latest_article,  # latest_article
        oldest_article,  # oldest_article
        3,  # feed_count
        2,  # active_feed_count
        10,  # processing_log_count
        15   # entity_count
    )
    
    # Call the command through the CLI
    runner = CliRunner()
    result = runner.invoke(cli, ["db", "stats"])
    
    # Verify result
    assert result.exit_code == 0
    assert "Database Statistics" in result.output
    # Verify the injectable provider was called
    mock_get_db_stats.assert_called_once()


@patch('local_newsifier.cli.commands.db.get_injectable_session')
def test_db_articles_integration(mock_get_session):
    """Test the db articles command with injectable dependencies."""
    # Set up mock session
    mock_session = MagicMock()
    mock_get_session.return_value = mock_session
    
    # Mock empty result for the query
    mock_session.exec.return_value.all.return_value = []
    
    # Call the command through the CLI
    runner = CliRunner()
    result = runner.invoke(cli, ["db", "articles"])
    
    # Verify result
    assert result.exit_code == 0
    assert "No articles found" in result.output
    # Verify the injectable session was used
    mock_get_session.assert_called_once()


@patch('local_newsifier.cli.commands.apify._get_apify_client')
def test_apify_test_connection_integration(mock_get_client):
    """Test the apify test connection command with injectable client."""
    # Set up mock client
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client
    mock_client.user().get.return_value = {"username": "test_user"}
    
    # Call the command through the CLI
    runner = CliRunner()
    result = runner.invoke(cli, ["apify", "test", "--token", "test_token"])
    
    # Verify result
    assert result.exit_code == 0
    assert "Connection to Apify API successful" in result.output
    assert "Connected as: test_user" in result.output
    # Verify the _get_apify_client helper was called with the token
    mock_get_client.assert_called_once_with("test_token")
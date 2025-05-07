"""Tests for the database diagnostics CLI commands."""

import pytest
from unittest.mock import patch, MagicMock
from click.testing import CliRunner

from local_newsifier.cli.main import cli


def test_db_group():
    """Test that the db command group loads without errors."""
    runner = CliRunner()
    result = runner.invoke(cli, ["db", "--help"])
    assert result.exit_code == 0
    assert "stats" in result.output
    assert "duplicates" in result.output
    assert "articles" in result.output
    assert "inspect" in result.output
    assert "purge-duplicates" in result.output


@patch('local_newsifier.cli.commands.db.get_db_stats')
@patch('local_newsifier.cli.commands.db.next')
def test_db_stats_command_injectable(mock_next, mock_get_db_stats):
    """Test that the db stats command runs using injectable dependencies."""
    # Create a mock article with created_at attribute
    mock_article = MagicMock()
    mock_article.created_at = None
    
    # Set up mock statistics return value
    mock_get_db_stats.return_value = (
        5,  # article_count
        mock_article,  # latest_article
        mock_article,  # oldest_article
        3,  # feed_count
        2,  # active_feed_count
        10,  # processing_log_count
        15   # entity_count
    )
    
    runner = CliRunner()
    result = runner.invoke(cli, ["db", "stats"])
    
    assert result.exit_code == 0
    assert "Database Statistics" in result.output
    assert "Articles:" in result.output
    assert "Total count: 5" in result.output
    assert "RSS Feeds:" in result.output
    assert "Total count: 3" in result.output
    
    # Verify that the injectable provider was called
    mock_get_db_stats.assert_called_once()
    # The fallback mechanism should not be used
    mock_next.assert_not_called()


@patch('local_newsifier.cli.commands.db.get_db_stats', side_effect=ImportError)
@patch('local_newsifier.cli.commands.db.next')
def test_db_stats_command_fallback(mock_next, mock_get_db_stats):
    """Test that the db stats command runs with fallback when injectable fails."""
    # Set up mock session and query results
    mock_session = MagicMock()
    mock_next.return_value = mock_session
    
    # Mock query execution results for article stats
    mock_session.exec.return_value.one.return_value = 5  # Mock count
    mock_session.exec.return_value.first.return_value = None  # Mock no articles
    
    runner = CliRunner()
    result = runner.invoke(cli, ["db", "stats"])
    
    assert result.exit_code == 0
    assert "Database Statistics" in result.output
    assert "Articles" in result.output
    assert "RSS Feeds" in result.output
    
    # Verify that fallback to direct DB access was used
    mock_get_db_stats.assert_called_once()
    mock_next.assert_called_once()


@patch('local_newsifier.cli.commands.db.get_injectable_session')
@patch('local_newsifier.cli.commands.db.next')
def test_db_duplicates_no_duplicates(mock_next, mock_get_injectable_session):
    """Test that the db duplicates command handles case with no duplicates."""
    # Set up mock session and query results
    mock_session = MagicMock()
    mock_next.return_value = mock_session
    mock_get_injectable_session.side_effect = ImportError()  # Force fallback path
    
    # Mock empty result for duplicate query
    mock_session.exec.return_value.all.return_value = []
    
    runner = CliRunner()
    result = runner.invoke(cli, ["db", "duplicates"])
    
    assert result.exit_code == 0
    assert "No duplicate articles found" in result.output


@patch('local_newsifier.cli.commands.db.get_injectable_session')
def test_db_articles_no_articles_injectable(mock_get_injectable_session):
    """Test that the db articles command works with injectable dependencies."""
    # Set up mock session
    mock_session = MagicMock()
    mock_get_injectable_session.return_value = mock_session
    
    # Mock the session.exec() chain to return an empty list
    mock_session.exec.return_value.all.return_value = []
    
    runner = CliRunner()
    result = runner.invoke(cli, ["db", "articles"])
    
    assert result.exit_code == 0
    assert "No articles found matching the criteria" in result.output
    
    # Verify injectable dependencies were used
    mock_get_injectable_session.assert_called_once()


@patch('local_newsifier.cli.commands.db.get_injectable_session')
@patch('local_newsifier.cli.commands.db.get_article_crud')
def test_db_inspect_article_not_found_injectable(mock_get_article_crud, mock_get_injectable_session):
    """Test that the db inspect command works with injectable dependencies."""
    # Set up mock session
    mock_session = MagicMock()
    mock_get_injectable_session.return_value = mock_session
    
    # Set up mock article CRUD
    mock_article_crud = MagicMock()
    mock_get_article_crud.return_value = mock_article_crud
    
    # Mock article crud get to return None (not found)
    mock_article_crud.get.return_value = None
    
    runner = CliRunner()
    result = runner.invoke(cli, ["db", "inspect", "article", "999"])
    
    assert result.exit_code == 0
    assert "not found" in result.output
    
    # Verify that article crud's get method was called correctly
    mock_article_crud.get.assert_called_once_with(mock_session, 999)


@patch('local_newsifier.cli.commands.db.get_injectable_session')
@patch('local_newsifier.cli.commands.db.next')
def test_db_purge_duplicates_no_duplicates(mock_next, mock_get_injectable_session):
    """Test that the purge-duplicates command handles case with no duplicates."""
    # Set up mock session
    mock_session = MagicMock()
    mock_next.return_value = mock_session
    mock_get_injectable_session.side_effect = ImportError()  # Force fallback path
    
    # Mock empty result for duplicate query
    mock_session.exec.return_value.all.return_value = []
    
    runner = CliRunner()
    # Use --yes to skip confirmation prompt
    result = runner.invoke(cli, ["db", "purge-duplicates", "--yes"])
    
    assert result.exit_code == 0
    assert "No duplicate articles found" in result.output

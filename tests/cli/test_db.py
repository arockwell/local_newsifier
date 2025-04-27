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


@patch('local_newsifier.cli.commands.db.next')
def test_db_stats_command(mock_next):
    """Test that the db stats command runs without errors using mocks."""
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


@patch('local_newsifier.cli.commands.db.next')
def test_db_duplicates_no_duplicates(mock_next):
    """Test that the db duplicates command handles case with no duplicates."""
    # Set up mock session and query results
    mock_session = MagicMock()
    mock_next.return_value = mock_session
    
    # Mock empty result for duplicate query
    mock_session.exec.return_value.all.return_value = []
    
    runner = CliRunner()
    result = runner.invoke(cli, ["db", "duplicates"])
    
    assert result.exit_code == 0
    assert "No duplicate articles found" in result.output


@patch('local_newsifier.cli.commands.db.next')
def test_db_articles_no_articles(mock_next):
    """Test that the db articles command handles case with no articles."""
    # Set up mock session and query results
    mock_session = MagicMock()
    mock_next.return_value = mock_session
    
    # Mock empty result for articles query
    mock_session.exec.return_value.all.return_value = []
    
    runner = CliRunner()
    result = runner.invoke(cli, ["db", "articles"])
    
    assert result.exit_code == 0
    assert "No articles found matching the criteria" in result.output


@patch('local_newsifier.cli.commands.db.next')
def test_db_inspect_article_not_found(mock_next):
    """Test that the db inspect command handles non-existent article."""
    # Set up mock session
    mock_session = MagicMock()
    mock_next.return_value = mock_session
    
    # Mock article crud get to return None (not found)
    from local_newsifier.cli.commands.db import article_crud
    with patch.object(article_crud, 'get', return_value=None):
        runner = CliRunner()
        result = runner.invoke(cli, ["db", "inspect", "article", "999"])
        
        assert result.exit_code == 0
        assert "not found" in result.output


@patch('local_newsifier.cli.commands.db.next')
def test_db_purge_duplicates_no_duplicates(mock_next):
    """Test that the purge-duplicates command handles case with no duplicates."""
    # Set up mock session
    mock_session = MagicMock()
    mock_next.return_value = mock_session
    
    # Mock empty result for duplicate query
    mock_session.exec.return_value.all.return_value = []
    
    runner = CliRunner()
    # Use --yes to skip confirmation prompt
    result = runner.invoke(cli, ["db", "purge-duplicates", "--yes"])
    
    assert result.exit_code == 0
    assert "No duplicate articles found" in result.output

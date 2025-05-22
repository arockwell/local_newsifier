"""Tests for the database diagnostics CLI commands."""

import pytest
from unittest.mock import patch, MagicMock
from click.testing import CliRunner

from local_newsifier.cli.main import cli
from local_newsifier.di.providers import (
    get_session,
    get_article_crud,
    get_rss_feed_crud,
    get_entity_crud,
    get_feed_processing_log_crud,
)


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


@patch("local_newsifier.cli.commands.db.get_injected_obj")
def test_db_stats_command(mock_get_injected_obj):
    """Test that the db stats command runs without errors using mocks."""
    # Set up mock session
    mock_session = MagicMock()
    mock_session_gen = MagicMock()
    mock_session_gen.__next__.return_value = mock_session

    # Configure get_injected_obj to return appropriate objects based on the argument
    def side_effect(provider):
        if provider == get_session:
            return mock_session_gen
        else:
            return MagicMock()

    mock_get_injected_obj.side_effect = side_effect

    # Mock query execution results for article stats
    mock_session.exec.return_value.one.side_effect = [
        5,
        3,
        2,
        7,
        4,
    ]  # Article count, feed count, active feeds, log count, entity count
    mock_session.exec.return_value.first.side_effect = [
        None,
        None,
    ]  # Latest article, oldest article

    runner = CliRunner()
    result = runner.invoke(cli, ["db", "stats"])

    assert result.exit_code == 0
    assert "Database Statistics" in result.output
    assert "Articles" in result.output
    assert "RSS Feeds" in result.output


@patch("local_newsifier.cli.commands.db.get_injected_obj")
def test_db_duplicates_no_duplicates(mock_get_injected_obj):
    """Test that the db duplicates command handles case with no duplicates."""
    # Set up mock session
    mock_session = MagicMock()
    mock_session_gen = MagicMock()
    mock_session_gen.__next__.return_value = mock_session

    # Configure get_injected_obj to return appropriate objects based on the argument
    def side_effect(provider):
        if provider == get_session:
            return mock_session_gen
        else:
            return MagicMock()

    mock_get_injected_obj.side_effect = side_effect

    # Mock empty result for duplicate query
    mock_session.exec.return_value.all.return_value = []

    runner = CliRunner()
    result = runner.invoke(cli, ["db", "duplicates"])

    assert result.exit_code == 0
    assert "No duplicate articles found" in result.output


@patch("local_newsifier.cli.commands.db.get_injected_obj")
def test_db_articles_no_articles(mock_get_injected_obj):
    """Test that the db articles command handles case with no articles."""
    # Set up mock session
    mock_session = MagicMock()
    mock_session_gen = MagicMock()
    mock_session_gen.__next__.return_value = mock_session

    # Configure get_injected_obj to return appropriate objects based on the argument
    def side_effect(provider):
        if provider == get_session:
            return mock_session_gen
        else:
            return MagicMock()

    mock_get_injected_obj.side_effect = side_effect

    # Mock the session.exec() chain to return an empty list
    mock_session.exec.return_value.all.return_value = []

    runner = CliRunner()
    result = runner.invoke(cli, ["db", "articles"])

    assert result.exit_code == 0
    assert "No articles found matching the criteria" in result.output


@patch("local_newsifier.cli.commands.db.get_injected_obj")
def test_db_inspect_article_not_found(mock_get_injected_obj):
    """Test that the db inspect command handles non-existent article."""
    # Set up mock session and article_crud
    mock_session = MagicMock()
    mock_session_gen = MagicMock()
    mock_session_gen.__next__.return_value = mock_session
    mock_article_crud = MagicMock()

    # Configure get_injected_obj to return appropriate objects based on the argument
    def side_effect(provider):
        if provider == get_session:
            return mock_session_gen
        elif provider == get_article_crud:
            return mock_article_crud
        else:
            return MagicMock()

    mock_get_injected_obj.side_effect = side_effect

    # Mock article crud get to return None (not found)
    mock_article_crud.get.return_value = None

    runner = CliRunner()
    result = runner.invoke(cli, ["db", "inspect", "article", "999"])

    assert result.exit_code == 0
    assert "not found" in result.output


@patch("local_newsifier.cli.commands.db.get_injected_obj")
def test_db_purge_duplicates_no_duplicates(mock_get_injected_obj):
    """Test that the purge-duplicates command handles case with no duplicates."""
    # Set up mock session and article_crud
    mock_session = MagicMock()
    mock_session_gen = MagicMock()
    mock_session_gen.__next__.return_value = mock_session
    mock_article_crud = MagicMock()

    # Configure get_injected_obj to return appropriate objects based on the argument
    def side_effect(provider):
        if provider == get_session:
            return mock_session_gen
        elif provider == get_article_crud:
            return mock_article_crud
        else:
            return MagicMock()

    mock_get_injected_obj.side_effect = side_effect

    # Mock empty result for duplicate query
    mock_session.exec.return_value.all.return_value = []

    runner = CliRunner()
    # Use --yes to skip confirmation prompt
    result = runner.invoke(cli, ["db", "purge-duplicates", "--yes"])

    assert result.exit_code == 0
    assert "No duplicate articles found" in result.output

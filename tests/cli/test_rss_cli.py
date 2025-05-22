"""Tests for the RSS CLI utilities."""

import pytest
import click
from click.testing import CliRunner
from unittest.mock import patch

from local_newsifier.cli.commands.rss_cli import handle_rss_cli_errors
from local_newsifier.errors.rss_error import RSSError


def test_handle_rss_cli_errors_with_rss_error():
    """Test the handle_rss_cli_errors decorator with RSSError."""

    @click.command()
    @handle_rss_cli_errors
    def test_command():
        raise RSSError("Test RSS error")

    runner = CliRunner()
    result = runner.invoke(test_command)

    assert result.exit_code == 1
    assert "Error: Test RSS error" in result.output
    assert "Hint:" in result.output


def test_handle_rss_cli_errors_with_timeout_error():
    """Test the handle_rss_cli_errors decorator with timeout error."""

    @click.command()
    @handle_rss_cli_errors
    def test_command():
        raise RSSError("Connection timeout occurred")

    runner = CliRunner()
    result = runner.invoke(test_command)

    assert result.exit_code == 1
    assert "Error: Connection timeout occurred" in result.output
    assert "Hint: The server is taking too long to respond" in result.output


def test_handle_rss_cli_errors_with_connection_error():
    """Test the handle_rss_cli_errors decorator with connection error."""

    @click.command()
    @handle_rss_cli_errors
    def test_command():
        raise RSSError("Connection error")

    runner = CliRunner()
    result = runner.invoke(test_command)

    assert result.exit_code == 1
    assert "Error: Connection error" in result.output
    assert "Hint: Could not connect to the RSS feed" in result.output


def test_handle_rss_cli_errors_with_not_found_error():
    """Test the handle_rss_cli_errors decorator with not found error."""

    @click.command()
    @handle_rss_cli_errors
    def test_command():
        raise RSSError("Feed not found")

    runner = CliRunner()
    result = runner.invoke(test_command)

    assert result.exit_code == 1
    assert "Error: Feed not found" in result.output
    assert "Hint: The RSS feed could not be found" in result.output


def test_handle_rss_cli_errors_with_format_error():
    """Test the handle_rss_cli_errors decorator with format error."""

    @click.command()
    @handle_rss_cli_errors
    def test_command():
        raise RSSError("Invalid format")

    runner = CliRunner()
    result = runner.invoke(test_command)

    assert result.exit_code == 1
    assert "Error: Invalid format" in result.output
    assert "Hint: The feed format is invalid" in result.output


def test_handle_rss_cli_errors_with_exists_error():
    """Test the handle_rss_cli_errors decorator with exists error."""

    @click.command()
    @handle_rss_cli_errors
    def test_command():
        raise RSSError("Feed already exists")

    runner = CliRunner()
    result = runner.invoke(test_command)

    assert result.exit_code == 1
    assert "Error: Feed already exists" in result.output
    assert "Hint: A feed with this URL already exists" in result.output


def test_handle_rss_cli_errors_with_generic_error():
    """Test the handle_rss_cli_errors decorator with generic error."""

    @click.command()
    @handle_rss_cli_errors
    def test_command():
        raise RSSError("Some other error")

    runner = CliRunner()
    result = runner.invoke(test_command)

    assert result.exit_code == 1
    assert "Error: Some other error" in result.output
    assert "Hint: There was a problem with the RSS feed operation" in result.output


def test_handle_rss_cli_errors_with_verbose_mode():
    """Test the handle_rss_cli_errors decorator with verbose mode."""

    @click.command()
    @click.option("--verbose", is_flag=True)
    @handle_rss_cli_errors
    def test_command(verbose):
        ctx = click.get_current_context()
        ctx.obj = {"verbose": verbose}
        original_error = ValueError("Original error")
        raise RSSError("Test RSS error with original", original=original_error)

    runner = CliRunner()
    result = runner.invoke(test_command, ["--verbose"])

    assert result.exit_code == 1
    assert "Error: Test RSS error with original" in result.output
    assert "Additional information:" in result.output
    assert "Original error: ValueError: Original error" in result.output


def test_handle_rss_cli_errors_with_other_exception_verbose():
    """Test the handle_rss_cli_errors decorator with other exceptions in verbose mode."""

    @click.command()
    @click.option("--verbose", is_flag=True)
    @handle_rss_cli_errors
    def test_command(verbose):
        ctx = click.get_current_context()
        ctx.obj = {"verbose": verbose}
        raise ValueError("Test general error")

    runner = CliRunner()
    result = runner.invoke(test_command, ["--verbose"])

    assert result.exit_code == 1
    assert "Unexpected error: ValueError: Test general error" in result.output
    assert "Traceback:" in result.output


def test_handle_rss_cli_errors_with_other_exception():
    """Test the handle_rss_cli_errors decorator with other exceptions."""

    @click.command()
    @handle_rss_cli_errors
    def test_command():
        raise ValueError("Test general error")

    runner = CliRunner()
    result = runner.invoke(test_command)

    assert result.exit_code == 1
    assert "Unexpected error: ValueError: Test general error" in result.output
    assert "Traceback:" not in result.output

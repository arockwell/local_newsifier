"""Tests for the RSS CLI utilities."""

import pytest
import click
from click.testing import CliRunner
from unittest.mock import patch

from local_newsifier.errors.cli import handle_rss_cli
from local_newsifier.errors.error import ServiceError


def test_handle_rss_cli_with_service_error():
    """Test the handle_rss_cli decorator with ServiceError."""
    @click.command()
    @handle_rss_cli
    def test_command():
        raise ServiceError("rss", "parse", "Test RSS error")

    runner = CliRunner()
    result = runner.invoke(test_command)

    assert result.exit_code == 1
    assert "rss.parse: Test RSS error" in result.output
    assert "Hint:" in result.output


def test_handle_rss_cli_with_timeout_error():
    """Test the handle_rss_cli decorator with timeout error."""
    @click.command()
    @handle_rss_cli
    def test_command():
        raise ServiceError("rss", "timeout", "Connection timeout occurred")

    runner = CliRunner()
    result = runner.invoke(test_command)

    assert result.exit_code == 1
    assert "rss.timeout: Connection timeout occurred" in result.output
    assert "Hint: Request timed out" in result.output


def test_handle_rss_cli_with_connection_error():
    """Test the handle_rss_cli decorator with connection error."""
    @click.command()
    @handle_rss_cli
    def test_command():
        raise ServiceError("rss", "network", "Connection error")

    runner = CliRunner()
    result = runner.invoke(test_command)

    assert result.exit_code == 1
    assert "rss.network: Connection error" in result.output
    assert "Hint: Could not connect to RSS feed" in result.output


def test_handle_rss_cli_with_not_found_error():
    """Test the handle_rss_cli decorator with not found error."""
    @click.command()
    @handle_rss_cli
    def test_command():
        raise ServiceError("rss", "not_found", "Feed not found")

    runner = CliRunner()
    result = runner.invoke(test_command)

    assert result.exit_code == 1
    assert "rss.not_found: Feed not found" in result.output
    assert "Hint: RSS feed not found" in result.output


def test_handle_rss_cli_with_format_error():
    """Test the handle_rss_cli decorator with format error."""
    @click.command()
    @handle_rss_cli
    def test_command():
        raise ServiceError("rss", "parse", "Invalid format")

    runner = CliRunner()
    result = runner.invoke(test_command)

    assert result.exit_code == 1
    assert "rss.parse: Invalid format" in result.output
    assert "Hint: RSS feed format is invalid" in result.output


def test_handle_rss_cli_with_exists_error():
    """Test the handle_rss_cli decorator with exists error."""
    @click.command()
    @handle_rss_cli
    def test_command():
        raise ServiceError("rss", "validation", "Feed already exists")

    runner = CliRunner()
    result = runner.invoke(test_command)

    assert result.exit_code == 1
    assert "rss.validation: Feed already exists" in result.output
    assert "Hint: Input validation failed" in result.output


def test_handle_rss_cli_with_generic_error():
    """Test the handle_rss_cli decorator with generic error."""
    @click.command()
    @handle_rss_cli
    def test_command():
        raise ServiceError("rss", "unknown", "Some other error")

    runner = CliRunner()
    result = runner.invoke(test_command)

    assert result.exit_code == 1
    assert "rss.unknown: Some other error" in result.output
    assert "Hint: Unknown error occurred" in result.output


def test_handle_rss_cli_verbose_mode():
    """Test the handle_rss_cli decorator with verbose mode."""
    @click.command()
    @click.option("--verbose", is_flag=True)
    @handle_rss_cli
    def test_command(verbose):
        ctx = click.get_current_context()
        ctx.obj = {"verbose": verbose}
        original_error = ValueError("Original error")
        raise ServiceError("rss", "network", "Test RSS error with original", original=original_error)

    runner = CliRunner()
    result = runner.invoke(test_command, ["--verbose"])

    assert result.exit_code == 1
    assert "rss.network: Test RSS error with original" in result.output
    assert "Debug Information:" in result.output
    assert "original: Original error" in result.output


def test_handle_rss_cli_other_exception_verbose():
    """Test the handle_rss_cli decorator with other exceptions in verbose mode."""
    @click.command()
    @click.option("--verbose", is_flag=True)
    @handle_rss_cli
    def test_command(verbose):
        ctx = click.get_current_context()
        ctx.obj = {"verbose": verbose}
        raise ValueError("Test general error")

    runner = CliRunner()
    result = runner.invoke(test_command, ["--verbose"])

    assert result.exit_code == 1
    assert "Unexpected error: Test general error" in result.output
    assert "Traceback:" in result.output


def test_handle_rss_cli_other_exception():
    """Test the handle_rss_cli decorator with other exceptions."""
    @click.command()
    @handle_rss_cli
    def test_command():
        raise ValueError("Test general error")

    runner = CliRunner()
    result = runner.invoke(test_command)

    assert result.exit_code == 1
    assert "Unexpected error: Test general error" in result.output
    assert "Traceback:" not in result.output
"""Tests for the CLI application."""

import pytest
from click.testing import CliRunner

from local_newsifier.cli.main import cli


def test_cli_loads_without_error():
    """Test that the CLI application loads without errors."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "feeds" in result.output
    assert "db" in result.output
    

def test_cli_version():
    """Test that the CLI has a version."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert "0.1.0" in result.output


def test_feeds_group():
    """Test that the feeds command group loads without errors."""
    runner = CliRunner()
    result = runner.invoke(cli, ["feeds", "--help"])
    assert result.exit_code == 0
    assert "list" in result.output
    assert "add" in result.output
    assert "show" in result.output
    assert "remove" in result.output
    assert "process" in result.output
    assert "update" in result.output


def test_apify_config_group():
    """Test that the apify-config command group loads without errors."""
    runner = CliRunner()
    result = runner.invoke(cli, ["apify-config", "--help"])
    assert result.exit_code == 0
    assert "list" in result.output
    assert "add" in result.output
    assert "show" in result.output
    assert "remove" in result.output
    assert "update" in result.output
    assert "run" in result.output

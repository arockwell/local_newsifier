"""Tests for the Claude Code CLI commands."""

from pathlib import Path
from unittest.mock import mock_open, patch

import pytest
from click.testing import CliRunner

from local_newsifier.cli.commands.claude import claude_group


@pytest.fixture
def runner():
    """Create a CLI runner for testing."""
    return CliRunner()


@pytest.fixture
def temp_dir(tmp_path):
    """Create a temporary directory for the test."""
    return tmp_path


def test_claude_group_help(runner):
    """Test that the claude command group provides help."""
    result = runner.invoke(claude_group, ["--help"])
    assert result.exit_code == 0
    assert "Commands for managing Claude Code integration" in result.output
    assert "init" in result.output
    assert "validate" in result.output


def test_init_claude_code_simple(runner, temp_dir):
    """Test initializing Claude Code in a new directory with simple mocking."""
    with runner.isolated_filesystem():
        # Create a new directory for testing
        new_dir = Path(temp_dir) / "claude_workspace"
        new_dir.mkdir(exist_ok=True)

        # Run with skip-db to avoid actual database initialization
        with patch("local_newsifier.cli.commands.claude.shutil"):
            result = runner.invoke(claude_group, ["init", str(new_dir), "--skip-db"])

        # Just check basic success conditions
        assert result.exit_code == 0
        assert "Claude Code workspace initialized successfully" in result.output


@patch("local_newsifier.cli.commands.claude.shutil")
def test_init_claude_code_existing_nonempty_directory(mock_shutil, runner, temp_dir):
    """Test initializing Claude Code in an existing, non-empty directory without force."""
    # Create directory and a test file
    existing_dir = temp_dir / "existing_dir"
    existing_dir.mkdir()
    (existing_dir / "some_file.txt").write_text("test content")

    # Run the command
    result = runner.invoke(claude_group, ["init", str(existing_dir)])

    # Assertions
    assert result.exit_code != 0
    assert "not empty" in result.output
    assert "--force" in result.output


@patch("local_newsifier.cli.commands.claude.shutil")
def test_init_claude_code_force_flag(mock_shutil, runner, temp_dir):
    """Test initializing Claude Code with --force flag."""
    # Create directory and a test file
    existing_dir = temp_dir / "force_dir"
    existing_dir.mkdir()
    (existing_dir / "some_file.txt").write_text("test content")

    # Run the command
    with patch("builtins.open", mock_open()):
        with patch("pathlib.Path.write_text"):
            result = runner.invoke(
                claude_group, ["init", str(existing_dir), "--force", "--skip-db"]
            )

    # Assertions
    assert result.exit_code == 0
    assert "Copying project files..." in result.output
    assert "Claude Code workspace initialized successfully" in result.output


def test_validate_claude_code_good_setup(runner, temp_dir):
    """Test validating a correctly set up Claude Code workspace."""
    # Create a mock Claude Code workspace
    workspace_dir = temp_dir / "good_workspace"
    workspace_dir.mkdir()

    # Create required files
    (workspace_dir / "CLAUDE.md").write_text("# Claude Code")
    (workspace_dir / ".env").write_text(
        "POSTGRES_USER=test\nPOSTGRES_PASSWORD=test\n"
        "POSTGRES_HOST=localhost\nPOSTGRES_PORT=5432"
    )
    (workspace_dir / ".env.cursor").write_text("export CURSOR_DB_ID=12345678")
    (workspace_dir / "pyproject.toml").write_text("[tool.poetry]")

    # Create directory structure
    src_dir = workspace_dir / "src" / "local_newsifier" / "config"
    src_dir.mkdir(parents=True)
    (src_dir / "settings.py").write_text("# settings")

    # Run the command
    result = runner.invoke(claude_group, ["validate", "-d", str(workspace_dir)])

    # Assertions
    assert result.exit_code == 0
    assert "Validating Claude Code workspace" in result.output
    assert "Checking required files:" in result.output
    assert ".env.cursor contains CURSOR_DB_ID" in result.output
    assert "Claude Code workspace is properly configured" in result.output


def test_validate_claude_code_missing_files(runner, temp_dir):
    """Test validating a Claude Code workspace with missing files."""
    # Create a mock Claude Code workspace with issues
    workspace_dir = temp_dir / "bad_workspace"
    workspace_dir.mkdir()

    # Create only some required files
    (workspace_dir / ".env").write_text("POSTGRES_USER=test")

    # Run the command
    result = runner.invoke(claude_group, ["validate", "-d", str(workspace_dir)])

    # Assertions
    assert result.exit_code == 0  # Command succeeds even with validation failures
    assert "Validating Claude Code workspace" in result.output
    assert "✗ CLAUDE.md (missing)" in result.output
    assert "✗ .env.cursor file missing" in result.output
    assert "Claude Code workspace has configuration issues" in result.output

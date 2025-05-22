"""Tests for get_db_inspect_command provider."""

from local_newsifier.di.providers import get_db_inspect_command
from local_newsifier.cli.commands.db import inspect_record


def test_get_db_inspect_command_returns_inspect_record():
    """Ensure provider returns the inspect_record function."""
    result = get_db_inspect_command()
    assert result is inspect_record

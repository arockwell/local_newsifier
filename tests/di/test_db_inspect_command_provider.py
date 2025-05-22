"""Tests for get_db_inspect_command provider."""

from local_newsifier.cli.commands.db import inspect_record
from local_newsifier.di.providers import get_db_inspect_command
from tests.fixtures.event_loop import event_loop_fixture  # noqa: F401


def test_get_db_inspect_command_returns_inspect_record(event_loop_fixture):  # noqa: F811
    """Ensure provider returns the inspect_record function."""
    result = get_db_inspect_command()
    assert result is inspect_record

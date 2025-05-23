"""Tests for task persistence helper functions."""

from pathlib import Path
import pytest

from tests.fixtures.event_loop import event_loop_fixture

from local_newsifier.api.tasks.persistence import (
    TaskRecord,
    load_tasks,
    save_tasks,
)


class DummyManager:
    """Simple manager object for testing."""

    def __init__(self, path: Path):
        self.persistence_path = str(path)
        self.tasks: list[TaskRecord] = []


pytestmark = pytest.mark.usefixtures("event_loop_fixture")


def test_save_and_load_tasks(tmp_path, event_loop_fixture):
    """Ensure tasks are persisted and loaded correctly."""
    file_path = tmp_path / "tasks.json"
    manager = DummyManager(file_path)

    manager.tasks = [
        TaskRecord(
            id="1",
            type="process_article",
            description="Article 1",
            status="queued",
            submitted="2024-01-01T00:00:00Z",
        ),
        TaskRecord(
            id="2",
            type="fetch_rss",
            description="RSS",
            status="queued",
            submitted="2024-01-02T00:00:00Z",
        ),
    ]

    event_loop_fixture.run_until_complete(save_tasks(manager))

    manager.tasks = []

    event_loop_fixture.run_until_complete(load_tasks(manager))

    assert len(manager.tasks) == 2
    assert manager.tasks[0].id == "1"
    assert manager.tasks[1].type == "fetch_rss"

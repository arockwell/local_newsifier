import asyncio
import pytest

from local_newsifier.api.background_task_manager import BackgroundTaskManager
from tests.fixtures.event_loop import event_loop_fixture


async def _dummy_success(value: str) -> str:
    await asyncio.sleep(0.01)
    return value


async def _dummy_failure() -> None:
    await asyncio.sleep(0.01)
    raise RuntimeError("boom")


class TestBackgroundTaskManager:
    """Tests for the BackgroundTaskManager class."""

    def test_create_task(self, event_loop_fixture):
        manager = BackgroundTaskManager()

        async def run() -> tuple[str, str]:
            task_id = manager.create_task(_dummy_success, "ok")
            result = await manager.tasks[task_id]
            await asyncio.sleep(0)  # allow done callback
            return task_id, result

        task_id, result = event_loop_fixture.run_until_complete(run())
        assert result == "ok"
        assert task_id not in manager.tasks

    def test_run_task_success(self, event_loop_fixture):
        manager = BackgroundTaskManager()

        async def run() -> str:
            return await manager.run_task(_dummy_success, "done")

        result = event_loop_fixture.run_until_complete(run())
        assert result == "done"
        assert manager.tasks == {}

    def test_run_task_failure(self, event_loop_fixture):
        manager = BackgroundTaskManager()

        async def run():
            try:
                await manager.run_task(_dummy_failure)
            except RuntimeError as exc:  # noqa: B902
                return str(exc)
            return "no error"

        err = event_loop_fixture.run_until_complete(run())
        assert err == "boom"
        assert manager.tasks == {}

    def test_cleanup_cancels_tasks(self, event_loop_fixture):
        manager = BackgroundTaskManager()

        async def long():
            await asyncio.sleep(10)

        async def run() -> tuple[bool, int]:
            task_id = manager.create_task(long)
            task = manager.tasks[task_id]
            manager.cleanup()
            await asyncio.sleep(0)
            return task.cancelled(), len(manager.tasks)

        cancelled, remaining = event_loop_fixture.run_until_complete(run())
        assert cancelled
        assert remaining == 0

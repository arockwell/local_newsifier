import asyncio
import uuid
from typing import Any, Awaitable, Callable, Dict


class BackgroundTaskManager:
    """Simple manager for asyncio background tasks."""

    def __init__(self) -> None:
        self.tasks: Dict[str, asyncio.Task] = {}

    def create_task(self, func: Callable[..., Awaitable[Any]], *args: Any, **kwargs: Any) -> str:
        """Create and register an asyncio task.

        The task is automatically removed from the registry when done.
        """
        task_id = str(uuid.uuid4())
        task = asyncio.create_task(func(*args, **kwargs))
        self.tasks[task_id] = task

        def _cleanup(_: asyncio.Task, *, t_id: str = task_id) -> None:
            self.tasks.pop(t_id, None)

        task.add_done_callback(_cleanup)
        return task_id

    async def run_task(self, func: Callable[..., Awaitable[Any]], *args: Any, **kwargs: Any) -> Any:
        """Run a coroutine function and wait for completion.

        This registers the task and cleans it up when finished.
        """
        task_id = self.create_task(func, *args, **kwargs)
        task = self.tasks[task_id]
        return await task

    def cleanup(self) -> None:
        """Cancel all running tasks and clear the registry."""
        for task in list(self.tasks.values()):
            if not task.done():
                task.cancel()
        self.tasks.clear()

    def __del__(self) -> None:  # pragma: no cover - cleanup on GC
        self.cleanup()

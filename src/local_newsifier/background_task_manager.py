import logging
from typing import Any, Awaitable, Callable

logger = logging.getLogger(__name__)


class BackgroundTaskManager:
    """Simple background task runner.

    This placeholder executes the coroutine immediately and logs the
    start and completion of the task. A full implementation would
    persist progress in the database.
    """

    @staticmethod
    async def run_task(
        task_name: str, coro: Callable[..., Awaitable[Any]], *args, **kwargs
    ) -> Any:
        logger.info("Starting task %s", task_name)
        try:
            return await coro(*args, **kwargs)
        finally:
            logger.info("Completed task %s", task_name)

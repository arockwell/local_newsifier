"""Background task management for Local Newsifier API."""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class TaskStatus(str, Enum):
    """Enumeration of task states."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class TaskRecord:
    """Record representing a background task."""

    id: str
    func: Callable[..., Any]
    args: tuple
    kwargs: Dict[str, Any]
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    result: Optional[Any] = None
    error: Optional[str] = None


class BackgroundTaskManager:
    """Simple in-memory background task manager."""

    def __init__(self, persistence_hook: Optional[Callable[[Dict[str, TaskRecord]], None]] = None):
        self.tasks: Dict[str, TaskRecord] = {}
        self.persistence_hook = persistence_hook
        logger.debug("BackgroundTaskManager initialized")

    def create_task(self, task_id: str, func: Callable[..., Any], *args, **kwargs) -> TaskRecord:
        """Register a new task without starting it."""
        record = TaskRecord(id=task_id, func=func, args=args, kwargs=kwargs)
        self.tasks[task_id] = record
        logger.info("Task %s created", task_id)
        self._persist()
        return record

    def start_task(self, task_id: str) -> None:
        """Mark a task as started."""
        task = self.tasks.get(task_id)
        if not task:
            raise KeyError(task_id)
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.utcnow()
        logger.info("Task %s started", task_id)
        self._persist()

    def run_task(self, task_id: str) -> None:
        """Execute a registered task synchronously."""
        task = self.tasks.get(task_id)
        if not task:
            raise KeyError(task_id)
        if task.status != TaskStatus.PENDING:
            logger.warning("Task %s run requested but status is %s", task_id, task.status)
            return
        self.start_task(task_id)
        try:
            task.result = task.func(*task.args, **task.kwargs)
            task.status = TaskStatus.COMPLETED
            logger.info("Task %s completed", task_id)
        except Exception as exc:  # noqa: BLE001
            task.error = str(exc)
            task.status = TaskStatus.FAILED
            logger.exception("Task %s failed", task_id)
        finally:
            task.finished_at = datetime.utcnow()
            self._persist()

    def get_task(self, task_id: str) -> Optional[TaskRecord]:
        """Retrieve a task by ID."""
        return self.tasks.get(task_id)

    def list_tasks(self) -> Dict[str, TaskRecord]:
        """Return all tasks."""
        return dict(self.tasks)

    def clean_old_tasks(self, older_than: timedelta) -> None:
        """Remove tasks finished before the given age."""
        cutoff = datetime.utcnow() - older_than
        to_delete = [tid for tid, rec in self.tasks.items() if rec.finished_at and rec.finished_at < cutoff]
        for tid in to_delete:
            del self.tasks[tid]
            logger.debug("Task %s removed during cleanup", tid)
        if to_delete:
            self._persist()

    def _persist(self) -> None:
        if self.persistence_hook:
            try:
                self.persistence_hook(self.tasks)
            except Exception:  # noqa: BLE001
                logger.exception("Error during persistence hook")

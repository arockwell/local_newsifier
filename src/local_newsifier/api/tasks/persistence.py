# Task persistence helpers for API tasks.

from __future__ import annotations

import asyncio
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import List

# Global lock to prevent concurrent file access
_TASK_FILE_LOCK = asyncio.Lock()


@dataclass
class TaskRecord:
    """Simple representation of a task for persistence."""

    id: str
    type: str
    description: str
    status: str
    submitted: str  # ISO formatted datetime string


async def _read_json(path: Path) -> List[dict]:
    return await asyncio.to_thread(_sync_read_json, path)


def _sync_read_json(path: Path) -> List[dict]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


async def _write_json(path: Path, data: List[dict]) -> None:
    await asyncio.to_thread(_sync_write_json, path, data)


def _sync_write_json(path: Path, data: List[dict]) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


async def load_task_records(file_path: str | Path) -> List[TaskRecord]:
    """Load task records from a JSON file."""
    path = Path(file_path)
    if not path.exists():
        return []

    async with _TASK_FILE_LOCK:
        raw = await _read_json(path)
        return [TaskRecord(**item) for item in raw]


async def save_task_records(file_path: str | Path, tasks: List[TaskRecord]) -> None:
    """Save task records to a JSON file."""
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = [asdict(t) for t in tasks]

    async with _TASK_FILE_LOCK:
        await _write_json(path, data)


async def load_tasks(manager) -> List[TaskRecord]:
    """Helper to load tasks using a manager with a persistence_path attribute."""
    tasks = await load_task_records(manager.persistence_path)
    manager.tasks = tasks
    return tasks


async def save_tasks(manager) -> None:
    """Helper to save tasks using a manager with a persistence_path attribute."""
    tasks: List[TaskRecord] = getattr(manager, "tasks", [])
    await save_task_records(manager.persistence_path, tasks)

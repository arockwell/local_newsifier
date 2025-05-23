import json
import os
from typing import Any, Dict, List


class BackgroundTaskManager:
    """Simple manager for persisting background tasks to disk."""

    def __init__(self, storage_path: str = "background_tasks.json") -> None:
        self.storage_path = storage_path
        self.tasks: List[Dict[str, Any]] = []

    async def restore_tasks(self) -> None:
        """Load persisted tasks from disk if the file exists."""
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.tasks = data.get("tasks", [])
            except Exception:
                # If loading fails, start with an empty task list
                self.tasks = []

    async def save_tasks(self) -> None:
        """Persist current tasks to disk."""
        try:
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump({"tasks": self.tasks}, f)
        except Exception:
            # Saving errors are ignored for now
            pass

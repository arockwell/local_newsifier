"""Task management API router.

This router exposes simple endpoints for creating and tracking background
jobs executed using FastAPI's ``BackgroundTasks`` utility. Tasks are stored in a
process-local dictionary and are not persisted between restarts.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Path,
    Query,
    Request,
)
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from local_newsifier.api.dependencies import (
    get_templates,
)
from local_newsifier.config.settings import settings

router = APIRouter(prefix="/tasks", tags=["tasks"])


class TaskRecord(BaseModel):
    """Representation of a background task."""

    id: str
    name: str
    status: str
    created_at: datetime
    result: Optional[Any] = None
    error: Optional[str] = None


# In-memory task storage
TASK_STORE: Dict[str, TaskRecord] = {}


def _run_process_article(task_id: str, article_id: int) -> None:
    """Background worker for ``process_article``."""
    record = TASK_STORE[task_id]
    record.status = "running"
    try:
        from local_newsifier.tasks import process_article

        record.result = process_article.run(article_id)
        record.status = "completed"
    except Exception as exc:  # pragma: no cover - defensive
        record.status = "failed"
        record.error = str(exc)


def _run_fetch_rss_feeds(task_id: str, feed_urls: List[str]) -> None:
    """Background worker for ``fetch_rss_feeds``."""
    record = TASK_STORE[task_id]
    record.status = "running"
    try:
        from local_newsifier.tasks import fetch_rss_feeds

        record.result = fetch_rss_feeds.run(feed_urls)
        record.status = "completed"
    except Exception as exc:  # pragma: no cover - defensive
        record.status = "failed"
        record.error = str(exc)


@router.get("/dashboard", response_class=HTMLResponse)
async def tasks_dashboard(
    request: Request,
    templates: Jinja2Templates = Depends(get_templates),
):
    """Render the task management dashboard."""
    return templates.TemplateResponse(
        "tasks_dashboard.html",
        {
            "request": request,
            "title": "Task Dashboard",
            "rss_feed_urls": settings.RSS_FEED_URLS,
        },
    )


@router.get("", response_model=List[TaskRecord])
async def list_tasks(
    status: Optional[str] = Query(None, description="Filter tasks by status"),
    limit: int = Query(100, gt=0, le=1000, description="Maximum number of records"),
) -> List[TaskRecord]:
    """Return tasks with optional status filtering."""
    records = list(TASK_STORE.values())
    if status:
        records = [t for t in records if t.status == status]
    records.sort(key=lambda r: r.created_at, reverse=True)
    return records[:limit]


@router.get("/{task_id}", response_model=TaskRecord)
async def get_task(task_id: str = Path(..., description="Task identifier")) -> TaskRecord:
    """Retrieve a single task."""
    task = TASK_STORE.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.post("/{task_name}", response_model=TaskRecord)
async def create_task(
    background_tasks: BackgroundTasks,
    task_name: str = Path(..., description="Name of the task to run"),
    article_id: Optional[int] = Query(None, description="Article ID for process_article"),
    feed_urls: Optional[List[str]] = Query(None, description="Feed URLs for fetch_rss_feeds"),
) -> TaskRecord:
    """Create and queue a new task."""
    if task_name not in {"process_article", "fetch_rss_feeds"}:
        raise HTTPException(status_code=404, detail="Unknown task")

    task_id = str(uuid4())
    record = TaskRecord(
        id=task_id,
        name=task_name,
        status="queued",
        created_at=datetime.now(timezone.utc),
    )
    TASK_STORE[task_id] = record

    if task_name == "process_article":
        if article_id is None:
            raise HTTPException(status_code=400, detail="article_id required")
        background_tasks.add_task(_run_process_article, task_id, article_id)
    else:  # fetch_rss_feeds
        urls = feed_urls or settings.RSS_FEED_URLS
        background_tasks.add_task(_run_fetch_rss_feeds, task_id, urls)

    return record


@router.delete("/{task_id}", response_model=TaskRecord)
async def cancel_task(task_id: str = Path(..., description="Task identifier")) -> TaskRecord:
    """Mark a task as cancelled if it has not finished."""
    task = TASK_STORE.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.status in {"completed", "failed", "cancelled"}:
        return task
    task.status = "cancelled"
    return task


"""FastAPI routes for background task processing.

Replaces Celery task endpoints with FastAPI Background Tasks.
"""

import uuid
from datetime import datetime
from typing import Annotated, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session

from local_newsifier.di.providers import get_session
from local_newsifier.tasks_sync import fetch_rss_feeds_sync, process_article_sync

router = APIRouter(prefix="/background-tasks", tags=["background-tasks"])


# In-memory task storage (for demo purposes - use Redis or DB in production)
task_status: Dict[str, Dict] = {}


class TaskResponse(BaseModel):
    """Response model for task creation."""

    task_id: str
    status: str
    message: str


class TaskStatus(BaseModel):
    """Task status information."""

    task_id: str
    status: str
    created_at: datetime
    updated_at: datetime
    result: Optional[Dict] = None
    error: Optional[str] = None


def update_task_status(
    task_id: str, status: str, result: Optional[Dict] = None, error: Optional[str] = None
):
    """Update task status in storage."""
    if task_id in task_status:
        task_status[task_id].update(
            {"status": status, "updated_at": datetime.now(), "result": result, "error": error}
        )


def process_article_background(task_id: str, article_id: int):
    """Background task wrapper for article processing."""
    update_task_status(task_id, "processing")
    try:
        result = process_article_sync(article_id)
        update_task_status(task_id, "completed", result=result)
    except Exception as e:
        update_task_status(task_id, "failed", error=str(e))


def fetch_feeds_background(
    task_id: str, feed_urls: Optional[List[str]] = None, process_articles: bool = True
):
    """Background task wrapper for RSS feed fetching."""
    update_task_status(task_id, "processing")
    try:
        result = fetch_rss_feeds_sync(feed_urls, process_articles)
        update_task_status(task_id, "completed", result=result)
    except Exception as e:
        update_task_status(task_id, "failed", error=str(e))


@router.post("/process-article/{article_id}", response_model=TaskResponse)
def process_article(
    article_id: int,
    background_tasks: BackgroundTasks,
    session: Annotated[Session, Depends(get_session)],
):
    """
    Process an article in the background.

    Args:
        article_id: ID of the article to process
        background_tasks: FastAPI background tasks
        session: Database session

    Returns:
        TaskResponse with task ID and initial status
    """
    # Generate task ID
    task_id = str(uuid.uuid4())

    # Initialize task status
    task_status[task_id] = {
        "task_id": task_id,
        "status": "pending",
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "result": None,
        "error": None,
    }

    # Add to background tasks
    background_tasks.add_task(process_article_background, task_id, article_id)

    return TaskResponse(
        task_id=task_id, status="pending", message=f"Article {article_id} queued for processing"
    )


@router.post("/fetch-feeds", response_model=TaskResponse)
def fetch_feeds(
    background_tasks: BackgroundTasks,
    feed_urls: Optional[List[str]] = None,
    process_articles: bool = True,
):
    """
    Fetch RSS feeds in the background.

    Args:
        background_tasks: FastAPI background tasks
        feed_urls: Optional list of feed URLs to process
        process_articles: Whether to process articles after fetching

    Returns:
        TaskResponse with task ID and initial status
    """
    # Generate task ID
    task_id = str(uuid.uuid4())

    # Initialize task status
    task_status[task_id] = {
        "task_id": task_id,
        "status": "pending",
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "result": None,
        "error": None,
    }

    # Add to background tasks
    background_tasks.add_task(fetch_feeds_background, task_id, feed_urls, process_articles)

    return TaskResponse(task_id=task_id, status="pending", message="Feed fetching queued")


@router.get("/status/{task_id}", response_model=TaskStatus)
def get_task_status(task_id: str):
    """
    Get the status of a background task.

    Args:
        task_id: Task ID to check

    Returns:
        TaskStatus with current task information
    """
    if task_id not in task_status:
        raise HTTPException(status_code=404, detail="Task not found")

    return TaskStatus(**task_status[task_id])


@router.get("/active", response_model=List[TaskStatus])
def get_active_tasks():
    """
    Get all active (pending or processing) tasks.

    Returns:
        List of active task statuses
    """
    active_tasks = [
        TaskStatus(**task)
        for task in task_status.values()
        if task["status"] in ["pending", "processing"]
    ]
    return active_tasks


@router.get("/all", response_model=List[TaskStatus])
def get_all_tasks(limit: int = 100):
    """
    Get all tasks (limited to most recent).

    Args:
        limit: Maximum number of tasks to return

    Returns:
        List of task statuses
    """
    # Sort by created_at descending and limit
    sorted_tasks = sorted(task_status.values(), key=lambda x: x["created_at"], reverse=True)[:limit]

    return [TaskStatus(**task) for task in sorted_tasks]


@router.delete("/cleanup")
def cleanup_completed_tasks():
    """
    Clean up completed and failed tasks from memory.

    Returns:
        Number of tasks cleaned up
    """
    completed_tasks = [
        task_id
        for task_id, task in task_status.items()
        if task["status"] in ["completed", "failed"]
    ]

    for task_id in completed_tasks:
        del task_status[task_id]

    return {
        "cleaned_up": len(completed_tasks),
        "message": f"Removed {len(completed_tasks)} completed/failed tasks",
    }

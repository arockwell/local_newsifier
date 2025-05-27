"""API router for Celery task management.

This module provides endpoints for submitting, checking, and managing asynchronous tasks.
"""

from typing import List, Optional

from celery.result import AsyncResult
from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from local_newsifier.api.dependencies import (get_article_service, get_rss_feed_service,
                                              get_templates)
from local_newsifier.celery_app import app as celery_app
from local_newsifier.config.settings import settings
from local_newsifier.services.article_service import ArticleService
from local_newsifier.services.rss_feed_service import RSSFeedService
from local_newsifier.tasks import fetch_rss_feeds, process_article

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("/", response_class=HTMLResponse)
async def tasks_dashboard(request: Request, templates: Jinja2Templates = Depends(get_templates)):
    """
    Task management dashboard.

    Provides a web interface for submitting and monitoring tasks.
    """
    return templates.TemplateResponse(
        "tasks_dashboard.html",
        {
            "request": request,
            "title": "Task Dashboard",
            "rss_feed_urls": settings.RSS_FEED_URLS,
        },
    )


@router.post("/process-article/{article_id}")
async def process_article_endpoint(
    article_id: int = Path(..., title="Article ID", description="ID of the article to process"),
    article_service: ArticleService = Depends(get_article_service),
):
    """
    Submit a task to process an article asynchronously.

    Args:
        article_id: ID of the article to process

    Returns:
        Task information including task ID
    """
    # Verify article exists
    article = article_service.get_article(article_id)
    if not article:
        raise HTTPException(status_code=404, detail=f"Article with ID {article_id} not found")

    # Submit task
    task = process_article.delay(article_id)

    return {
        "task_id": task.id,
        "article_id": article_id,
        "article_title": article.title,
        "status": "queued",
        "task_url": f"/tasks/status/{task.id}",
    }


@router.post("/fetch-rss-feeds")
async def fetch_rss_feeds_endpoint(
    feed_urls: Optional[List[str]] = Query(None, description="List of RSS feed URLs to process"),
    rss_feed_service: RSSFeedService = Depends(get_rss_feed_service),
):
    """
    Submit a task to fetch articles from RSS feeds.

    Args:
        feed_urls: Optional list of RSS feed URLs.
            If not provided, uses default feeds from settings.
        rss_feed_service: RSS feed service provided by dependency injection

    Returns:
        Task information including task ID
    """
    if not feed_urls:
        feed_urls = settings.RSS_FEED_URLS

    task = fetch_rss_feeds.delay(feed_urls)

    return {
        "task_id": task.id,
        "feed_count": len(feed_urls),
        "status": "queued",
        "task_url": f"/tasks/status/{task.id}",
    }


@router.get("/status/{task_id}")
async def get_task_status(
    task_id: str = Path(..., title="Task ID", description="ID of the task to check status for")
):
    """
    Check the status of a task.

    Args:
        task_id: ID of the task to check

    Returns:
        Task status information
    """
    task_result = AsyncResult(task_id, app=celery_app)

    result = {
        "task_id": task_id,
        "status": task_result.status,
    }

    # Add additional info based on task state
    if task_result.successful():
        result["result"] = task_result.result
    elif task_result.failed():
        result["error"] = str(task_result.result)
    elif task_result.status == "PROGRESS":
        result["progress"] = task_result.info

    return result


@router.delete("/cancel/{task_id}")
async def cancel_task(
    task_id: str = Path(..., title="Task ID", description="ID of the task to cancel")
):
    """
    Cancel a running task.

    Args:
        task_id: ID of the task to cancel

    Returns:
        Confirmation message
    """
    task_result = AsyncResult(task_id, app=celery_app)

    if task_result.successful() or task_result.failed():
        return {"message": f"Task {task_id} already completed"}

    # Attempt to revoke the task
    celery_app.control.revoke(task_id, terminate=True)

    return {"message": f"Task {task_id} revoke signal sent"}

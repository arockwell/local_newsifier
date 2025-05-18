"""
API router for task utilities.
Celery support has been removed, so tasks run synchronously within the request cycle.
"""

from typing import Annotated, Dict, List, Optional, Union

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from local_newsifier.api.dependencies import (
    get_templates,
    get_article_service,
    get_rss_feed_service,
)
from local_newsifier.config.settings import settings
from local_newsifier.services.article_service import ArticleService
from local_newsifier.services.rss_feed_service import RSSFeedService
from local_newsifier.tasks import (
    fetch_rss_feeds,
    process_article,
)

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("/", response_class=HTMLResponse)
async def tasks_dashboard(
    request: Request, 
    templates: Jinja2Templates = Depends(get_templates)
):
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
    """Process an article and return the result."""
    # Verify article exists
    article = article_service.get_article(article_id)
    if not article:
        raise HTTPException(status_code=404, detail=f"Article with ID {article_id} not found")

    result = process_article(article_id)
    return result


@router.post("/fetch-rss-feeds")
async def fetch_rss_feeds_endpoint(
    feed_urls: Optional[List[str]] = Query(None, description="List of RSS feed URLs to process"),
    rss_feed_service: RSSFeedService = Depends(get_rss_feed_service),
):
    """Fetch articles from RSS feeds and return the result."""
    if not feed_urls:
        feed_urls = settings.RSS_FEED_URLS

    result = fetch_rss_feeds(feed_urls)
    return result



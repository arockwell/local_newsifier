"""Database inspection and management router."""

from datetime import datetime
from typing import Annotated, Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, text
from sqlmodel import Session, select

from local_newsifier.api.dependencies import get_session
from local_newsifier.di.providers import (get_article_crud, get_entity_crud,
                                          get_feed_processing_log_crud, get_rss_feed_crud)
from local_newsifier.models.article import Article
from local_newsifier.models.entity import Entity
from local_newsifier.models.rss_feed import RSSFeed, RSSFeedProcessingLog

router = APIRouter(
    prefix="/db",
    tags=["database"],
    responses={404: {"description": "Not found"}},
)


def format_datetime(dt) -> Optional[str]:
    """Format a datetime object for display."""
    if not dt:
        return None
    return dt.strftime("%Y-%m-%d %H:%M:%S")


class PurgeDuplicatesRequest(BaseModel):
    """Request model for purging duplicates."""

    dry_run: bool = True


@router.get("/stats")
async def get_db_stats(session: Annotated[Session, Depends(get_session)]) -> Dict[str, Any]:
    """Get database statistics for all major tables."""
    stats = {}

    # Article stats
    article_count = session.exec(select(func.count()).select_from(Article)).one()
    latest_article = session.exec(
        select(Article).order_by(Article.created_at.desc()).limit(1)
    ).first()
    oldest_article = session.exec(select(Article).order_by(Article.created_at).limit(1)).first()

    # RSS Feed stats
    feed_count = session.exec(select(func.count()).select_from(RSSFeed)).one()
    active_feed_count = session.exec(
        select(func.count()).select_from(RSSFeed).where(RSSFeed.is_active)
    ).one()

    # RSSFeedProcessingLog stats
    processing_log_count = session.exec(
        select(func.count()).select_from(RSSFeedProcessingLog)
    ).one()

    # Entity stats
    entity_count = session.exec(select(func.count()).select_from(Entity)).one()

    stats["articles"] = {
        "count": article_count,
        "latest": format_datetime(latest_article.created_at) if latest_article else None,
        "oldest": format_datetime(oldest_article.created_at) if oldest_article else None,
    }

    stats["rss_feeds"] = {
        "count": feed_count,
        "active": active_feed_count,
        "inactive": feed_count - active_feed_count,
    }

    stats["feed_processing_logs"] = {
        "count": processing_log_count,
    }

    stats["entities"] = {
        "count": entity_count,
    }

    return stats


@router.get("/duplicates")
async def get_duplicates(
    limit: int = 10, session: Annotated[Session, Depends(get_session)] = None
) -> List[Dict[str, Any]]:
    """Find duplicate articles (same URL) and show details."""
    # Query to find duplicate URLs
    duplicate_urls = session.exec(
        select(Article.url, func.count(Article.id).label("count"))
        .group_by(Article.url)
        .having(func.count(Article.id) > 1)
        .order_by(text("count DESC"))
        .limit(limit)
    ).all()

    if not duplicate_urls:
        return []

    # Get detailed information about the duplicates
    results = []
    for url, count in duplicate_urls:
        duplicates = session.exec(
            select(Article).where(Article.url == url).order_by(Article.created_at)
        ).all()

        duplicate_info = {"url": url, "count": count, "articles": []}

        for article in duplicates:
            duplicate_info["articles"].append(
                {
                    "id": article.id,
                    "title": (
                        article.title[:50] + "..."
                        if article.title and len(article.title) > 50
                        else article.title
                    ),
                    "created_at": format_datetime(article.created_at),
                    "status": article.status,
                    "content_len": len(article.content) if article.content else 0,
                }
            )

        results.append(duplicate_info)

    return results


@router.get("/articles")
async def list_articles(
    source: Optional[str] = None,
    status: Optional[str] = None,
    before: Optional[str] = None,
    after: Optional[str] = None,
    limit: int = 10,
    session: Annotated[Session, Depends(get_session)] = None,
) -> List[Dict[str, Any]]:
    """List articles with filtering options."""
    # Build the query with filters
    query = select(Article)

    if source:
        query = query.where(Article.source == source)

    if status:
        query = query.where(Article.status == status)

    if before:
        try:
            before_date = datetime.strptime(before, "%Y-%m-%d")
            query = query.where(Article.created_at < before_date)
        except ValueError:
            raise HTTPException(
                status_code=400, detail="Invalid date format for 'before'. Use YYYY-MM-DD"
            )

    if after:
        try:
            after_date = datetime.strptime(after, "%Y-%m-%d")
            query = query.where(Article.created_at > after_date)
        except ValueError:
            raise HTTPException(
                status_code=400, detail="Invalid date format for 'after'. Use YYYY-MM-DD"
            )

    # Order by most recent first and apply limit
    query = query.order_by(Article.created_at.desc()).limit(limit)

    # Execute query
    articles = session.exec(query).all()

    # Format the results
    results = []
    for article in articles:
        results.append(
            {
                "id": article.id,
                "title": article.title,
                "url": article.url,
                "source": article.source,
                "status": article.status,
                "created_at": format_datetime(article.created_at),
                "content_len": len(article.content) if article.content else 0,
            }
        )

    return results


@router.get("/inspect/{table}/{id}")
async def inspect_record(
    table: str,
    id: int,
    session: Annotated[Session, Depends(get_session)] = None,
    article_crud: Annotated[Any, Depends(get_article_crud)] = None,
    rss_feed_crud: Annotated[Any, Depends(get_rss_feed_crud)] = None,
    entity_crud: Annotated[Any, Depends(get_entity_crud)] = None,
    feed_processing_log_crud: Annotated[Any, Depends(get_feed_processing_log_crud)] = None,
) -> Dict[str, Any]:
    """Inspect a specific database record in detail."""
    if table not in ["article", "rss_feed", "feed_log", "entity"]:
        raise HTTPException(status_code=400, detail=f"Invalid table: {table}")

    result = None

    if table == "article":
        article = article_crud.get(session, id=id)
        if not article:
            raise HTTPException(status_code=404, detail=f"Article with ID {id} not found")

        result = {
            "id": article.id,
            "title": article.title,
            "url": article.url,
            "source": article.source,
            "status": article.status,
            "created_at": format_datetime(article.created_at),
            "updated_at": format_datetime(article.updated_at),
            "published_at": format_datetime(article.published_at) if article.published_at else None,
            "scraped_at": format_datetime(article.scraped_at) if article.scraped_at else None,
            "content_len": len(article.content) if article.content else 0,
            "content_preview": (
                (article.content[:200] + "...")
                if article.content and len(article.content) > 200
                else article.content
            ),
        }

    elif table == "rss_feed":
        feed = rss_feed_crud.get(session, id=id)
        if not feed:
            raise HTTPException(status_code=404, detail=f"RSS Feed with ID {id} not found")

        # Get processing logs for this feed
        logs = session.exec(
            select(RSSFeedProcessingLog)
            .where(RSSFeedProcessingLog.feed_id == id)
            .order_by(RSSFeedProcessingLog.started_at.desc())
            .limit(5)
        ).all()

        log_data = []
        for log in logs:
            log_data.append(
                {
                    "id": log.id,
                    "status": log.status,
                    "started_at": format_datetime(log.started_at),
                    "completed_at": format_datetime(log.completed_at) if log.completed_at else None,
                    "articles_found": log.articles_found,
                    "articles_added": log.articles_added,
                    "error_message": log.error_message,
                }
            )

        result = {
            "id": feed.id,
            "name": feed.name,
            "url": feed.url,
            "description": feed.description,
            "is_active": feed.is_active,
            "created_at": format_datetime(feed.created_at),
            "updated_at": format_datetime(feed.updated_at),
            "last_fetched_at": (
                format_datetime(feed.last_fetched_at) if feed.last_fetched_at else None
            ),
            "recent_logs": log_data,
        }

    elif table == "feed_log":
        log = feed_processing_log_crud.get(session, id=id)
        if not log:
            raise HTTPException(
                status_code=404, detail=f"Feed Processing Log with ID {id} not found"
            )

        result = {
            "id": log.id,
            "feed_id": log.feed_id,
            "status": log.status,
            "started_at": format_datetime(log.started_at),
            "completed_at": format_datetime(log.completed_at) if log.completed_at else None,
            "articles_found": log.articles_found,
            "articles_added": log.articles_added,
            "error_message": log.error_message,
        }

    elif table == "entity":
        entity = entity_crud.get(session, id=id)
        if not entity:
            raise HTTPException(status_code=404, detail=f"Entity with ID {id} not found")

        result = {
            "id": entity.id,
            "name": entity.name,
            "entity_type": entity.entity_type,
            "created_at": format_datetime(entity.created_at),
            "updated_at": format_datetime(entity.updated_at),
        }

    return result


@router.post("/purge-duplicates")
async def purge_duplicates(
    request: PurgeDuplicatesRequest,
    session: Annotated[Session, Depends(get_session)] = None,
    article_crud: Annotated[Any, Depends(get_article_crud)] = None,
) -> Dict[str, Any]:
    """Remove duplicate articles, keeping the oldest version."""
    # Query to find duplicate URLs
    duplicate_urls = session.exec(
        select(Article.url, func.count(Article.id).label("count"))
        .group_by(Article.url)
        .having(func.count(Article.id) > 1)
    ).all()

    if not duplicate_urls:
        return {"total_urls": 0, "total_removed": 0, "dry_run": request.dry_run, "details": []}

    # Process each set of duplicates
    results = []
    total_removed = 0

    for url, count in duplicate_urls:
        duplicates = session.exec(
            select(Article).where(Article.url == url).order_by(Article.created_at)
        ).all()

        # Keep the oldest (first) article
        to_keep = duplicates[0]
        to_remove = duplicates[1:]

        result = {
            "url": url,
            "kept_id": to_keep.id,
            "removed_ids": [a.id for a in to_remove],
            "removed_count": len(to_remove),
        }
        results.append(result)
        total_removed += len(to_remove)

        # Remove duplicates if not a dry run
        if not request.dry_run:
            for article in to_remove:
                article_crud.remove(session, id=article.id)

    # Commit changes if not a dry run
    if not request.dry_run:
        session.commit()

    return {
        "total_urls": len(results),
        "total_removed": total_removed,
        "dry_run": request.dry_run,
        "details": results,
    }

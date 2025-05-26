"""RSS Feeds API router."""

import logging
from typing import Annotated, Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlmodel import Session

from local_newsifier.api.dependencies import get_session
from local_newsifier.di.providers import get_rss_feed_service

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/feeds",
    tags=["feeds"],
    responses={404: {"description": "Not found"}},
)


class FeedCreate(BaseModel):
    """Request model for creating a feed."""

    url: str
    name: Optional[str] = None
    description: Optional[str] = None


class FeedUpdate(BaseModel):
    """Request model for updating a feed."""

    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class FeedResponse(BaseModel):
    """Response model for a feed."""

    id: int
    name: str
    url: str
    description: Optional[str]
    is_active: bool
    created_at: str
    updated_at: str
    last_fetched_at: Optional[str]


def format_datetime(dt) -> Optional[str]:
    """Format a datetime object for display."""
    if not dt:
        return None
    return dt.strftime("%Y-%m-%d %H:%M:%S")


@router.get("/", response_model=List[Dict[str, Any]])
async def list_feeds(
    active_only: bool = Query(False, description="Show only active feeds"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of feeds to return"),
    skip: int = Query(0, ge=0, description="Number of feeds to skip"),
    session: Annotated[Session, Depends(get_session)] = None,
    rss_feed_service: Annotated[Any, Depends(get_rss_feed_service)] = None,
) -> List[Dict[str, Any]]:
    """List RSS feeds with optional filtering."""
    try:
        feeds = rss_feed_service.list_feeds(skip=skip, limit=limit, active_only=active_only)
        return feeds
    except Exception as e:
        logger.error(f"Error listing feeds: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{feed_id}", response_model=Dict[str, Any])
async def get_feed(
    feed_id: int,
    session: Annotated[Session, Depends(get_session)] = None,
    rss_feed_service: Annotated[Any, Depends(get_rss_feed_service)] = None,
) -> Dict[str, Any]:
    """Get a specific RSS feed by ID."""
    try:
        feed = rss_feed_service.get_feed(feed_id)
        if not feed:
            raise HTTPException(status_code=404, detail=f"Feed with ID {feed_id} not found")

        # Get processing logs
        logs = rss_feed_service.get_feed_processing_logs(feed_id, limit=5)

        # Format response
        result = {
            "id": feed["id"],
            "name": feed["name"],
            "url": feed["url"],
            "description": feed.get("description"),
            "is_active": feed["is_active"],
            "created_at": feed["created_at"],
            "updated_at": feed["updated_at"],
            "last_fetched_at": feed.get("last_fetched_at"),
            "recent_logs": logs,
        }

        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting feed {feed_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=Dict[str, Any])
async def create_feed(
    feed_data: FeedCreate,
    session: Annotated[Session, Depends(get_session)] = None,
    rss_feed_service: Annotated[Any, Depends(get_rss_feed_service)] = None,
) -> Dict[str, Any]:
    """Create a new RSS feed."""
    try:
        feed = rss_feed_service.create_feed(
            url=feed_data.url,
            name=feed_data.name or feed_data.url,  # Use URL as default name
            description=feed_data.description,
        )
        return feed
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating feed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{feed_id}", response_model=Dict[str, Any])
async def update_feed(
    feed_id: int,
    feed_update: FeedUpdate,
    session: Annotated[Session, Depends(get_session)] = None,
    rss_feed_service: Annotated[Any, Depends(get_rss_feed_service)] = None,
) -> Dict[str, Any]:
    """Update an existing RSS feed."""
    try:
        # Build update data
        update_data = {}
        if feed_update.name is not None:
            update_data["name"] = feed_update.name
        if feed_update.description is not None:
            update_data["description"] = feed_update.description
        if feed_update.is_active is not None:
            update_data["is_active"] = feed_update.is_active

        feed = rss_feed_service.update_feed(feed_id, **update_data)
        if not feed:
            raise HTTPException(status_code=404, detail=f"Feed with ID {feed_id} not found")

        return feed
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating feed {feed_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{feed_id}")
async def delete_feed(
    feed_id: int,
    session: Annotated[Session, Depends(get_session)] = None,
    rss_feed_service: Annotated[Any, Depends(get_rss_feed_service)] = None,
) -> Dict[str, str]:
    """Delete an RSS feed."""
    try:
        success = rss_feed_service.remove_feed(feed_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Feed with ID {feed_id} not found")

        return {"message": f"Feed {feed_id} deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting feed {feed_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{feed_id}/process")
async def process_feed(
    feed_id: int,
    session: Annotated[Session, Depends(get_session)] = None,
    rss_feed_service: Annotated[Any, Depends(get_rss_feed_service)] = None,
) -> Dict[str, Any]:
    """Process a specific RSS feed."""
    try:
        result = rss_feed_service.process_feed(feed_id)
        if not result:
            raise HTTPException(status_code=404, detail=f"Feed with ID {feed_id} not found")

        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing feed {feed_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/process-all")
async def process_all_feeds(
    session: Annotated[Session, Depends(get_session)] = None,
    rss_feed_service: Annotated[Any, Depends(get_rss_feed_service)] = None,
) -> Dict[str, Any]:
    """Process all active RSS feeds."""
    try:
        # Get all active feeds
        feeds = rss_feed_service.list_feeds(active_only=True)

        results = []
        for feed in feeds:
            try:
                result = rss_feed_service.process_feed(feed["id"])
                results.append(result)
            except Exception as e:
                logger.error(f"Error processing feed {feed['id']}: {str(e)}")
                results.append(
                    {
                        "status": "error",
                        "feed_id": feed["id"],
                        "feed_name": feed["name"],
                        "error": str(e),
                    }
                )

        return {"processed": len(results), "results": results}
    except Exception as e:
        logger.error(f"Error processing all feeds: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

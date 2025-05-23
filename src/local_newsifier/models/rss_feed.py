"""
Database models for RSS feeds.
"""

from datetime import datetime, timezone
from typing import List, Optional

from sqlmodel import Field, Relationship, SQLModel


class RSSFeed(SQLModel, table=True):
    """Model for storing RSS feed information."""
    
    __tablename__ = "rss_feeds"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    url: str = Field(index=True, unique=True)
    name: str
    description: Optional[str] = None
    is_active: bool = Field(default=True)
    last_fetched_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Relationships
    processing_logs: List["RSSFeedProcessingLog"] = Relationship(
        back_populates="feed",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )


class RSSFeedProcessingLog(SQLModel, table=True):
    """Model for tracking RSS feed processing history."""
    
    __tablename__ = "rss_feed_processing_logs"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    feed_id: int = Field(foreign_key="rss_feeds.id", index=True)
    status: str = Field(index=True)  # success, error, etc.
    articles_found: int = Field(default=0)
    articles_added: int = Field(default=0)
    error_message: Optional[str] = None
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    
    # Relationships
    feed: RSSFeed = Relationship(back_populates="processing_logs")


class RSSFeedRead(SQLModel):
    """Read DTO for RSSFeed model - used for API responses."""
    
    id: int
    url: str
    name: str
    description: Optional[str] = None
    is_active: bool
    last_fetched_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    # Related processing log IDs instead of full objects
    processing_log_ids: List[int] = Field(default_factory=list)
    
    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                {
                    "id": 1,
                    "url": "https://example.com/rss",
                    "name": "Example News RSS",
                    "description": "RSS feed for Example News",
                    "is_active": True,
                    "last_fetched_at": "2023-01-01T12:00:00Z",
                    "created_at": "2023-01-01T00:00:00Z",
                    "updated_at": "2023-01-01T00:00:00Z",
                    "processing_log_ids": [1, 2, 3]
                }
            ]
        }
    }


class RSSFeedProcessingLogRead(SQLModel):
    """Read DTO for RSSFeedProcessingLog model - used for API responses."""
    
    id: int
    feed_id: int
    status: str
    articles_found: int
    articles_added: int
    error_message: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    
    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                {
                    "id": 1,
                    "feed_id": 1,
                    "status": "success",
                    "articles_found": 10,
                    "articles_added": 5,
                    "error_message": None,
                    "started_at": "2023-01-01T12:00:00Z",
                    "completed_at": "2023-01-01T12:05:00Z"
                }
            ]
        }
    }

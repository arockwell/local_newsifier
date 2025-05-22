"""
Database models for RSS feeds.
"""

from datetime import datetime, timezone
from typing import List, Optional

from sqlmodel import Field, Relationship, SQLModel


class RSSFeedBase(SQLModel):
    """Base model for RSSFeed."""
    # TODO: move field definitions from RSSFeed here

class RSSFeedRead(RSSFeedBase):
    """Read model for RSSFeed."""
    pass

class RSSFeedProcessingLogBase(SQLModel):
    """Base model for RSSFeedProcessingLog."""
    # TODO: move field definitions from RSSFeedProcessingLog here

class RSSFeedProcessingLogRead(RSSFeedProcessingLogBase):
    """Read model for RSSFeedProcessingLog."""
    pass

class RSSFeed(RSSFeedBase, table=True):
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


class RSSFeedProcessingLog(RSSFeedProcessingLogBase, table=True):
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

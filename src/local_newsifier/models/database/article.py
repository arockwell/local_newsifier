"""Article database model for the news analysis system."""

from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Index, String, Text
from sqlalchemy.orm import relationship

from local_newsifier.models.database.base import BaseModel
from local_newsifier.models.state import AnalysisStatus


class Article(BaseModel):
    """Database model for news articles."""
    
    __tablename__ = "articles"
    
    # Primary fields
    url = Column(String, unique=True, nullable=False, index=True)
    title = Column(String)
    source_domain = Column(String, index=True)
    
    # Content fields
    scraped_text = Column(Text)
    scraped_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Status fields
    status = Column(
        Enum(AnalysisStatus),
        default=AnalysisStatus.INITIALIZED,
        nullable=False
    )
    
    # Relationships
    entities = relationship(
        "Entity", 
        back_populates="article",
        cascade="all, delete-orphan"
    )
    
    # Indexes
    __table_args__ = (
        Index("ix_articles_status", "status"),
        Index("ix_articles_scraped_at", "scraped_at"),
    )
    
    def __repr__(self) -> str:
        """String representation of the model."""
        return f"<Article(id={self.id}, url='{self.url}', status='{self.status}')>"
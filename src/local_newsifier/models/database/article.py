"""Article database model for the news analysis system."""

from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Index, String, Text
from sqlalchemy.orm import relationship

from local_newsifier.models.database.base import Base
from local_newsifier.models.state import AnalysisStatus


class ArticleDB(Base):
    """Database model for news articles."""
    
    __tablename__ = "articles"
    
    # Primary fields
    url = Column(String, unique=True, nullable=False, index=True)
    title = Column(String)
    source = Column(String, index=True)  # Keep 'source' name for backward compatibility
    published_at = Column(DateTime)
    
    # Content fields
    content = Column(Text)  # Keep 'content' name for backward compatibility
    scraped_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Status fields - allow string values for backward compatibility
    status = Column(
        String,
        default=AnalysisStatus.INITIALIZED.value,
        nullable=False
    )
    
    # Relationships
    entities = relationship(
        "EntityDB", 
        back_populates="article",
        cascade="all, delete-orphan"
    )
    analysis_results = relationship(
        "AnalysisResultDB", 
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
        return f"<ArticleDB(id={self.id}, url='{self.url}', status='{self.status}')>"
        
    @classmethod
    def from_article_create(cls, article_data: dict) -> "ArticleDB":
        """Create an ArticleDB instance from article data."""
        return cls(**article_data)
"""Analysis result model for the news analysis system using SQLModel."""

from datetime import datetime
from typing import Dict, Any, Optional, TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel
from sqlalchemy import Column, JSON

from local_newsifier.models.base import TimestampMixin, SQLModelBase, sqlmodel_metadata

if TYPE_CHECKING:
    from local_newsifier.models.article import Article


class AnalysisResult(TimestampMixin, SQLModelBase, table=True):
    """SQLModel for analysis results."""
    
    # Use a different table name to avoid conflicts during transition
    __tablename__ = "sm_analysis_results"
    
    # Associate with our separate metadata
    metadata = sqlmodel_metadata
    
    id: Optional[int] = Field(default=None, primary_key=True)
    article_id: int = Field(foreign_key="sm_articles.id")
    analysis_type: str
    results: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))
    
    # Relationship
    article: "Article" = Relationship(back_populates="analysis_results")
    
    class Config:
        """Model configuration."""
        # For backward compatibility with pydantic v1
        from_attributes = True
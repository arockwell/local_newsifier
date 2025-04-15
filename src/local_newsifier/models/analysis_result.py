"""Analysis result model for the news analysis system using SQLModel."""

from datetime import datetime
from typing import Dict, Any, Optional, TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel
from sqlalchemy import Column, JSON

from local_newsifier.models.base import TimestampMixin

if TYPE_CHECKING:
    from local_newsifier.models.article import Article


class AnalysisResult(TimestampMixin, table=True):
    """SQLModel for analysis results."""
    
    __tablename__ = "analysis_results"
    __table_args__ = {"extend_existing": True}
    
    id: Optional[int] = Field(default=None, primary_key=True)
    article_id: int = Field(foreign_key="articles.id")
    analysis_type: str
    results: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))
    
    # Relationship
    article: "Article" = Relationship(back_populates="analysis_results")
    
    class Config:
        """Model configuration."""
        from_attributes = True
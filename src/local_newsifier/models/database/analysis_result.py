"""Analysis result models for the news analysis system."""

from datetime import datetime
from typing import Dict, Any, Optional, TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel
from sqlalchemy import Column, JSON, String

from local_newsifier.models.database.base import Base

# Handle circular imports
if TYPE_CHECKING:
    from local_newsifier.models.database.article import Article


class AnalysisResult(Base, table=True):
    """SQLModel for analysis results."""

    __tablename__ = "analysis_results"

    article_id: int = Field(foreign_key="articles.id", nullable=False)
    analysis_type: str = Field(sa_column=Column(String, nullable=False))
    results: Dict[str, Any] = Field(sa_column=Column(JSON, nullable=False))
    
    # Define relationship
    article: Optional["Article"] = Relationship(back_populates="analysis_results")


# For backward compatibility during migration
AnalysisResultDB = AnalysisResult
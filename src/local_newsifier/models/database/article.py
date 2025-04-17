"""Article models for the news analysis system."""

from datetime import datetime
from typing import List, Optional, TYPE_CHECKING

from sqlmodel import Field, Relationship

from local_newsifier.models.database.base import TableBase

# Handle circular imports
if TYPE_CHECKING:
    from local_newsifier.models.database.entity import Entity
    from local_newsifier.models.database.analysis_result import AnalysisResult


class Article(TableBase, table=True):
    """SQLModel for articles."""

    __tablename__ = "articles"
    
    # Handle multiple imports during test collection
    __table_args__ = {"extend_existing": True}
    
    title: str
    content: str
    url: str = Field(unique=True)
    source: str
    published_at: datetime
    status: str
    scraped_at: datetime
    
    # Define relationships
    entities: List["Entity"] = Relationship(back_populates="article")
    analysis_results: List["AnalysisResult"] = Relationship(back_populates="article")
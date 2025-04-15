"""Article model for the news analysis system using SQLModel."""

from datetime import datetime, timezone
from typing import List, Optional, TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

from local_newsifier.models.base import TimestampMixin, SQLModelBase, sqlmodel_metadata

if TYPE_CHECKING:
    from local_newsifier.models.entity import Entity
    from local_newsifier.models.analysis_result import AnalysisResult


class Article(TimestampMixin, SQLModelBase, table=True):
    """SQLModel for articles - combines database and schema functionality."""
    
    # Use a different table name to avoid conflicts during transition
    __tablename__ = "sm_articles"
    
    # Associate with our separate metadata
    metadata = sqlmodel_metadata
    
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(max_length=255)
    content: str 
    url: str = Field(max_length=512, unique=True)
    source: str = Field(max_length=255)
    published_at: datetime
    status: str = Field(max_length=50)
    scraped_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Relationships
    entities: List["Entity"] = Relationship(
        back_populates="article",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    analysis_results: List["AnalysisResult"] = Relationship(
        back_populates="article",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    
    class Config:
        """Model configuration."""
        # For backward compatibility with pydantic v1
        from_attributes = True
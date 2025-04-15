"""Entity model for the news analysis system using SQLModel."""

from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

from local_newsifier.models.base import TimestampMixin, SQLModelBase, sqlmodel_metadata

if TYPE_CHECKING:
    from local_newsifier.models.article import Article


class Entity(TimestampMixin, SQLModelBase, table=True):
    """SQLModel for entities."""
    
    # Use a different table name to avoid conflicts during transition
    __tablename__ = "sm_entities"
    
    # Associate with our separate metadata
    metadata = sqlmodel_metadata
    
    id: Optional[int] = Field(default=None, primary_key=True)
    article_id: int = Field(foreign_key="sm_articles.id")
    text: str
    entity_type: str
    confidence: float = Field(default=1.0)
    sentence_context: Optional[str] = None
    
    # Relationship
    article: "Article" = Relationship(back_populates="entities")
    
    class Config:
        """Model configuration."""
        # For backward compatibility with pydantic v1
        from_attributes = True
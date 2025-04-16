"""Entity models for the news analysis system."""

from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel
from sqlalchemy import Column, Float, String

from local_newsifier.models.database.base import Base

# Handle circular imports
if TYPE_CHECKING:
    from local_newsifier.models.database.article import Article


class Entity(Base, table=True):
    """SQLModel for entities, combining Pydantic validation and SQLAlchemy ORM."""

    __tablename__ = "entities"

    article_id: int = Field(foreign_key="articles.id", nullable=False)
    text: str = Field(sa_column=Column(String, nullable=False))
    entity_type: str = Field(sa_column=Column(String, nullable=False))
    confidence: float = Field(default=1.0, sa_column=Column(Float, default=1.0))
    sentence_context: Optional[str] = Field(default=None)
    
    # Define relationship
    article: Optional["Article"] = Relationship(back_populates="entities")


# No separate schema for entity creation, using the main Entity model instead
# No backward compatibility - we'll refactor references directly
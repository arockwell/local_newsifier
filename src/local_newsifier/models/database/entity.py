"""Entity models for the news analysis system."""

from typing import Optional, TYPE_CHECKING

from sqlmodel import Field, Relationship

from local_newsifier.models.database.base import TableBase

# Handle circular imports
if TYPE_CHECKING:
    from local_newsifier.models.database.article import Article


class Entity(TableBase, table=True):
    """SQLModel for entities."""

    __tablename__ = "entities"
    
    # Handle multiple imports during test collection
    __table_args__ = {"extend_existing": True}

    article_id: int = Field(foreign_key="articles.id")
    text: str
    entity_type: str
    confidence: float = Field(default=1.0)
    sentence_context: Optional[str] = None
    
    # Define relationship
    article: Optional["Article"] = Relationship(back_populates="entities")
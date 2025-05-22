"""Entity models for the news analysis system."""

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel

# Handle circular imports
if TYPE_CHECKING:
    from local_newsifier.models.article import Article


class Entity(SQLModel, table=True):
    """SQLModel for entities extracted from articles."""

    __tablename__ = "entities"
    
    # Handle multiple imports during test collection
    __table_args__ = {"extend_existing": True}
    
    # Primary key and timestamps
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column_kwargs={"onupdate": lambda: datetime.now(timezone.utc)}
    )

    # Entity fields
    article_id: int = Field(foreign_key="articles.id")
    text: str
    entity_type: str
    confidence: float = Field(default=1.0)
    sentence_context: Optional[str] = None
    
    # Define relationship with fully qualified path
    article: Optional["local_newsifier.models.article.Article"] = Relationship(back_populates="entities")
    
    # Model configuration for both SQLModel and Pydantic functionality
    model_config = {
        "arbitrary_types_allowed": True,
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                {
                    "article_id": 1,
                    "text": "John Smith",
                    "entity_type": "PERSON",
                    "confidence": 0.95,
                    "sentence_context": "John Smith announced the new policy today."
                }
            ]
        }
    }

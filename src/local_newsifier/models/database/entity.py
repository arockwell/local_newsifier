"""Entity models for the news analysis system."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from local_newsifier.models.database.base import Base


class EntityDB(Base):
    """Database model for entities."""

    __tablename__ = "entities"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True)
    article_id = Column(Integer, ForeignKey("articles.id"), nullable=False)
    text = Column(String, nullable=False)
    entity_type = Column(String, nullable=False)
    confidence = Column(Float, default=1.0)
    sentence_context = Column(String)
    created_at = Column(DateTime, default=lambda: datetime.now())

    # Relationships
    article = relationship("ArticleDB", back_populates="entities")


class EntityBase(BaseModel):
    """Base Pydantic model for entities."""

    text: str
    entity_type: str
    confidence: float
    sentence_context: Optional[str] = None


class EntityCreate(EntityBase):
    """Pydantic model for creating entities."""

    article_id: int


class Entity(EntityBase):
    """Pydantic model for entities with relationships."""

    id: int
    article_id: int

    class Config:
        """Pydantic config."""

        from_attributes = True


# Update forward references
Entity.model_rebuild()
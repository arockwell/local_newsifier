"""Entity database model for the news analysis system."""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Column, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import relationship

from local_newsifier.models.database.base import BaseModel


class Entity(BaseModel):
    """Database model for named entities found in articles."""
    
    __tablename__ = "entities"
    
    # Foreign key to article
    article_id = Column(Integer, ForeignKey("articles.id"), nullable=False)
    
    # Entity fields
    text = Column(String, nullable=False)
    entity_type = Column(String, nullable=False)  # PERSON, ORG, GPE, etc.
    sentence_context = Column(Text)  # The sentence where the entity was found
    confidence = Column(Float, default=1.0)
    
    # Relationships
    article = relationship("Article", back_populates="entities")
    
    # Indexes
    __table_args__ = (
        Index("ix_entities_text", "text"),
        Index("ix_entities_type", "entity_type"),
        Index("ix_entities_article_type", "article_id", "entity_type"),
    )
    
    def __repr__(self) -> str:
        """String representation of the model."""
        return f"<Entity(id={self.id}, text='{self.text}', type='{self.entity_type}')>"
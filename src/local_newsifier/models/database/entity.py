"""Entity database model for the news analysis system."""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Column, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import relationship

from local_newsifier.models.database.base import Base


class EntityDB(Base):
    """Database model for named entities found in articles."""
    
    __tablename__ = "entities"
    
    # Foreign key to article
    article_id = Column(Integer, ForeignKey("articles.id"), nullable=False)
    
    # Entity fields
    text = Column(String, nullable=False)
    entity_type = Column(String, nullable=False)  # PERSON, ORG, GPE, etc.
    confidence = Column(Float, default=1.0)
    
    # Add sentence_context field for storing context
    sentence_context = Column(Text)  # The sentence where the entity was found
    
    # Set created_at for backward compatibility (already included from Base)
    
    # Relationships
    article = relationship("ArticleDB", back_populates="entities")
    
    # Indexes
    __table_args__ = (
        Index("ix_entities_text", "text"),
        Index("ix_entities_type", "entity_type"),
        Index("ix_entities_article_type", "article_id", "entity_type"),
    )
    
    def __repr__(self) -> str:
        """String representation of the model."""
        return f"<EntityDB(id={self.id}, text='{self.text}', type='{self.entity_type}')>"
    
    @classmethod
    def from_entity_create(cls, entity_data: dict) -> "EntityDB":
        """Create an EntityDB instance from entity data."""
        return cls(**entity_data)
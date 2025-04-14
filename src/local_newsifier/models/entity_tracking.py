"""Entity tracking models for the news analysis system."""

from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

from pydantic import BaseModel, Field
from sqlalchemy import (Column, DateTime, Float, ForeignKey, Integer, String, 
                        Table, Text, UniqueConstraint, JSON)
from sqlalchemy.orm import relationship

from local_newsifier.models.database.base import Base

# Association table for entity mentions
entity_mentions = Table(
    "entity_mentions",
    Base.metadata,
    Column("id", Integer, primary_key=True),
    Column("canonical_entity_id", Integer, ForeignKey("canonical_entities.id"), nullable=False),
    Column("entity_id", Integer, ForeignKey("entities.id"), nullable=False),
    Column("article_id", Integer, ForeignKey("articles.id"), nullable=False),
    Column("confidence", Float, default=1.0),
    Column("created_at", DateTime, default=lambda: datetime.now(timezone.utc)),
    UniqueConstraint("canonical_entity_id", "entity_id", name="uix_entity_mention"),
    extend_existing=True
)

# Association table for entity relationships
entity_relationships = Table(
    "entity_relationships",
    Base.metadata,
    Column("id", Integer, primary_key=True),
    Column("source_entity_id", Integer, ForeignKey("canonical_entities.id"), nullable=False),
    Column("target_entity_id", Integer, ForeignKey("canonical_entities.id"), nullable=False),
    Column("relationship_type", String, nullable=False),
    Column("confidence", Float, default=1.0),
    Column("evidence", Text),
    Column("created_at", DateTime, default=lambda: datetime.now(timezone.utc)),
    Column("updated_at", DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)),
    UniqueConstraint("source_entity_id", "target_entity_id", "relationship_type", 
                    name="uix_entity_relationship"),
    extend_existing=True
)


class CanonicalEntityDB(Base):
    """Database model for canonical entities."""
    
    __tablename__ = "canonical_entities"
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    entity_type = Column(String, nullable=False)  # e.g., "PERSON", "ORG", "GPE"
    description = Column(Text)
    entity_metadata = Column(JSON)  # Renamed from metadata to avoid SQLAlchemy reserved name
    first_seen = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_seen = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Define a unique constraint for name and entity_type
    __table_args__ = (
        UniqueConstraint('name', 'entity_type', name='uix_name_type'),
        {'extend_existing': True}
    )
    
    # Relationships
    mentions = relationship(
        "EntityDB", 
        secondary="entity_mentions", 
        backref="canonical_entities"
    )
    
    # Relationships with other entities
    related_to = relationship(
        "CanonicalEntityDB",
        secondary="entity_relationships",
        primaryjoin="CanonicalEntityDB.id==entity_relationships.c.source_entity_id",
        secondaryjoin="CanonicalEntityDB.id==entity_relationships.c.target_entity_id",
        backref="related_from"
    )


class EntityMentionContextDB(Base):
    """Database model for storing entity mention contexts."""
    
    __tablename__ = "entity_mention_contexts"
    
    id = Column(Integer, primary_key=True)
    entity_id = Column(Integer, ForeignKey("entities.id"), nullable=False)
    article_id = Column(Integer, ForeignKey("articles.id"), nullable=False)
    context_text = Column(Text, nullable=False)
    context_type = Column(String)  # e.g., "sentence", "paragraph"
    sentiment_score = Column(Float)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Define a unique constraint
    __table_args__ = (
        UniqueConstraint('entity_id', 'article_id', name='uix_entity_article'),
        {'extend_existing': True}
    )
    
    # Relationships
    entity = relationship("EntityDB", backref="contexts")


class EntityProfileDB(Base):
    """Database model for entity profiles."""
    
    __tablename__ = "entity_profiles"
    
    id = Column(Integer, primary_key=True)
    canonical_entity_id = Column(Integer, ForeignKey("canonical_entities.id"), nullable=False)
    profile_type = Column(String, nullable=False)  # e.g., "summary", "background", "timeline"
    content = Column(Text, nullable=False)
    metadata = Column(JSON)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Define a unique constraint
    __table_args__ = (
        UniqueConstraint('canonical_entity_id', 'profile_type', name='uix_entity_profile_type'),
        {'extend_existing': True}
    )
    
    # Relationship back to canonical entity
    canonical_entity = relationship("CanonicalEntityDB", backref="profiles")


# Pydantic models for API/serialization
class CanonicalEntityBase(BaseModel):
    """Base model for canonical entities."""
    name: str
    entity_type: str
    description: Optional[str] = None
    entity_metadata: Optional[Dict[str, Any]] = None


class CanonicalEntityCreate(CanonicalEntityBase):
    """Model for creating canonical entities."""
    pass


class CanonicalEntity(CanonicalEntityBase):
    """Model for canonical entities with ID and timestamps."""
    id: int
    first_seen: datetime
    last_seen: datetime

    class Config:
        from_attributes = True


class EntityMentionContextBase(BaseModel):
    """Base model for entity mention contexts."""
    entity_id: int
    article_id: int
    context_text: str
    context_type: Optional[str] = None
    sentiment_score: Optional[float] = None


class EntityMentionContextCreate(EntityMentionContextBase):
    """Model for creating entity mention contexts."""
    pass


class EntityMentionContext(EntityMentionContextBase):
    """Model for entity mention contexts with ID and timestamp."""
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class EntityProfileBase(BaseModel):
    """Base model for entity profiles."""
    canonical_entity_id: int
    profile_type: str
    content: str
    metadata: Optional[Dict[str, Any]] = None


class EntityProfileCreate(EntityProfileBase):
    """Model for creating entity profiles."""
    pass


class EntityProfile(EntityProfileBase):
    """Model for entity profiles with ID and timestamps."""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EntityMention(BaseModel):
    """Model for entity mentions."""
    canonical_entity_id: int
    entity_id: int
    article_id: int
    confidence: float = 1.0

    class Config:
        from_attributes = True


class EntityMentionCreate(EntityMention):
    """Model for creating entity mentions."""
    pass


class EntityRelationship(BaseModel):
    """Model for entity relationships."""
    source_entity_id: int
    target_entity_id: int
    relationship_type: str
    confidence: float = 1.0
    evidence: Optional[str] = None

    class Config:
        from_attributes = True


class EntityRelationshipCreate(EntityRelationship):
    """Model for creating entity relationships."""
    pass

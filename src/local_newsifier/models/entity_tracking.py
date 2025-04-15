"""Entity tracking models for the news analysis system using SQLModel."""

from datetime import datetime, timezone
from typing import List, Optional, Dict, Any, TYPE_CHECKING, ForwardRef

from sqlmodel import Field, Relationship, SQLModel, MetaData
from sqlalchemy import Column, JSON, UniqueConstraint, Table, ForeignKey, DateTime, Integer, Float, String, Text

from local_newsifier.models.base import TimestampMixin

# For type checking
if TYPE_CHECKING:
    from local_newsifier.models.entity import Entity
    from local_newsifier.models.article import Article

# Create metadata for our tables
metadata = MetaData()

# Association table for entity mentions
entity_mentions = Table(
    "entity_mentions",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("canonical_entity_id", Integer, ForeignKey("canonical_entities.id"), nullable=False),
    Column("entity_id", Integer, ForeignKey("entities.id"), nullable=False),
    Column("article_id", Integer, ForeignKey("articles.id"), nullable=False),
    Column("confidence", Float, default=1.0),
    Column("created_at", DateTime, default=lambda: datetime.now(timezone.utc)),
    UniqueConstraint("canonical_entity_id", "entity_id", name="uix_entity_mention"),
)

# Association table for entity relationships
entity_relationships = Table(
    "entity_relationships",
    metadata,
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
)


class CanonicalEntity(TimestampMixin, table=True):
    """SQLModel for canonical entities."""
    
    __tablename__ = "canonical_entities"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    entity_type: str  # e.g., "PERSON", "ORG", "GPE"
    description: Optional[str] = None
    entity_metadata: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    first_seen: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_seen: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Define table constraints
    __table_args__ = (
        UniqueConstraint("name", "entity_type", name="uix_name_type"),
        {"extend_existing": True}
    )
    
    class Config:
        """Model configuration."""
        from_attributes = True


class EntityMentionContext(TimestampMixin, table=True):
    """SQLModel for entity mention contexts."""
    
    __tablename__ = "entity_mention_contexts"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    entity_id: int = Field(foreign_key="entities.id")
    article_id: int = Field(foreign_key="articles.id")
    context_text: str
    context_type: Optional[str] = None  # e.g., "sentence", "paragraph"
    sentiment_score: Optional[float] = None
    
    # Define table constraints
    __table_args__ = (
        UniqueConstraint("entity_id", "article_id", name="uix_entity_article"),
        {"extend_existing": True}
    )
    
    class Config:
        """Model configuration."""
        from_attributes = True


class EntityProfile(TimestampMixin, table=True):
    """SQLModel for entity profiles."""
    
    __tablename__ = "entity_profiles"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    canonical_entity_id: int = Field(foreign_key="canonical_entities.id")
    profile_type: str  # e.g., "summary", "background", "timeline"
    content: str
    profile_metadata: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    
    # Define table constraints
    __table_args__ = (
        UniqueConstraint("canonical_entity_id", "profile_type", name="uix_entity_profile_type"),
        {"extend_existing": True}
    )
    
    class Config:
        """Model configuration."""
        from_attributes = True


# Schema models for request/response
class CanonicalEntityCreate(SQLModel):
    """Model for creating canonical entities."""
    name: str
    entity_type: str
    description: Optional[str] = None
    entity_metadata: Optional[Dict[str, Any]] = None


class EntityMention(SQLModel):
    """Model for entity mentions."""
    canonical_entity_id: int
    entity_id: int
    article_id: int
    confidence: float = 1.0


class EntityMentionCreate(EntityMention):
    """Model for creating entity mentions."""
    pass


class EntityMentionContextCreate(SQLModel):
    """Model for creating entity mention contexts."""
    entity_id: int
    article_id: int
    context_text: str
    context_type: Optional[str] = None
    sentiment_score: Optional[float] = None


class EntityProfileCreate(SQLModel):
    """Model for creating entity profiles."""
    canonical_entity_id: int
    profile_type: str
    content: str
    profile_metadata: Optional[Dict[str, Any]] = None


class EntityRelationship(SQLModel):
    """Model for entity relationships."""
    id: Optional[int] = None
    source_entity_id: int
    target_entity_id: int
    relationship_type: str
    confidence: float = 1.0
    evidence: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class EntityRelationshipCreate(SQLModel):
    """Model for creating entity relationships."""
    source_entity_id: int
    target_entity_id: int
    relationship_type: str
    confidence: float = 1.0
    evidence: Optional[str] = None


class EntityConnection(SQLModel):
    """Model for representing entity connections with metadata."""
    source_entity: str
    target_entity: str
    relationship_type: str
    strength: float = 1.0
    context: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


# Legacy stubs for compatibility with tests
class CanonicalEntityDB:
    """Legacy stub for CanonicalEntityDB to maintain compatibility."""
    __tablename__ = "canonical_entities"
    __table_args__ = {"extend_existing": True}
    
    id: int
    name: str
    entity_type: str
    description: Optional[str]
    first_seen: datetime
    last_seen: datetime
    entity_metadata: Optional[Dict[str, Any]]

class EntityMentionContextDB:
    """Legacy stub for EntityMentionContextDB to maintain compatibility.""" 
    __tablename__ = "entity_mention_contexts"
    __table_args__ = {"extend_existing": True}
    
    id: int
    entity_id: int
    article_id: int
    context_text: str
    context_type: str
    sentiment_score: float
    framing_category: Optional[str] = None
    context_metadata: Optional[Dict[str, Any]] = None
    created_at: datetime

class EntityProfileDB:
    """Legacy stub for EntityProfileDB to maintain compatibility."""
    __tablename__ = "entity_profiles"
    __table_args__ = {"extend_existing": True}
    
    id: int
    canonical_entity_id: int
    profile_type: str
    content: str
    profile_metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
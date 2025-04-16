"""Entity tracking models for the news analysis system using SQLModel."""

from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, TYPE_CHECKING

from sqlmodel import SQLModel, Field, Relationship, JSON

from local_newsifier.models.database.base import TableBase

# Handle circular imports
if TYPE_CHECKING:
    from local_newsifier.models.database.entity import Entity
    from local_newsifier.models.database.article import Article


# Association tables as SQLModel classes
class EntityMention(SQLModel, table=True):
    """SQLModel for entity mentions."""
    
    __tablename__ = "entity_mentions"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    canonical_entity_id: int = Field(foreign_key="canonical_entities.id")
    entity_id: int = Field(foreign_key="entities.id")
    article_id: int = Field(foreign_key="articles.id")
    confidence: float = Field(default=1.0)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Define a unique constraint through sa_column_kwargs
    __table_args__ = (
        {"UniqueConstraint": ("canonical_entity_id", "entity_id", "name", "uix_entity_mention")},
        {"extend_existing": True}
    )


class EntityRelationship(SQLModel, table=True):
    """SQLModel for entity relationships."""
    
    __tablename__ = "entity_relationships"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    source_entity_id: int = Field(foreign_key="canonical_entities.id")
    target_entity_id: int = Field(foreign_key="canonical_entities.id")
    relationship_type: str
    confidence: float = Field(default=1.0)
    evidence: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column_kwargs={"onupdate": lambda: datetime.now(timezone.utc)}
    )
    
    # Define a unique constraint through sa_column_kwargs
    __table_args__ = (
        {"UniqueConstraint": ("source_entity_id", "target_entity_id", "relationship_type", "name", "uix_entity_relationship")},
        {"extend_existing": True}
    )


class CanonicalEntity(TableBase, table=True):
    """SQLModel for canonical entities."""
    
    __tablename__ = "canonical_entities"
    
    name: str
    entity_type: str  # e.g., "PERSON", "ORG", "GPE"
    description: Optional[str] = None
    entity_metadata: Optional[Dict[str, Any]] = Field(default=None, sa_type=JSON)
    first_seen: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_seen: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Define a unique constraint
    __table_args__ = (
        {"UniqueConstraint": ("name", "entity_type", "name", "uix_name_type")},
        {"extend_existing": True}
    )
    
    # Define relationships
    # These will be added later after the LinkingModel approach is implemented


class EntityMentionContext(TableBase, table=True):
    """SQLModel for entity mention contexts."""
    
    __tablename__ = "entity_mention_contexts"
    
    entity_id: int = Field(foreign_key="entities.id")
    article_id: int = Field(foreign_key="articles.id")
    context_text: str
    context_type: Optional[str] = None
    sentiment_score: Optional[float] = None
    
    # Define a unique constraint 
    __table_args__ = (
        {"UniqueConstraint": ("entity_id", "article_id", "name", "uix_entity_article")},
        {"extend_existing": True}
    )
    
    # Define relationships
    # These will be implemented with the LinkingModel approach


class EntityProfile(TableBase, table=True):
    """SQLModel for entity profiles."""
    
    __tablename__ = "entity_profiles"
    
    canonical_entity_id: int = Field(foreign_key="canonical_entities.id")
    profile_type: str  # e.g., "summary", "background", "timeline"
    content: str
    profile_metadata: Optional[Dict[str, Any]] = Field(default=None, sa_type=JSON)
    
    # Define a unique constraint
    __table_args__ = (
        {"UniqueConstraint": ("canonical_entity_id", "profile_type", "name", "uix_entity_profile_type")},
        {"extend_existing": True}
    )
    
    # Define relationships
    # These will be added later with LinkingModel approach


# Add connection model for visualizations and APIs
class EntityConnection(SQLModel):
    """Model for representing entity connections with metadata."""
    source_entity: str
    target_entity: str
    relationship_type: str
    strength: float = 1.0
    context: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

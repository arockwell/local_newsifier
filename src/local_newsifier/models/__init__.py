"""Model imports and initialization."""

# Import SQLModel base
from sqlmodel import SQLModel

# Import base models
from local_newsifier.models.base import TimestampMixin

# Import core models
from local_newsifier.models.article import Article
from local_newsifier.models.entity import Entity
from local_newsifier.models.analysis_result import AnalysisResult

# Import entity tracking models
from local_newsifier.models.entity_tracking import (
    CanonicalEntity,
    EntityMentionContext,
    EntityProfile,
    EntityMention,
    EntityMentionCreate,
    EntityRelationship,
    EntityRelationshipCreate,
    EntityConnection,
    entity_mentions,
    entity_relationships,
    metadata,
)

# Export all models
__all__ = [
    "SQLModel",
    "TimestampMixin",
    # Core models
    "Article",
    "Entity",
    "AnalysisResult",
    # Entity tracking models
    "CanonicalEntity",
    "EntityMentionContext",
    "EntityProfile",
    "EntityMention",
    "EntityMentionCreate",
    "EntityRelationship",
    "EntityRelationshipCreate",
    "EntityConnection",
    "entity_mentions",
    "entity_relationships",
    "metadata",
]
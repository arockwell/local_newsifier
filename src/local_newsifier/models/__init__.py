"""Model imports and initialization."""

# Re-export base SQLModel class
from sqlmodel import SQLModel

# Export table base
from local_newsifier.models.database.base import TableBase

# Import all models from their original locations but don't re-export
# This prevents duplicate class registrations
from local_newsifier.models.database.article import Article
from local_newsifier.models.database.entity import Entity
from local_newsifier.models.database.analysis_result import AnalysisResult
from local_newsifier.models.entity_tracking import (
    CanonicalEntity,
    EntityMention,
    EntityMentionContext,
    EntityProfile,
    EntityRelationship,
)
from local_newsifier.models.sentiment import (
    SentimentAnalysis,
    OpinionTrend,
    SentimentShift,
)

# Export only the class names, not the actual classes
__all__ = [
    "SQLModel",
    "TableBase",
    "Article",
    "Entity",
    "AnalysisResult",
    # Entity tracking models
    "CanonicalEntity",
    "EntityMention",
    "EntityMentionContext",
    "EntityProfile",
    "EntityRelationship",
    # Sentiment models
    "SentimentAnalysis",
    "OpinionTrend",
    "SentimentShift",
]
"""Model imports and initialization."""

# Import base classes
from local_newsifier.models.database.base import SQLModel, TableBase

# Import models
from local_newsifier.models.database.article import Article
from local_newsifier.models.database.entity import Entity
from local_newsifier.models.database.analysis_result import AnalysisResult

# Import entity tracking models (now converted to SQLModel)
from local_newsifier.models.entity_tracking import (
    CanonicalEntity,
    EntityMention,
    EntityMentionContext,
    EntityProfile,
    EntityRelationship,
)

# Import sentiment models
from local_newsifier.models.sentiment import (
    SentimentAnalysis,
    OpinionTrend,
    SentimentShift,
)

# Export all models
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
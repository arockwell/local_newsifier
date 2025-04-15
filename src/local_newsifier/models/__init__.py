"""Model imports and initialization."""

# Import SQLModel models
from sqlmodel import SQLModel
from local_newsifier.models.base import TimestampMixin
from local_newsifier.models.article import Article
from local_newsifier.models.entity import Entity
from local_newsifier.models.analysis_result import AnalysisResult

# Legacy imports - will be migrated to SQLModel
from local_newsifier.models.database.base import Base
from local_newsifier.models.database import (
    EntityDB,
    AnalysisResultDB,
)

# Import entity tracking models
from local_newsifier.models.entity_tracking import (
    CanonicalEntityDB,
    EntityMentionContextDB,
    EntityProfileDB,
    entity_mentions,
    entity_relationships,
)

# Export all models
__all__ = [
    "SQLModel",
    "TimestampMixin",
    "Article",
    "Entity",
    "AnalysisResult",
    "Base",
    "EntityDB",
    "AnalysisResultDB",
    "CanonicalEntityDB",
    "EntityMentionContextDB",
    "EntityProfileDB",
    "entity_mentions",
    "entity_relationships",
]

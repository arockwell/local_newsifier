"""Model imports and initialization."""

# Import base classes
from local_newsifier.models.database.base import SQLModel, TableBase, SchemaBase

# Import models
from local_newsifier.models.database.article import Article
from local_newsifier.models.database.entity import Entity
from local_newsifier.models.database.analysis_result import AnalysisResult

# Import entity tracking models (not yet converted to SQLModel)
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
    "TableBase",
    "SchemaBase",
    "Article",
    "Entity",
    "AnalysisResult",
    # Legacy models not yet converted
    "CanonicalEntityDB",
    "EntityMentionContextDB",
    "EntityProfileDB",
    "entity_mentions",
    "entity_relationships",
]

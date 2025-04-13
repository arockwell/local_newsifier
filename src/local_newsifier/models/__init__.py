"""Model imports and initialization."""

# Import Base first
from local_newsifier.models.database.base import Base

# Import database models
from local_newsifier.models.database.article import ArticleDB
from local_newsifier.models.database.entity import EntityDB
from local_newsifier.models.database.analysis_result import AnalysisResultDB

# Import entity tracking models
from local_newsifier.models.entity_tracking import (
    CanonicalEntityDB,
    EntityMentionContextDB,
    EntityProfileDB,
    entity_mentions,
    entity_relationships
)

# Export all models
__all__ = [
    "Base",
    "ArticleDB",
    "EntityDB",
    "AnalysisResultDB",
    "CanonicalEntityDB",
    "EntityMentionContextDB",
    "EntityProfileDB",
    "entity_mentions",
    "entity_relationships"
]

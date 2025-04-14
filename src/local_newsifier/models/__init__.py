"""Model imports and initialization."""

# Import Base first
from local_newsifier.models.database.base import Base

# Import database models
from local_newsifier.models.database import (
    ArticleDB,
    EntityDB,
    AnalysisResultDB,
)

# Import Pydantic models
from local_newsifier.models.pydantic_models import (
    Article,
    Entity,
    AnalysisResult,
    ArticleCreate,
    EntityCreate,
    AnalysisResultCreate,
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
    "Base",
    "ArticleDB",
    "EntityDB",
    "AnalysisResultDB",
    "Article",
    "Entity",
    "AnalysisResult",
    "ArticleCreate",
    "EntityCreate",
    "AnalysisResultCreate",
    "CanonicalEntityDB",
    "EntityMentionContextDB",
    "EntityProfileDB",
    "entity_mentions",
    "entity_relationships",
]

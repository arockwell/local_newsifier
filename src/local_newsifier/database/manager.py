"""Database manager for handling database operations (legacy compatibility layer).

This module provides a compatibility layer for existing code that uses the DatabaseManager
class. New code should use the CRUD modules directly instead.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from local_newsifier.crud.analysis_result import \
    analysis_result as analysis_result_crud
# Import CRUD modules
from local_newsifier.crud.article import article as article_crud
from local_newsifier.crud.canonical_entity import \
    canonical_entity as canonical_entity_crud
from local_newsifier.crud.entity import entity as entity_crud
from local_newsifier.crud.entity_mention_context import \
    entity_mention_context as entity_mention_context_crud
from local_newsifier.crud.entity_profile import \
    entity_profile as entity_profile_crud
from local_newsifier.crud.entity_relationship import \
    entity_relationship as entity_relationship_crud
# Import models from their original locations for backward compatibility
from local_newsifier.models.database import (AnalysisResultDB, ArticleDB,
                                             EntityDB)
from local_newsifier.models.database.base import Base
from local_newsifier.models.entity_tracking import (CanonicalEntity,
                                                    CanonicalEntityCreate,
                                                    CanonicalEntityDB,
                                                    EntityMentionContext,
                                                    EntityMentionContextCreate,
                                                    EntityMentionContextDB,
                                                    EntityProfile,
                                                    EntityProfileCreate,
                                                    EntityProfileDB,
                                                    EntityRelationship,
                                                    EntityRelationshipCreate,
                                                    entity_mentions,
                                                    entity_relationships)
from local_newsifier.models.pydantic_models import (AnalysisResult,
                                                    AnalysisResultCreate,
                                                    Article, ArticleCreate,
                                                    Entity, EntityCreate)
from local_newsifier.models.state import AnalysisStatus
from local_newsifier.models.trend import TrendAnalysis, TrendEntity

# Export models through manager
__all__ = [
    "DatabaseManager",
    "Article",
    "ArticleCreate",
    "ArticleDB",
    "Entity",
    "EntityCreate",
    "EntityDB",
    "AnalysisResult",
    "AnalysisResultCreate",
    "AnalysisResultDB",
    "CanonicalEntity",
    "CanonicalEntityCreate",
    "CanonicalEntityDB",
    "EntityMentionContext",
    "EntityMentionContextCreate",
    "EntityMentionContextDB",
    "EntityProfile",
    "EntityProfileCreate",
    "EntityProfileDB",
    "EntityRelationship",
    "EntityRelationshipCreate",
]


class DatabaseManager:
    """Manager class for database operations (legacy compatibility layer).

    This class provides a compatibility layer for existing code that uses the
    DatabaseManager class. New code should use the CRUD modules directly instead.
    """

    def __init__(self, session: Session):
        """Initialize the database manager.

        Args:
            session: SQLAlchemy session instance
        """
        self.session = session

    def create_article(self, article: ArticleCreate) -> Article:
        """Create a new article in the database.

        Args:
            article: Article data to create

        Returns:
            Created article
        """
        return article_crud.create(self.session, obj_in=article)

    def get_article(self, article_id: int) -> Optional[Article]:
        """Get an article by ID.

        Args:
            article_id: ID of the article to get

        Returns:
            Article if found, None otherwise
        """
        return article_crud.get(self.session, id=article_id)

    def get_article_by_url(self, url: str) -> Optional[Article]:
        """Get an article by URL.

        Args:
            url: URL of the article to get

        Returns:
            Article if found, None otherwise
        """
        return article_crud.get_by_url(self.session, url=url)

    def add_entity(self, entity: EntityCreate) -> Entity:
        """Add an entity to an article.

        Args:
            entity: Entity data to add

        Returns:
            Created entity
        """
        return entity_crud.create(self.session, obj_in=entity)

    def add_analysis_result(self, result: AnalysisResultCreate) -> AnalysisResult:
        """Add an analysis result to an article.

        Args:
            result: Analysis result data to add

        Returns:
            Created analysis result
        """
        return analysis_result_crud.create(self.session, obj_in=result)

    def update_article_status(self, article_id: int, status: str) -> Optional[Article]:
        """Update an article's status.

        Args:
            article_id: ID of the article to update
            status: New status

        Returns:
            Updated article if found, None otherwise
        """
        return article_crud.update_status(
            self.session, article_id=article_id, status=status
        )

    def get_articles_by_status(self, status: str) -> List[Article]:
        """Get all articles with a specific status.

        Args:
            status: Status to filter by

        Returns:
            List of articles with the specified status
        """
        return article_crud.get_by_status(self.session, status=status)

    def get_entities_by_article(self, article_id: int) -> List[Entity]:
        """Get all entities for an article.

        Args:
            article_id: ID of the article

        Returns:
            List of entities for the article
        """
        return entity_crud.get_by_article(self.session, article_id=article_id)

    def get_analysis_results_by_article(self, article_id: int) -> List[AnalysisResult]:
        """Get all analysis results for an article.

        Args:
            article_id: ID of the article

        Returns:
            List of analysis results for the article
        """
        return analysis_result_crud.get_by_article(self.session, article_id=article_id)

    # Entity Tracking Methods

    def create_canonical_entity(self, entity: CanonicalEntityCreate) -> CanonicalEntity:
        """Create a new canonical entity in the database.

        Args:
            entity: Canonical entity data to create

        Returns:
            Created canonical entity
        """
        return canonical_entity_crud.create(self.session, obj_in=entity)

    def get_canonical_entity(self, entity_id: int) -> Optional[CanonicalEntity]:
        """Get a canonical entity by ID.

        Args:
            entity_id: ID of the canonical entity to get

        Returns:
            Canonical entity if found, None otherwise
        """
        return canonical_entity_crud.get(self.session, id=entity_id)

    def get_canonical_entity_by_name(
        self, name: str, entity_type: str
    ) -> Optional[CanonicalEntity]:
        """Get a canonical entity by name and type.

        Args:
            name: Name of the canonical entity
            entity_type: Type of the entity (e.g., "PERSON")

        Returns:
            Canonical entity if found, None otherwise
        """
        return canonical_entity_crud.get_by_name(
            self.session, name=name, entity_type=entity_type
        )

    def add_entity_mention_context(
        self, context: EntityMentionContextCreate
    ) -> EntityMentionContext:
        """Add context for an entity mention.

        Args:
            context: Entity mention context data to add

        Returns:
            Created entity mention context
        """
        return entity_mention_context_crud.create(self.session, obj_in=context)

    def add_entity_profile(self, profile: EntityProfileCreate) -> EntityProfile:
        """Add a new entity profile.

        Args:
            profile: Entity profile data to add

        Returns:
            Created entity profile
        """
        try:
            return entity_profile_crud.create(self.session, obj_in=profile)
        except ValueError as e:
            if "Profile already exists" in str(e):
                raise ValueError(
                    f"Profile already exists for entity {profile.canonical_entity_id}"
                )
            raise

    def update_entity_profile(self, profile: EntityProfileCreate) -> EntityProfile:
        """Update an entity profile.

        Args:
            profile: Profile data to update

        Returns:
            Updated profile
        """
        return entity_profile_crud.update_or_create(self.session, obj_in=profile)

    def add_entity_relationship(
        self, relationship: EntityRelationshipCreate
    ) -> EntityRelationship:
        """Add a relationship between entities.

        Args:
            relationship: Entity relationship data to add

        Returns:
            Created entity relationship
        """
        return entity_relationship_crud.create_or_update(
            self.session, obj_in=relationship
        )

    def get_entity_mentions_count(self, entity_id: int) -> int:
        """Get the count of mentions for an entity.

        Args:
            entity_id: ID of the entity

        Returns:
            Count of mentions
        """
        return canonical_entity_crud.get_mentions_count(
            self.session, entity_id=entity_id
        )

    def get_entity_timeline(
        self, entity_id: int, start_date: datetime, end_date: datetime
    ) -> List[Dict[str, Any]]:
        """Get the timeline of entity mentions.

        Args:
            entity_id: ID of the entity
            start_date: Start date for the timeline
            end_date: End date for the timeline

        Returns:
            List of timeline entries
        """
        return canonical_entity_crud.get_entity_timeline(
            self.session, entity_id=entity_id, start_date=start_date, end_date=end_date
        )

    def get_entity_sentiment_trend(
        self, entity_id: int, start_date: datetime, end_date: datetime
    ) -> List[Dict[str, Any]]:
        """Get the sentiment trend for an entity.

        Args:
            entity_id: ID of the entity
            start_date: Start date for the trend
            end_date: End date for the trend

        Returns:
            List of sentiment trend entries
        """
        return entity_mention_context_crud.get_sentiment_trend(
            self.session, entity_id=entity_id, start_date=start_date, end_date=end_date
        )

    def get_canonical_entities_by_type(self, entity_type: str) -> List[CanonicalEntity]:
        """Get all canonical entities of a specific type.

        Args:
            entity_type: Type of entities to get

        Returns:
            List of canonical entities
        """
        return canonical_entity_crud.get_by_type(self.session, entity_type=entity_type)

    def get_all_canonical_entities(
        self, entity_type: Optional[str] = None
    ) -> List[CanonicalEntity]:
        """Get all canonical entities, optionally filtered by type.

        Args:
            entity_type: Optional type to filter by

        Returns:
            List of canonical entities
        """
        return canonical_entity_crud.get_all(self.session, entity_type=entity_type)

    def get_entity_profile(self, entity_id: int) -> Optional[EntityProfile]:
        """Get the profile for an entity.

        Args:
            entity_id: ID of the entity

        Returns:
            Entity profile if found, None otherwise
        """
        return entity_profile_crud.get_by_entity(self.session, entity_id=entity_id)

    def get_articles_mentioning_entity(
        self, entity_id: int, start_date: datetime, end_date: datetime
    ) -> List[Article]:
        """Get all articles mentioning an entity within a date range.

        Args:
            entity_id: ID of the entity
            start_date: Start date for the range
            end_date: End date for the range

        Returns:
            List of articles mentioning the entity
        """
        db_articles = canonical_entity_crud.get_articles_mentioning_entity(
            self.session, entity_id=entity_id, start_date=start_date, end_date=end_date
        )
        return [Article.model_validate(article) for article in db_articles]

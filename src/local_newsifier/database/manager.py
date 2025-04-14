"""Database manager for handling database operations."""

from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

# Import models from their original locations
from local_newsifier.models.database import ArticleDB, EntityDB, AnalysisResultDB
from local_newsifier.models.pydantic_models import (
    Article, ArticleCreate,
    Entity, EntityCreate,
    AnalysisResult, AnalysisResultCreate
)
from local_newsifier.models.database.base import Base
from local_newsifier.models.entity_tracking import (
    CanonicalEntity, CanonicalEntityCreate, CanonicalEntityDB,
    EntityMentionContext, EntityMentionContextCreate, EntityMentionContextDB,
    EntityProfile, EntityProfileCreate, EntityProfileDB,
    EntityRelationship, EntityRelationshipCreate,
    entity_mentions, entity_relationships
)
from local_newsifier.models.state import AnalysisStatus
from local_newsifier.models.trend import TrendAnalysis, TrendEntity

# Export models through manager
__all__ = [
    'DatabaseManager',
    'Article', 'ArticleCreate', 'ArticleDB',
    'Entity', 'EntityCreate', 'EntityDB',
    'AnalysisResult', 'AnalysisResultCreate', 'AnalysisResultDB',
    'CanonicalEntity', 'CanonicalEntityCreate', 'CanonicalEntityDB',
    'EntityMentionContext', 'EntityMentionContextCreate', 'EntityMentionContextDB',
    'EntityProfile', 'EntityProfileCreate', 'EntityProfileDB',
    'EntityRelationship', 'EntityRelationshipCreate',
]

class DatabaseManager:
    """Manager class for database operations."""

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
        article_data = article.model_dump()
        if 'scraped_at' not in article_data or article_data['scraped_at'] is None:
            article_data['scraped_at'] = datetime.now(timezone.utc)
        db_article = ArticleDB(**article_data)
        self.session.add(db_article)
        self.session.commit()
        self.session.refresh(db_article)
        return Article.model_validate(db_article)

    def get_article(self, article_id: int) -> Optional[Article]:
        """Get an article by ID.

        Args:
            article_id: ID of the article to get

        Returns:
            Article if found, None otherwise
        """
        db_article = (
            self.session.query(ArticleDB).filter(ArticleDB.id == article_id).first()
        )
        return Article.model_validate(db_article) if db_article else None

    def get_article_by_url(self, url: str) -> Optional[Article]:
        """Get an article by URL.

        Args:
            url: URL of the article to get

        Returns:
            Article if found, None otherwise
        """
        db_article = self.session.query(ArticleDB).filter(ArticleDB.url == url).first()
        return Article.model_validate(db_article) if db_article else None

    def add_entity(self, entity: EntityCreate) -> Entity:
        """Add an entity to an article.

        Args:
            entity: Entity data to add

        Returns:
            Created entity
        """
        db_entity = EntityDB(**entity.model_dump())
        self.session.add(db_entity)
        self.session.commit()
        self.session.refresh(db_entity)
        return Entity.model_validate(db_entity)

    def add_analysis_result(self, result: AnalysisResultCreate) -> AnalysisResult:
        """Add an analysis result to an article.

        Args:
            result: Analysis result data to add

        Returns:
            Created analysis result
        """
        db_result = AnalysisResultDB(**result.model_dump())
        self.session.add(db_result)
        self.session.commit()
        self.session.refresh(db_result)
        return AnalysisResult.model_validate(db_result)

    def update_article_status(self, article_id: int, status: str) -> Optional[Article]:
        """Update an article's status.

        Args:
            article_id: ID of the article to update
            status: New status

        Returns:
            Updated article if found, None otherwise
        """
        db_article = (
            self.session.query(ArticleDB).filter(ArticleDB.id == article_id).first()
        )
        if db_article:
            db_article.status = status  # type: ignore
            self.session.commit()
            self.session.refresh(db_article)
            return Article.model_validate(db_article)
        return None

    def get_articles_by_status(self, status: str) -> List[Article]:
        """Get all articles with a specific status.

        Args:
            status: Status to filter by

        Returns:
            List of articles with the specified status
        """
        db_articles = (
            self.session.query(ArticleDB).filter(ArticleDB.status == status).all()
        )
        return [Article.model_validate(article) for article in db_articles]

    def get_entities_by_article(self, article_id: int) -> List[Entity]:
        """Get all entities for an article.

        Args:
            article_id: ID of the article

        Returns:
            List of entities for the article
        """
        db_entities = (
            self.session.query(EntityDB).filter(EntityDB.article_id == article_id).all()
        )
        return [Entity.model_validate(entity) for entity in db_entities]

    def get_analysis_results_by_article(self, article_id: int) -> List[AnalysisResult]:
        """Get all analysis results for an article.

        Args:
            article_id: ID of the article

        Returns:
            List of analysis results for the article
        """
        db_results = (
            self.session.query(AnalysisResultDB)
            .filter(AnalysisResultDB.article_id == article_id)
            .all()
        )
        return [AnalysisResult.model_validate(result) for result in db_results]

    # Entity Tracking Methods
    
    def create_canonical_entity(self, entity: CanonicalEntityCreate) -> CanonicalEntity:
        """Create a new canonical entity in the database.

        Args:
            entity: Canonical entity data to create

        Returns:
            Created canonical entity
        """
        db_entity = CanonicalEntityDB(**entity.model_dump())
        self.session.add(db_entity)
        self.session.commit()
        self.session.refresh(db_entity)
        return CanonicalEntity.model_validate(db_entity)

    def get_canonical_entity(self, entity_id: int) -> Optional[CanonicalEntity]:
        """Get a canonical entity by ID.

        Args:
            entity_id: ID of the canonical entity to get

        Returns:
            Canonical entity if found, None otherwise
        """
        db_entity = (
            self.session.query(CanonicalEntityDB)
            .filter(CanonicalEntityDB.id == entity_id)
            .first()
        )
        return CanonicalEntity.model_validate(db_entity) if db_entity else None

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
        db_entity = (
            self.session.query(CanonicalEntityDB)
            .filter(
                CanonicalEntityDB.name == name, 
                CanonicalEntityDB.entity_type == entity_type
            )
            .first()
        )
        return CanonicalEntity.model_validate(db_entity) if db_entity else None

    def add_entity_mention_context(
        self, context: EntityMentionContextCreate
    ) -> EntityMentionContext:
        """Add context for an entity mention.

        Args:
            context: Entity mention context data to add

        Returns:
            Created entity mention context
        """
        db_context = EntityMentionContextDB(**context.model_dump())
        self.session.add(db_context)
        self.session.commit()
        self.session.refresh(db_context)
        return EntityMentionContext.model_validate(db_context)

    def add_entity_profile(self, profile: EntityProfileCreate) -> EntityProfile:
        """Add a new entity profile.

        Args:
            profile: Entity profile data to add

        Returns:
            Created entity profile
        """
        # Check if profile already exists
        existing_profile = (
            self.session.query(EntityProfileDB)
            .filter(EntityProfileDB.canonical_entity_id == profile.canonical_entity_id)
            .first()
        )
        
        if existing_profile:
            raise ValueError(f"Profile already exists for entity {profile.canonical_entity_id}")
            
        db_profile = EntityProfileDB(**profile.model_dump())
        self.session.add(db_profile)
        self.session.commit()
        self.session.refresh(db_profile)
        return EntityProfile.model_validate(db_profile)

    def update_entity_profile(self, profile: EntityProfileCreate) -> EntityProfile:
        """Update an entity profile.

        Args:
            profile: Profile data to update

        Returns:
            Updated profile
        """
        # Get existing profile
        db_profile = (
            self.session.query(EntityProfileDB)
            .filter(
                EntityProfileDB.canonical_entity_id == profile.canonical_entity_id,
                EntityProfileDB.profile_type == profile.profile_type
            )
            .first()
        )
        
        if db_profile:
            # Update profile data using SQLAlchemy's update method
            self.session.query(EntityProfileDB).filter(
                EntityProfileDB.id == db_profile.id
            ).update({
                "content": profile.content,
                "profile_metadata": profile.profile_metadata,
                "updated_at": datetime.now(timezone.utc)
            })
            
            self.session.commit()
            self.session.refresh(db_profile)
            return EntityProfile.model_validate(db_profile)
        
        # If profile doesn't exist, create it
        return self.add_entity_profile(profile)

    def add_entity_relationship(
        self, relationship: EntityRelationshipCreate
    ) -> EntityRelationship:
        """Add a relationship between entities.

        Args:
            relationship: Entity relationship data to add

        Returns:
            Created entity relationship
        """
        # Check if relationship already exists
        existing = (
            self.session.query(entity_relationships)
            .filter(
                entity_relationships.c.source_entity_id == relationship.source_entity_id,
                entity_relationships.c.target_entity_id == relationship.target_entity_id,
                entity_relationships.c.relationship_type == relationship.relationship_type,
            )
            .first()
        )
        
        if existing:
            # Update existing relationship
            self.session.execute(
                entity_relationships.update()
                .where(
                    entity_relationships.c.source_entity_id == relationship.source_entity_id,
                    entity_relationships.c.target_entity_id == relationship.target_entity_id,
                    entity_relationships.c.relationship_type == relationship.relationship_type,
                )
                .values(
                    confidence=relationship.confidence,
                    evidence=relationship.evidence,
                    updated_at=datetime.now(timezone.utc),
                )
            )
            self.session.commit()
            
            # Get the updated relationship
            updated = (
                self.session.query(entity_relationships)
                .filter(
                    entity_relationships.c.source_entity_id == relationship.source_entity_id,
                    entity_relationships.c.target_entity_id == relationship.target_entity_id,
                    entity_relationships.c.relationship_type == relationship.relationship_type,
                )
                .first()
            )
            
            if updated:
                return EntityRelationship(
                    id=updated.id,  # type: ignore
                    source_entity_id=updated.source_entity_id,
                    target_entity_id=updated.target_entity_id,
                    relationship_type=updated.relationship_type,
                    confidence=updated.confidence,
                    evidence=updated.evidence,
                    created_at=updated.created_at,  # type: ignore
                    updated_at=updated.updated_at,  # type: ignore
                )
        
        # Create new relationship
        result = self.session.execute(
            entity_relationships.insert().values(
                source_entity_id=relationship.source_entity_id,
                target_entity_id=relationship.target_entity_id,
                relationship_type=relationship.relationship_type,
                confidence=relationship.confidence,
                evidence=relationship.evidence,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
        )
        self.session.commit()
        
        # Get the created relationship
        created = (
            self.session.query(entity_relationships)
            .filter(
                entity_relationships.c.source_entity_id == relationship.source_entity_id,
                entity_relationships.c.target_entity_id == relationship.target_entity_id,
                entity_relationships.c.relationship_type == relationship.relationship_type,
            )
            .first()
        )
        
        if created:
            return EntityRelationship(
                id=created.id,  # type: ignore
                source_entity_id=created.source_entity_id,
                target_entity_id=created.target_entity_id,
                relationship_type=created.relationship_type,
                confidence=created.confidence,
                evidence=created.evidence,
                created_at=created.created_at,  # type: ignore
                updated_at=created.updated_at,  # type: ignore
            )
        
        raise ValueError("Failed to create entity relationship")

    def get_entity_mentions_count(self, entity_id: int) -> int:
        """Get the count of mentions for an entity.

        Args:
            entity_id: ID of the entity

        Returns:
            Count of mentions
        """
        return (
            self.session.query(func.count(entity_mentions.c.id))
            .filter(entity_mentions.c.canonical_entity_id == entity_id)
            .scalar()
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
        results = (
            self.session.query(
                ArticleDB.published_at,
                func.count(entity_mentions.c.id).label("mention_count"),
            )
            .join(entity_mentions, ArticleDB.id == entity_mentions.c.article_id)
            .filter(
                entity_mentions.c.canonical_entity_id == entity_id,
                ArticleDB.published_at >= start_date,
                ArticleDB.published_at <= end_date,
            )
            .group_by(ArticleDB.published_at)
            .order_by(ArticleDB.published_at)
            .all()
        )
        
        return [
            {
                "date": date,
                "mention_count": count,
            }
            for date, count in results
        ]

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
        results = (
            self.session.query(
                ArticleDB.published_at,
                func.avg(EntityMentionContextDB.sentiment_score).label("avg_sentiment"),
            )
            .join(entity_mentions, ArticleDB.id == entity_mentions.c.article_id)
            .join(
                EntityMentionContextDB,
                EntityMentionContextDB.entity_id == entity_mentions.c.entity_id,
            )
            .filter(
                entity_mentions.c.canonical_entity_id == entity_id,
                ArticleDB.published_at >= start_date,
                ArticleDB.published_at <= end_date,
            )
            .group_by(ArticleDB.published_at)
            .order_by(ArticleDB.published_at)
            .all()
        )
        
        return [
            {
                "date": date,
                "avg_sentiment": float(sentiment) if sentiment is not None else None,
            }
            for date, sentiment in results
        ]

    def get_canonical_entities_by_type(self, entity_type: str) -> List[CanonicalEntity]:
        """Get all canonical entities of a specific type.

        Args:
            entity_type: Type of entities to get

        Returns:
            List of canonical entities
        """
        db_entities = (
            self.session.query(CanonicalEntityDB)
            .filter(CanonicalEntityDB.entity_type == entity_type)
            .all()
        )
        return [CanonicalEntity.model_validate(entity) for entity in db_entities]

    def get_all_canonical_entities(self, entity_type: Optional[str] = None) -> List[CanonicalEntity]:
        """Get all canonical entities, optionally filtered by type.

        Args:
            entity_type: Optional type to filter by

        Returns:
            List of canonical entities
        """
        query = self.session.query(CanonicalEntityDB)
        if entity_type:
            query = query.filter(CanonicalEntityDB.entity_type == entity_type)
        db_entities = query.all()
        return [CanonicalEntity.model_validate(entity) for entity in db_entities]

    def get_entity_profile(self, entity_id: int) -> Optional[EntityProfile]:
        """Get the profile for an entity.

        Args:
            entity_id: ID of the entity

        Returns:
            Entity profile if found, None otherwise
        """
        db_profile = (
            self.session.query(EntityProfileDB)
            .filter(EntityProfileDB.canonical_entity_id == entity_id)
            .first()
        )
        return EntityProfile.model_validate(db_profile) if db_profile else None

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
        db_articles = (
            self.session.query(ArticleDB)
            .join(entity_mentions, ArticleDB.id == entity_mentions.c.article_id)
            .filter(
                entity_mentions.c.canonical_entity_id == entity_id,
                ArticleDB.published_at >= start_date,
                ArticleDB.published_at <= end_date,
            )
            .all()
        )
        return [Article.model_validate(article) for article in db_articles]

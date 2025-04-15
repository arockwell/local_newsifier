"""Database manager for handling database operations."""

from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timezone
from uuid import UUID

from sqlmodel import Session, select, func
from sqlalchemy.exc import IntegrityError

# Import SQLModel models
from local_newsifier.models import (
    Article, 
    Entity, 
    AnalysisResult,
    CanonicalEntity,
    EntityMentionContext,
    EntityProfile,
    EntityRelationship,
    entity_mentions,
    entity_relationships
)

# Import Pydantic models
from local_newsifier.models.pydantic_models import ArticleCreate, EntityCreate
from local_newsifier.models.entity_tracking import (
    CanonicalEntityCreate,
    EntityMentionContextCreate,
    EntityProfileCreate,
    EntityRelationshipCreate
)
from local_newsifier.models.state import AnalysisStatus
from local_newsifier.models.trend import TrendAnalysis, TrendEntity

# Export models through manager
__all__ = [
    'DatabaseManager',
    'Article',
    'Entity',
    'AnalysisResult',
    'CanonicalEntity',
    'EntityMentionContext',
    'EntityProfile',
    'EntityRelationship',
]

class DatabaseManager:
    """Manager class for database operations."""

    def __init__(self, session: Session):
        """Initialize the database manager.

        Args:
            session: SQLModel session instance
        """
        self.session = session

    def create_article(self, article_data: Union[Dict[str, Any], ArticleCreate]) -> Article:
        """Create a new article in the database.

        Args:
            article_data: Article data to create (Dict or ArticleCreate model)

        Returns:
            Created article
        """
        # Handle either Dict or ArticleCreate
        if isinstance(article_data, dict):
            if 'scraped_at' not in article_data or article_data['scraped_at'] is None:
                article_data['scraped_at'] = datetime.now(timezone.utc)
            db_article = Article(**article_data)
        else:
            # SQLModel object - convert to dict and add scraped_at
            data_dict = article_data.model_dump()
            if 'scraped_at' not in data_dict or data_dict['scraped_at'] is None:
                data_dict['scraped_at'] = datetime.now(timezone.utc)
            db_article = Article(**data_dict)
        
        self.session.add(db_article)
        self.session.commit()
        self.session.refresh(db_article)
        return db_article

    def get_article(self, article_id: int) -> Optional[Article]:
        """Get an article by ID.

        Args:
            article_id: ID of the article to get

        Returns:
            Article if found, None otherwise
        """
        statement = select(Article).where(Article.id == article_id)
        return self.session.exec(statement).first()

    def get_article_by_url(self, url: str) -> Optional[Article]:
        """Get an article by URL.

        Args:
            url: URL of the article to get

        Returns:
            Article if found, None otherwise
        """
        statement = select(Article).where(Article.url == url)
        return self.session.exec(statement).first()

    def add_entity(self, entity_data: Dict[str, Any]) -> Entity:
        """Add an entity to an article.

        Args:
            entity_data: Entity data to add

        Returns:
            Created entity
        """
        db_entity = Entity(**entity_data)
        self.session.add(db_entity)
        self.session.commit()
        self.session.refresh(db_entity)
        return db_entity

    def add_analysis_result(self, result_data: Dict[str, Any]) -> AnalysisResult:
        """Add an analysis result to an article.

        Args:
            result_data: Analysis result data to add

        Returns:
            Created analysis result
        """
        db_result = AnalysisResult(**result_data)
        self.session.add(db_result)
        self.session.commit()
        self.session.refresh(db_result)
        return db_result

    def update_article_status(self, article_id: int, status: str) -> Optional[Article]:
        """Update an article's status.

        Args:
            article_id: ID of the article to update
            status: New status

        Returns:
            Updated article if found, None otherwise
        """
        statement = select(Article).where(Article.id == article_id)
        db_article = self.session.exec(statement).first()
        
        if db_article:
            db_article.status = status
            self.session.add(db_article)
            self.session.commit()
            self.session.refresh(db_article)
            return db_article
        return None

    def get_articles_by_status(self, status: str) -> List[Article]:
        """Get all articles with a specific status.

        Args:
            status: Status to filter by

        Returns:
            List of articles with the specified status
        """
        statement = select(Article).where(Article.status == status)
        return self.session.exec(statement).all()

    def get_entities_by_article(self, article_id: int) -> List[Entity]:
        """Get all entities for an article.

        Args:
            article_id: ID of the article

        Returns:
            List of entities for the article
        """
        statement = select(Entity).where(Entity.article_id == article_id)
        return self.session.exec(statement).all()

    def get_analysis_results_by_article(self, article_id: int) -> List[AnalysisResult]:
        """Get all analysis results for an article.

        Args:
            article_id: ID of the article

        Returns:
            List of analysis results for the article
        """
        statement = select(AnalysisResult).where(AnalysisResult.article_id == article_id)
        return self.session.exec(statement).all()

    # Entity Tracking Methods
    
    def create_canonical_entity(self, entity_data: Union[Dict[str, Any], CanonicalEntityCreate]) -> CanonicalEntity:
        """Create a new canonical entity in the database.

        Args:
            entity_data: Canonical entity data to create (Dict or CanonicalEntityCreate model)

        Returns:
            Created canonical entity
        """
        # Handle either Dict or CanonicalEntityCreate
        if isinstance(entity_data, dict):
            db_entity = CanonicalEntity(**entity_data)
        else:
            # Convert SQLModel to dict
            data_dict = entity_data.model_dump()
            db_entity = CanonicalEntity(**data_dict)
            
        self.session.add(db_entity)
        self.session.commit()
        self.session.refresh(db_entity)
        return db_entity

    def get_canonical_entity(self, entity_id: int) -> Optional[CanonicalEntity]:
        """Get a canonical entity by ID.

        Args:
            entity_id: ID of the canonical entity to get

        Returns:
            Canonical entity if found, None otherwise
        """
        statement = select(CanonicalEntity).where(CanonicalEntity.id == entity_id)
        return self.session.exec(statement).first()

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
        statement = select(CanonicalEntity).where(
            CanonicalEntity.name == name, 
            CanonicalEntity.entity_type == entity_type
        )
        return self.session.exec(statement).first()

    def add_entity_mention_context(
        self, context_data: Dict[str, Any]
    ) -> EntityMentionContext:
        """Add context for an entity mention.

        Args:
            context_data: Entity mention context data to add

        Returns:
            Created entity mention context
        """
        db_context = EntityMentionContext(**context_data)
        self.session.add(db_context)
        self.session.commit()
        self.session.refresh(db_context)
        return db_context

    def add_entity_profile(self, profile_data: Dict[str, Any]) -> EntityProfile:
        """Add a new entity profile.

        Args:
            profile_data: Entity profile data to add

        Returns:
            Created entity profile
        """
        # Check if profile already exists
        canonical_entity_id = profile_data.get('canonical_entity_id')
        statement = select(EntityProfile).where(
            EntityProfile.canonical_entity_id == canonical_entity_id
        )
        existing_profile = self.session.exec(statement).first()
        
        if existing_profile:
            raise ValueError(f"Profile already exists for entity {canonical_entity_id}")
            
        db_profile = EntityProfile(**profile_data)
        self.session.add(db_profile)
        self.session.commit()
        self.session.refresh(db_profile)
        return db_profile

    def update_entity_profile(self, profile_data: Dict[str, Any]) -> EntityProfile:
        """Update an entity profile.

        Args:
            profile_data: Profile data to update

        Returns:
            Updated profile
        """
        # Get existing profile
        canonical_entity_id = profile_data.get('canonical_entity_id')
        profile_type = profile_data.get('profile_type')
        statement = select(EntityProfile).where(
            EntityProfile.canonical_entity_id == canonical_entity_id,
            EntityProfile.profile_type == profile_type
        )
        db_profile = self.session.exec(statement).first()
        
        if db_profile:
            # Update profile data
            db_profile.content = profile_data.get('content', db_profile.content)
            db_profile.profile_metadata = profile_data.get('profile_metadata', db_profile.profile_metadata)
            db_profile.updated_at = datetime.now(timezone.utc)
            
            self.session.add(db_profile)
            self.session.commit()
            self.session.refresh(db_profile)
            return db_profile
        
        # If profile doesn't exist, create it
        return self.add_entity_profile(profile_data)

    def add_entity_relationship(
        self, relationship_data: Dict[str, Any]
    ) -> EntityRelationship:
        """Add a relationship between entities.

        Args:
            relationship_data: Entity relationship data to add

        Returns:
            Created entity relationship
        """
        # Check if relationship already exists
        source_entity_id = relationship_data.get('source_entity_id')
        target_entity_id = relationship_data.get('target_entity_id')
        relationship_type = relationship_data.get('relationship_type')
        
        existing = (
            self.session.execute(
                select(entity_relationships).where(
                    entity_relationships.c.source_entity_id == source_entity_id,
                    entity_relationships.c.target_entity_id == target_entity_id,
                    entity_relationships.c.relationship_type == relationship_type,
                )
            ).first()
        )
        
        if existing:
            # Update existing relationship
            self.session.execute(
                entity_relationships.update()
                .where(
                    entity_relationships.c.source_entity_id == source_entity_id,
                    entity_relationships.c.target_entity_id == target_entity_id,
                    entity_relationships.c.relationship_type == relationship_type,
                )
                .values(
                    confidence=relationship_data.get('confidence', existing.confidence),
                    evidence=relationship_data.get('evidence', existing.evidence),
                    updated_at=datetime.now(timezone.utc),
                )
            )
            self.session.commit()
            
            # Get the updated relationship
            updated = (
                self.session.execute(
                    select(entity_relationships).where(
                        entity_relationships.c.source_entity_id == source_entity_id,
                        entity_relationships.c.target_entity_id == target_entity_id,
                        entity_relationships.c.relationship_type == relationship_type,
                    )
                ).first()
            )
            
            if updated:
                return EntityRelationship(
                    id=updated.id,
                    source_entity_id=updated.source_entity_id,
                    target_entity_id=updated.target_entity_id,
                    relationship_type=updated.relationship_type,
                    confidence=updated.confidence,
                    evidence=updated.evidence,
                    created_at=updated.created_at,
                    updated_at=updated.updated_at,
                )
        
        # Create new relationship
        current_time = datetime.now(timezone.utc)
        insert_values = {
            'source_entity_id': source_entity_id,
            'target_entity_id': target_entity_id,
            'relationship_type': relationship_type,
            'confidence': relationship_data.get('confidence', 1.0),
            'evidence': relationship_data.get('evidence'),
            'created_at': current_time,
            'updated_at': current_time,
        }
        
        result = self.session.execute(
            entity_relationships.insert().values(**insert_values)
        )
        self.session.commit()
        
        # Get the created relationship
        created = (
            self.session.execute(
                select(entity_relationships).where(
                    entity_relationships.c.source_entity_id == source_entity_id,
                    entity_relationships.c.target_entity_id == target_entity_id,
                    entity_relationships.c.relationship_type == relationship_type,
                )
            ).first()
        )
        
        if created:
            return EntityRelationship(
                id=created.id,
                source_entity_id=created.source_entity_id,
                target_entity_id=created.target_entity_id,
                relationship_type=created.relationship_type,
                confidence=created.confidence,
                evidence=created.evidence,
                created_at=created.created_at,
                updated_at=created.updated_at,
            )
        
        raise ValueError("Failed to create entity relationship")

    def get_entity_mentions_count(self, entity_id: int) -> int:
        """Get the count of mentions for an entity.

        Args:
            entity_id: ID of the entity

        Returns:
            Count of mentions
        """
        result = self.session.execute(
            select(func.count(entity_mentions.c.id))
            .where(entity_mentions.c.canonical_entity_id == entity_id)
        ).scalar()
        
        return result or 0

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
        results = self.session.execute(
            select(
                Article.published_at,
                func.count(entity_mentions.c.id).label("mention_count"),
            )
            .join(entity_mentions, Article.id == entity_mentions.c.article_id)
            .where(
                entity_mentions.c.canonical_entity_id == entity_id,
                Article.published_at >= start_date,
                Article.published_at <= end_date,
            )
            .group_by(Article.published_at)
            .order_by(Article.published_at)
        ).all()
        
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
        results = self.session.execute(
            select(
                Article.published_at,
                func.avg(EntityMentionContext.sentiment_score).label("avg_sentiment"),
            )
            .join(entity_mentions, Article.id == entity_mentions.c.article_id)
            .join(
                EntityMentionContext,
                EntityMentionContext.entity_id == entity_mentions.c.entity_id,
            )
            .where(
                entity_mentions.c.canonical_entity_id == entity_id,
                Article.published_at >= start_date,
                Article.published_at <= end_date,
            )
            .group_by(Article.published_at)
            .order_by(Article.published_at)
        ).all()
        
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
        statement = select(CanonicalEntity).where(CanonicalEntity.entity_type == entity_type)
        return self.session.exec(statement).all()

    def get_all_canonical_entities(self, entity_type: Optional[str] = None) -> List[CanonicalEntity]:
        """Get all canonical entities, optionally filtered by type.

        Args:
            entity_type: Optional type to filter by

        Returns:
            List of canonical entities
        """
        statement = select(CanonicalEntity)
        if entity_type:
            statement = statement.where(CanonicalEntity.entity_type == entity_type)
        return self.session.exec(statement).all()

    def get_entity_profile(self, entity_id: int) -> Optional[EntityProfile]:
        """Get the profile for an entity.

        Args:
            entity_id: ID of the entity

        Returns:
            Entity profile if found, None otherwise
        """
        statement = select(EntityProfile).where(EntityProfile.canonical_entity_id == entity_id)
        return self.session.exec(statement).first()

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
        statement = select(Article).join(
            entity_mentions, Article.id == entity_mentions.c.article_id
        ).where(
            entity_mentions.c.canonical_entity_id == entity_id,
            Article.published_at >= start_date,
            Article.published_at <= end_date,
        )
        return self.session.exec(statement).all()

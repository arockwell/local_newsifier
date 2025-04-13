"""Database manager for handling database operations."""

from typing import Dict, List, Optional
from datetime import datetime, timezone

from sqlalchemy.orm import Session
from sqlalchemy import func

from ..models.database import (AnalysisResult, AnalysisResultCreate,
                               AnalysisResultDB, Article, ArticleCreate,
                               ArticleDB, Entity, EntityCreate, EntityDB)
from ..models.entity_tracking import (CanonicalEntity, CanonicalEntityCreate,
                                    CanonicalEntityDB, EntityMentionContext,
                                    EntityMentionContextCreate, EntityMentionContextDB,
                                    EntityProfile, EntityProfileCreate, EntityProfileDB,
                                    EntityRelationship, EntityRelationshipCreate,
                                    entity_mentions, entity_relationships)


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
        db_article = ArticleDB(**article.model_dump())
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
            db_article.status = status
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
        """Add or update an entity profile.

        Args:
            profile: Entity profile data to add

        Returns:
            Created or updated entity profile
        """
        # Check if a profile exists for this canonical entity
        db_profile = (
            self.session.query(EntityProfileDB)
            .filter(EntityProfileDB.canonical_entity_id == profile.canonical_entity_id)
            .first()
        )

        if db_profile:
            # Update existing profile
            for key, value in profile.model_dump().items():
                if key != "id" and value is not None:  # Skip id and None values
                    setattr(db_profile, key, value)
            
            db_profile.last_updated = datetime.now(timezone.utc)
            self.session.commit()
            self.session.refresh(db_profile)
            return EntityProfile.model_validate(db_profile)
        else:
            # Create new profile
            db_profile = EntityProfileDB(**profile.model_dump())
            self.session.add(db_profile)
            self.session.commit()
            self.session.refresh(db_profile)
            return EntityProfile.model_validate(db_profile)

    def add_entity_relationship(
        self, relationship: EntityRelationshipCreate
    ) -> EntityRelationship:
        """Add a relationship between entities.

        Args:
            relationship: Entity relationship data to add

        Returns:
            Created entity relationship
        """
        # Check if the relationship already exists
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
                    entity_relationships.c.id == existing.id
                )
                .values(
                    confidence=relationship.confidence,
                    evidence=relationship.evidence,
                    updated_at=datetime.now(timezone.utc),
                )
            )
            self.session.commit()
        else:
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

        # Get the created/updated relationship
        db_relationship = (
            self.session.query(entity_relationships)
            .filter(
                entity_relationships.c.source_entity_id == relationship.source_entity_id,
                entity_relationships.c.target_entity_id == relationship.target_entity_id,
                entity_relationships.c.relationship_type == relationship.relationship_type,
            )
            .first()
        )

        # Load the source and target entities
        source_entity = self.get_canonical_entity(relationship.source_entity_id)
        target_entity = self.get_canonical_entity(relationship.target_entity_id)

        # Create and return the relationship model
        return EntityRelationship(
            id=db_relationship.id,
            source_entity_id=relationship.source_entity_id,
            target_entity_id=relationship.target_entity_id,
            relationship_type=relationship.relationship_type,
            confidence=relationship.confidence,
            evidence=relationship.evidence,
            created_at=db_relationship.created_at,
            updated_at=db_relationship.updated_at,
            source_entity=source_entity,
            target_entity=target_entity,
        )
        
    def get_entity_mentions_count(self, entity_id: int) -> int:
        """Get the number of mentions for a specific entity.

        Args:
            entity_id: ID of the canonical entity

        Returns:
            Number of mentions
        """
        return (
            self.session.query(func.count(entity_mentions.c.id))
            .filter(entity_mentions.c.canonical_entity_id == entity_id)
            .scalar() or 0
        )
        
    def get_entity_timeline(
        self, entity_id: int, start_date: datetime, end_date: datetime
    ) -> List[Dict]:
        """Get timeline of mentions for a specific entity.

        Args:
            entity_id: ID of the canonical entity
            start_date: Start date for the timeline
            end_date: End date for the timeline

        Returns:
            List of mentions with article details
        """
        # Join entity mentions with entities and articles to get all relevant data
        results = (
            self.session.query(
                EntityMentionContextDB,
                ArticleDB.title,
                ArticleDB.url,
                ArticleDB.published_at,
            )
            .join(EntityDB, EntityMentionContextDB.entity_id == EntityDB.id)
            .join(entity_mentions, entity_mentions.c.entity_id == EntityDB.id)
            .join(ArticleDB, EntityDB.article_id == ArticleDB.id)
            .filter(
                entity_mentions.c.canonical_entity_id == entity_id,
                ArticleDB.published_at >= start_date,
                ArticleDB.published_at <= end_date,
            )
            .order_by(ArticleDB.published_at)
            .all()
        )
        
        # Transform results into timeline format
        timeline = []
        for context, title, url, published_at in results:
            timeline.append({
                "date": published_at,
                "context": context.context_text,
                "sentiment_score": context.sentiment_score,
                "article": {
                    "title": title,
                    "url": url
                }
            })
            
        return timeline
        
    def get_entity_sentiment_trend(
        self, entity_id: int, start_date: datetime, end_date: datetime
    ) -> List[Dict]:
        """Get sentiment trend for a specific entity over time.

        Args:
            entity_id: ID of the canonical entity
            start_date: Start date for the trend
            end_date: End date for the trend

        Returns:
            List of sentiment scores by date
        """
        # Query average sentiment by day
        results = (
            self.session.query(
                func.date(ArticleDB.published_at).label("date"),
                func.avg(EntityMentionContextDB.sentiment_score).label("avg_sentiment"),
                func.count(EntityMentionContextDB.id).label("mention_count"),
            )
            .join(EntityDB, EntityMentionContextDB.entity_id == EntityDB.id)
            .join(entity_mentions, entity_mentions.c.entity_id == EntityDB.id)
            .join(ArticleDB, EntityDB.article_id == ArticleDB.id)
            .filter(
                entity_mentions.c.canonical_entity_id == entity_id,
                ArticleDB.published_at >= start_date,
                ArticleDB.published_at <= end_date,
                EntityMentionContextDB.sentiment_score.isnot(None),
            )
            .group_by(func.date(ArticleDB.published_at))
            .order_by(func.date(ArticleDB.published_at))
            .all()
        )
        
        # Transform results into trend format
        trend = [
            {
                "date": date,
                "avg_sentiment": float(avg_sentiment),
                "mention_count": int(mention_count),
            }
            for date, avg_sentiment, mention_count in results
        ]
            
        return trend
    
    def get_canonical_entities_by_type(self, entity_type: str) -> List[CanonicalEntity]:
        """Get all canonical entities of a specific type.

        Args:
            entity_type: Type of entities to get (e.g., "PERSON")

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
            entity_type: Optional type filter

        Returns:
            List of canonical entities
        """
        query = self.session.query(CanonicalEntityDB)
        if entity_type:
            query = query.filter(CanonicalEntityDB.entity_type == entity_type)
        db_entities = query.all()
        return [CanonicalEntity.model_validate(entity) for entity in db_entities]
    
    def get_entity_profile(self, entity_id: int) -> Optional[EntityProfile]:
        """Get entity profile for a canonical entity.

        Args:
            entity_id: ID of the canonical entity

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
        """Get articles mentioning a specific entity.

        Args:
            entity_id: ID of the canonical entity
            start_date: Start date for the article search
            end_date: End date for the article search

        Returns:
            List of articles mentioning the entity
        """
        # Use entity_mentions to find articles mentioning this entity
        article_ids = (
            self.session.query(EntityDB.article_id)
            .join(entity_mentions, entity_mentions.c.entity_id == EntityDB.id)
            .filter(
                entity_mentions.c.canonical_entity_id == entity_id,
                EntityDB.created_at >= start_date,
                EntityDB.created_at <= end_date,
            )
            .distinct()
            .all()
        )
        
        # Flatten the list of tuples
        article_ids = [id[0] for id in article_ids]
        
        # Get articles
        db_articles = (
            self.session.query(ArticleDB)
            .filter(ArticleDB.id.in_(article_ids))
            .all()
        )
        
        return [Article.model_validate(article) for article in db_articles]

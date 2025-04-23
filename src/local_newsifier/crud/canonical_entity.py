"""CRUD operations for canonical entities."""

from datetime import datetime
from typing import List, Optional

from sqlmodel import Session, select, func, col

from local_newsifier.crud.base import CRUDBase
from local_newsifier.models.article import Article
from local_newsifier.models.entity_tracking import CanonicalEntity, EntityMention


class CRUDCanonicalEntity(CRUDBase[CanonicalEntity]):
    """CRUD operations for canonical entities."""

    def get_by_name(
        self, db: Session, *, name: str, entity_type: str
    ) -> Optional[CanonicalEntity]:
        """Get a canonical entity by name and type.

        Args:
            db: Database session
            name: Name of the canonical entity
            entity_type: Type of the entity (e.g., "PERSON")

        Returns:
            Canonical entity if found, None otherwise
        """
        result = db.execute(select(CanonicalEntity).where(
            CanonicalEntity.name == name,
            CanonicalEntity.entity_type == entity_type
        )).first()
        return result[0] if result else None

    def get_by_type(
        self, db: Session, *, entity_type: str
    ) -> List[CanonicalEntity]:
        """Get all canonical entities of a specific type.

        Args:
            db: Database session
            entity_type: Type of entities to get

        Returns:
            List of canonical entities
        """
        results = db.execute(select(CanonicalEntity).where(
            CanonicalEntity.entity_type == entity_type
        )).all()
        return [row[0] for row in results]

    def get_all(
        self, db: Session, *, entity_type: Optional[str] = None
    ) -> List[CanonicalEntity]:
        """Get all canonical entities, optionally filtered by type.

        Args:
            db: Database session
            entity_type: Optional type to filter by

        Returns:
            List of canonical entities
        """
        query = select(CanonicalEntity)
        if entity_type:
            query = query.where(CanonicalEntity.entity_type == entity_type)
        results = db.execute(query).all()
        return [row[0] for row in results]

    def get_mentions_count(self, db: Session, *, entity_id: int) -> int:
        """Get the count of mentions for an entity.

        Args:
            db: Database session
            entity_id: ID of the entity

        Returns:
            Count of mentions
        """
        statement = select(func.count(EntityMention.id)).where(
            EntityMention.canonical_entity_id == entity_id
        )
        result = db.execute(statement)
        return result.one_or_none()[0] or 0

    def get_entity_timeline(
        self,
        db: Session,
        *,
        entity_id: int,
        start_date: datetime,
        end_date: datetime
    ) -> List[dict]:
        """Get the timeline of entity mentions.

        Args:
            db: Database session
            entity_id: ID of the entity
            start_date: Start date for the timeline
            end_date: End date for the timeline

        Returns:
            List of timeline entries
        """
        statement = select(
            Article.published_at,
            func.count(EntityMention.id).label("mention_count")
        ).join(
            EntityMention, Article.id == EntityMention.article_id
        ).where(
            EntityMention.canonical_entity_id == entity_id,
            Article.published_at >= start_date,
            Article.published_at <= end_date
        ).group_by(
            Article.published_at
        ).order_by(
            Article.published_at
        )
        
        results = db.execute(statement)
        
        return [
            {
                "date": date,
                "mention_count": count,
            }
            for date, count in results
        ]

    def get_articles_mentioning_entity(
        self,
        db: Session,
        *,
        entity_id: int,
        start_date: datetime,
        end_date: datetime
    ) -> List[Article]:
        """Get all articles mentioning an entity within a date range.

        Args:
            db: Database session
            entity_id: ID of the entity
            start_date: Start date for the range
            end_date: End date for the range

        Returns:
            List of articles mentioning the entity
        """
        results = db.execute(select(Article).join(
            EntityMention, Article.id == EntityMention.article_id
        ).where(
            EntityMention.canonical_entity_id == entity_id,
            Article.published_at >= start_date,
            Article.published_at <= end_date
        )).all()
        return [row[0] for row in results]


canonical_entity = CRUDCanonicalEntity(CanonicalEntity)

"""CRUD operations for canonical entities."""

from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy.orm import Session
from sqlalchemy import func

from local_newsifier.crud.base import CRUDBase
from local_newsifier.models.entity_tracking import (
    CanonicalEntityDB, CanonicalEntity, CanonicalEntityCreate,
    entity_mentions
)
from local_newsifier.models.database.article import ArticleDB


class CRUDCanonicalEntity(CRUDBase[CanonicalEntityDB, CanonicalEntityCreate, CanonicalEntity]):
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
        db_entity = (
            db.query(CanonicalEntityDB)
            .filter(
                CanonicalEntityDB.name == name, 
                CanonicalEntityDB.entity_type == entity_type
            )
            .first()
        )
        return CanonicalEntity.model_validate(db_entity) if db_entity else None

    def get_by_type(self, db: Session, *, entity_type: str) -> List[CanonicalEntity]:
        """Get all canonical entities of a specific type.

        Args:
            db: Database session
            entity_type: Type of entities to get

        Returns:
            List of canonical entities
        """
        db_entities = (
            db.query(CanonicalEntityDB)
            .filter(CanonicalEntityDB.entity_type == entity_type)
            .all()
        )
        return [CanonicalEntity.model_validate(entity) for entity in db_entities]

    def get_all(self, db: Session, *, entity_type: Optional[str] = None) -> List[CanonicalEntity]:
        """Get all canonical entities, optionally filtered by type.

        Args:
            db: Database session
            entity_type: Optional type to filter by

        Returns:
            List of canonical entities
        """
        query = db.query(CanonicalEntityDB)
        if entity_type:
            query = query.filter(CanonicalEntityDB.entity_type == entity_type)
        db_entities = query.all()
        return [CanonicalEntity.model_validate(entity) for entity in db_entities]

    def get_mentions_count(self, db: Session, *, entity_id: int) -> int:
        """Get the count of mentions for an entity.

        Args:
            db: Database session
            entity_id: ID of the entity

        Returns:
            Count of mentions
        """
        return (
            db.query(func.count(entity_mentions.c.id))
            .filter(entity_mentions.c.canonical_entity_id == entity_id)
            .scalar()
        )

    def get_entity_timeline(
        self, db: Session, *, entity_id: int, start_date: datetime, end_date: datetime
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
        results = (
            db.query(
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

    def get_articles_mentioning_entity(
        self, db: Session, *, entity_id: int, start_date: datetime, end_date: datetime
    ) -> List[ArticleDB]:
        """Get all articles mentioning an entity within a date range.

        Args:
            db: Database session
            entity_id: ID of the entity
            start_date: Start date for the range
            end_date: End date for the range

        Returns:
            List of articles mentioning the entity
        """
        db_articles = (
            db.query(ArticleDB)
            .join(entity_mentions, ArticleDB.id == entity_mentions.c.article_id)
            .filter(
                entity_mentions.c.canonical_entity_id == entity_id,
                ArticleDB.published_at >= start_date,
                ArticleDB.published_at <= end_date,
            )
            .all()
        )
        return db_articles


canonical_entity = CRUDCanonicalEntity(CanonicalEntityDB, CanonicalEntity)
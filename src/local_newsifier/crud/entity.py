"""CRUD operations for entities."""

from datetime import datetime
from typing import List, Optional

from sqlmodel import Session, select, join

from local_newsifier.crud.base import CRUDBase
from local_newsifier.models.entity import Entity
from local_newsifier.models.article import Article


class CRUDEntity(CRUDBase[Entity]):
    """CRUD operations for entities."""

    def get_by_article(self, db: Session, *, article_id: int) -> List[Entity]:
        """Get all entities for an article.

        Args:
            db: Database session
            article_id: ID of the article

        Returns:
            List of entities for the article
        """
        results = db.execute(select(Entity).where(Entity.article_id == article_id)).all()
        return [row[0] for row in results]

    def get_by_text_and_article(
        self, db: Session, *, text: str, article_id: int
    ) -> Optional[Entity]:
        """Get an entity by text and article ID.

        Args:
            db: Database session
            text: Entity text
            article_id: Article ID

        Returns:
            Entity if found, None otherwise
        """
        result = db.execute(select(Entity).where(
            Entity.text == text, Entity.article_id == article_id
        )).first()
        return result[0] if result else None
        
    def get_by_date_range_and_types(
        self, 
        db: Session, 
        *, 
        start_date: datetime, 
        end_date: datetime,
        entity_types: List[str] = None
    ) -> List[Entity]:
        """Get entities by date range and entity types.

        Args:
            db: Database session
            start_date: Start date
            end_date: End date
            entity_types: List of entity types to include

        Returns:
            List of entities within the date range and with the specified types
        """
        # Join with Article to filter by published_at
        query = select(Entity).join(
            Article, Entity.article_id == Article.id
        ).where(
            Article.published_at >= start_date,
            Article.published_at <= end_date
        )
        
        # Add entity type filter if provided
        if entity_types:
            query = query.where(Entity.entity_type.in_(entity_types))
            
        results = db.execute(query).all()
        return [row[0] for row in results]


entity = CRUDEntity(Entity)

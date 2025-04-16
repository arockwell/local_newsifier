"""CRUD operations for entities."""

from typing import List, Optional

from sqlalchemy.orm import Session
from sqlmodel import select

from local_newsifier.crud.base import CRUDBase
from local_newsifier.models.database.entity import Entity


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
        statement = select(Entity).where(Entity.article_id == article_id)
        results = db.exec(statement)
        return results.all()

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
        statement = select(Entity).where(
            Entity.text == text, Entity.article_id == article_id
        )
        results = db.exec(statement)
        return results.first()


entity = CRUDEntity(Entity)

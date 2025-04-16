"""CRUD operations for entities."""

from typing import List, Optional

from sqlalchemy.orm import Session

from local_newsifier.crud.base import CRUDBase
from local_newsifier.models.database.entity import EntityDB
from local_newsifier.models.pydantic_models import Entity, EntityCreate


class CRUDEntity(CRUDBase[EntityDB, EntityCreate, Entity]):
    """CRUD operations for entities."""

    def get_by_article(self, db: Session, *, article_id: int) -> List[Entity]:
        """Get all entities for an article.

        Args:
            db: Database session
            article_id: ID of the article

        Returns:
            List of entities for the article
        """
        db_entities = (
            db.query(EntityDB).filter(EntityDB.article_id == article_id).all()
        )
        return [Entity.model_validate(entity) for entity in db_entities]

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
        db_entity = (
            db.query(EntityDB)
            .filter(EntityDB.text == text, EntityDB.article_id == article_id)
            .first()
        )
        return Entity.model_validate(db_entity) if db_entity else None


entity = CRUDEntity(EntityDB, Entity)

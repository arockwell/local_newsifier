"""Error-handled CRUD operations for entities."""

from datetime import datetime
from typing import List

from sqlmodel import Session, select

from local_newsifier.crud.error_handled_base import (EntityNotFoundError,
                                                     ErrorHandledCRUD,
                                                     handle_crud_error)
from local_newsifier.models.article import Article
from local_newsifier.models.entity import Entity


class ErrorHandledCRUDEntity(ErrorHandledCRUD[Entity]):
    """CRUD operations for entities with standardized error handling."""

    @handle_crud_error
    def get_by_article(self, db: Session, *, article_id: int) -> List[Entity]:
        """Get all entities for an article with error handling.

        Args:
            db: Database session
            article_id: ID of the article

        Returns:
            List of entities for the article

        Raises:
            DatabaseConnectionError: If there's a connection issue
            TransactionError: If there's a database transaction error
        """
        return db.exec(select(Entity).where(Entity.article_id == article_id)).all()

    @handle_crud_error
    def get_by_text_and_article(
        self, db: Session, *, text: str, article_id: int
    ) -> Entity:
        """Get an entity by text and article ID with error handling.

        Args:
            db: Database session
            text: Entity text
            article_id: Article ID

        Returns:
            Entity if found

        Raises:
            EntityNotFoundError: If the entity with the given text and article ID does not exist
            DatabaseConnectionError: If there's a connection issue
            TransactionError: If there's a database transaction error
        """
        result = db.exec(
            select(Entity).where(Entity.text == text, Entity.article_id == article_id)
        ).first()

        if result is None:
            raise EntityNotFoundError(
                f"Entity with text '{text}' not found in article {article_id}",
                context={
                    "text": text,
                    "article_id": article_id,
                    "model": self.model.__name__,
                },
            )

        return result

    @handle_crud_error
    def get_by_date_range_and_types(
        self,
        db: Session,
        *,
        start_date: datetime,
        end_date: datetime,
        entity_types: List[str] = None,
    ) -> List[Entity]:
        """Get entities by date range and entity types with error handling.

        Args:
            db: Database session
            start_date: Start date
            end_date: End date
            entity_types: List of entity types to include

        Returns:
            List of entities within the date range and with the specified types

        Raises:
            DatabaseConnectionError: If there's a connection issue
            TransactionError: If there's a database transaction error
        """
        # Join with Article to filter by published_at
        query = (
            select(Entity)
            .join(Article, Entity.article_id == Article.id)
            .where(Article.published_at >= start_date, Article.published_at <= end_date)
        )

        # Add entity type filter if provided
        if entity_types:
            query = query.where(Entity.entity_type.in_(entity_types))

        return db.exec(query).all()


# Create a singleton instance of the error handled entity CRUD
error_handled_entity = ErrorHandledCRUDEntity(Entity)

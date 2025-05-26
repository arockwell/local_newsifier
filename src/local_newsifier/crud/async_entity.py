"""Async CRUD operations for entities."""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from local_newsifier.crud.async_base import AsyncCRUDBase
from local_newsifier.models.article import Article
from local_newsifier.models.entity import Entity


class AsyncCRUDEntity(AsyncCRUDBase[Entity, Entity, Entity]):
    """Async CRUD operations for entities."""

    async def get_by_article(self, session: AsyncSession, *, article_id: int) -> List[Entity]:
        """Get all entities for an article.

        Args:
            session: Async database session
            article_id: ID of the article

        Returns:
            List of entities for the article
        """
        result = await session.execute(select(Entity).where(Entity.article_id == article_id))
        return result.scalars().all()

    async def get_by_text_and_article(
        self, session: AsyncSession, *, text: str, article_id: int
    ) -> Optional[Entity]:
        """Get an entity by text and article ID.

        Args:
            session: Async database session
            text: Entity text
            article_id: Article ID

        Returns:
            Entity if found, None otherwise
        """
        result = await session.execute(
            select(Entity).where(Entity.text == text, Entity.article_id == article_id)
        )
        return result.scalar_one_or_none()

    async def get_by_date_range_and_types(
        self,
        session: AsyncSession,
        *,
        start_date: datetime,
        end_date: datetime,
        entity_types: List[str] = None,
    ) -> List[Entity]:
        """Get entities by date range and entity types.

        Args:
            session: Async database session
            start_date: Start date
            end_date: End date
            entity_types: List of entity types to include

        Returns:
            List of entities within the date range and with the specified types
        """
        # Join with Article to filter by published_at
        query = (
            select(Entity)
            .join(Article, Entity.article_id == Article.id)
            .where(
                Article.published_at >= start_date,
                Article.published_at <= end_date,
            )
        )

        # Add entity type filter if provided
        if entity_types:
            query = query.where(Entity.entity_type.in_(entity_types))

        result = await session.execute(query)
        return result.scalars().all()

    async def create_bulk(self, session: AsyncSession, *, entities: List[Entity]) -> List[Entity]:
        """Create multiple entities in bulk.

        Args:
            session: Async database session
            entities: List of Entity objects to create

        Returns:
            List of created entities
        """
        session.add_all(entities)
        await session.commit()

        # Refresh all entities to get their IDs
        for entity in entities:
            await session.refresh(entity)

        return entities

    async def get_with_article(self, session: AsyncSession, *, entity_id: int) -> Optional[Entity]:
        """Get an entity with its associated article eagerly loaded.

        Args:
            session: Async database session
            entity_id: ID of the entity

        Returns:
            Entity with article loaded, or None if not found
        """
        result = await session.execute(
            select(Entity).options(selectinload(Entity.article)).where(Entity.id == entity_id)
        )
        return result.scalar_one_or_none()


# Global instance for easy import
async_entity = AsyncCRUDEntity(Entity)

"""Async CRUD operations for articles."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from local_newsifier.crud.async_base import AsyncCRUDBase
from local_newsifier.models.article import Article


class AsyncCRUDArticle(AsyncCRUDBase[Article, Article, Article]):
    """Async CRUD operations for articles."""

    async def get_by_url(self, session: AsyncSession, *, url: str) -> Optional[Article]:
        """Get an article by URL.

        Args:
            session: Async database session
            url: URL of the article to get

        Returns:
            Article if found, None otherwise
        """
        result = await session.execute(select(Article).where(Article.url == url))
        return result.scalar_one_or_none()

    async def create(
        self, session: AsyncSession, *, obj_in: Union[Dict[str, Any], Article]
    ) -> Article:
        """Create a new article.

        Args:
            session: Async database session
            obj_in: Article data to create

        Returns:
            Created article
        """
        # Handle dict or model instance
        if isinstance(obj_in, dict):
            article_data = obj_in
        else:
            article_data = obj_in.model_dump(exclude_unset=True)

        # Add scraped_at if not provided
        if "scraped_at" not in article_data or article_data["scraped_at"] is None:
            article_data["scraped_at"] = datetime.now(timezone.utc)

        db_article = Article(**article_data)
        session.add(db_article)
        await session.commit()
        await session.refresh(db_article)
        return db_article

    async def update_status(
        self, session: AsyncSession, *, article_id: int, status: str
    ) -> Optional[Article]:
        """Update an article's status.

        Args:
            session: Async database session
            article_id: ID of the article to update
            status: New status

        Returns:
            Updated article if found, None otherwise
        """
        result = await session.execute(select(Article).where(Article.id == article_id))
        db_article = result.scalar_one_or_none()

        if db_article:
            db_article.status = status
            session.add(db_article)
            await session.commit()
            await session.refresh(db_article)
            return db_article
        return None

    async def get_by_status(self, session: AsyncSession, *, status: str) -> List[Article]:
        """Get all articles with a specific status.

        Args:
            session: Async database session
            status: Status to filter by

        Returns:
            List of articles with the specified status
        """
        result = await session.execute(select(Article).where(Article.status == status))
        return result.scalars().all()

    async def get_by_date_range(
        self,
        session: AsyncSession,
        *,
        start_date: datetime,
        end_date: datetime,
        source: Optional[str] = None,
    ) -> List[Article]:
        """Get articles within a date range.

        Args:
            session: Async database session
            start_date: Start date
            end_date: End date
            source: Optional source to filter by

        Returns:
            List of articles within the date range
        """
        query = select(Article).where(
            Article.published_at >= start_date, Article.published_at <= end_date
        )

        # Add source filter if provided
        if source:
            query = query.where(Article.source == source)

        # Order by published date
        query = query.order_by(Article.published_at)

        result = await session.execute(query)
        return result.scalars().all()


# Global instance for easy import
async_article = AsyncCRUDArticle(Article)

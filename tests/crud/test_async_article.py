"""Tests for the async article CRUD module."""

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select

from local_newsifier.crud.async_article import AsyncCRUDArticle, async_article
from local_newsifier.models.article import Article


@pytest.mark.asyncio
class TestAsyncArticleCRUD:
    """Tests for AsyncCRUDArticle class."""

    async def test_create(self, async_db_session, sample_article_data):
        """Test creating a new article asynchronously."""
        article = await async_article.create(async_db_session, obj_in=sample_article_data)

        assert article is not None
        assert article.id is not None
        assert article.title == sample_article_data["title"]
        assert article.content == sample_article_data["content"]
        assert article.url == sample_article_data["url"]
        assert article.source == sample_article_data["source"]
        assert article.status == sample_article_data["status"]
        assert article.scraped_at is not None

        # Verify it was saved to the database
        result = await async_db_session.execute(select(Article).where(Article.id == article.id))
        db_article = result.scalar_one_or_none()
        assert db_article is not None
        assert db_article.title == sample_article_data["title"]

    async def test_create_with_missing_scraped_at(self, async_db_session, sample_article_data):
        """Test creating an article without scraped_at field."""
        # Remove scraped_at
        article_data = sample_article_data.copy()
        article_data.pop("scraped_at", None)

        article = await async_article.create(async_db_session, obj_in=article_data)

        assert article is not None
        assert article.scraped_at is not None  # Should be auto-populated

    async def test_create_with_model_instance(self, async_db_session, sample_article_data):
        """Test creating an article with a model instance."""
        article_instance = Article(**sample_article_data)
        article = await async_article.create(async_db_session, obj_in=article_instance)

        assert article is not None
        assert article.id is not None
        assert article.title == sample_article_data["title"]

    async def test_get_by_url(self, async_db_session, async_create_article):
        """Test getting an article by URL asynchronously."""
        article = await async_article.get_by_url(async_db_session, url=async_create_article.url)

        assert article is not None
        assert article.id == async_create_article.id
        assert article.url == async_create_article.url

    async def test_get_by_url_not_found(self, async_db_session):
        """Test getting a non-existent article by URL."""
        article = await async_article.get_by_url(
            async_db_session, url="https://nonexistent.com/article"
        )

        assert article is None

    async def test_update_status(self, async_db_session, async_create_article):
        """Test updating an article's status."""
        new_status = "processed"
        updated_article = await async_article.update_status(
            async_db_session, article_id=async_create_article.id, status=new_status
        )

        assert updated_article is not None
        assert updated_article.status == new_status

        # Verify it was updated in the database
        result = await async_db_session.execute(
            select(Article).where(Article.id == async_create_article.id)
        )
        db_article = result.scalar_one_or_none()
        assert db_article.status == new_status

    async def test_update_status_not_found(self, async_db_session):
        """Test updating a non-existent article's status."""
        updated_article = await async_article.update_status(
            async_db_session, article_id=99999, status="processed"
        )

        assert updated_article is None

    async def test_get_by_status(self, async_db_session):
        """Test getting articles by status."""
        # Create articles with different statuses
        statuses = ["new", "new", "processed", "error"]
        articles = []

        for i, status in enumerate(statuses):
            article = Article(
                title=f"Article {i}",
                content=f"Content {i}",
                url=f"https://example.com/article-{i}",
                source="test_source",
                status=status,
                published_at=datetime.now(timezone.utc),
                scraped_at=datetime.now(timezone.utc),
            )
            async_db_session.add(article)
            articles.append(article)
        await async_db_session.commit()

        # Test getting articles with "new" status
        new_articles = await async_article.get_by_status(async_db_session, status="new")
        assert len(new_articles) == 2

        # Test getting articles with "processed" status
        processed_articles = await async_article.get_by_status(async_db_session, status="processed")
        assert len(processed_articles) == 1

        # Test getting articles with "error" status
        error_articles = await async_article.get_by_status(async_db_session, status="error")
        assert len(error_articles) == 1

    async def test_get_by_date_range(self, async_db_session):
        """Test getting articles by date range."""
        now = datetime.now(timezone.utc)

        # Create articles with different publication dates
        article_dates = [
            now - timedelta(days=5),  # 5 days ago
            now - timedelta(days=3),  # 3 days ago
            now - timedelta(days=1),  # 1 day ago
            now + timedelta(days=1),  # 1 day in future
        ]

        articles = []
        for i, date in enumerate(article_dates):
            article = Article(
                title=f"Article {i}",
                content=f"Content of article {i}",
                url=f"https://example.com/article-{i}",
                source="test_source",
                published_at=date,
                status="new",
                scraped_at=now,
            )
            async_db_session.add(article)
            await async_db_session.commit()
            await async_db_session.refresh(article)
            articles.append(article)

        # Test getting articles within a date range
        start_date = now - timedelta(days=4)
        end_date = now
        articles_in_range = await async_article.get_by_date_range(
            async_db_session, start_date=start_date, end_date=end_date
        )

        assert len(articles_in_range) == 2  # Articles from 3 days ago and 1 day ago
        # Ensure published_at is timezone-aware for comparison
        for article in articles_in_range:
            if article.published_at.tzinfo is None:
                article.published_at = article.published_at.replace(tzinfo=timezone.utc)
            assert start_date <= article.published_at <= end_date

        # Test with source filter
        articles_with_source = await async_article.get_by_date_range(
            async_db_session,
            start_date=start_date,
            end_date=end_date,
            source="test_source",
        )
        assert len(articles_with_source) == 2

        # Test with non-matching source
        articles_no_match = await async_article.get_by_date_range(
            async_db_session,
            start_date=start_date,
            end_date=end_date,
            source="other_source",
        )
        assert len(articles_no_match) == 0

    async def test_singleton_instance(self):
        """Test that the async_article is a singleton instance of AsyncCRUDArticle."""
        assert isinstance(async_article, AsyncCRUDArticle)
        assert async_article.model == Article

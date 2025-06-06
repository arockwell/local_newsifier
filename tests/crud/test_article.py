"""Tests for the article CRUD module."""

from datetime import datetime, timedelta, timezone

from sqlmodel import select

from local_newsifier.crud.article import CRUDArticle
from local_newsifier.crud.article import article as article_crud
from local_newsifier.models.article import Article


class TestArticleCRUD:
    """Tests for ArticleCRUD class."""

    def test_create(self, db_session, sample_article_data):
        """Test creating a new article."""
        # Now we can create directly with a dict
        article = article_crud.create(db_session, obj_in=sample_article_data)

        assert article is not None
        assert article.id is not None
        assert article.title == sample_article_data["title"]
        assert article.url == sample_article_data["url"]
        assert article.status == sample_article_data["status"]
        assert article.source == sample_article_data["source"]

        # Verify it was saved to the database
        statement = select(Article).where(Article.id == article.id)
        result = db_session.exec(statement).first()  # Using exec instead of execute for SQLModel
        assert result is not None
        assert result.title == sample_article_data["title"]

    def test_create_with_missing_scraped_at(self, db_session, sample_article_data):
        """Test creating a new article with missing scraped_at field."""
        # Remove scraped_at from the data
        sample_article_data_copy = sample_article_data.copy()
        sample_article_data_copy.pop("scraped_at")

        article = article_crud.create(db_session, obj_in=sample_article_data_copy)

        assert article is not None
        assert article.id is not None
        assert article.scraped_at is not None  # Should be auto-populated

    def test_create_with_model_instance(self, db_session, sample_article_data):
        """Test creating an article with a model instance."""
        # Create from model instance directly
        article_instance = Article(**sample_article_data)
        article = article_crud.create(db_session, obj_in=article_instance)

        assert article is not None
        assert article.id is not None
        assert article.title == sample_article_data["title"]

    def test_get_by_url(self, db_session, create_article):
        """Test getting an article by URL."""
        article = article_crud.get_by_url(db_session, url=create_article.url)

        assert article is not None
        assert article.id == create_article.id
        assert article.title == create_article.title
        assert article.url == create_article.url

    def test_get_by_url_not_found(self, db_session):
        """Test getting a non-existent article by URL."""
        article = article_crud.get_by_url(db_session, url="https://example.com/nonexistent")

        assert article is None

    def test_update_status(self, db_session, create_article):
        """Test updating an article's status."""
        updated_article = article_crud.update_status(
            db_session, article_id=create_article.id, status="analyzed"
        )

        assert updated_article is not None
        assert updated_article.id == create_article.id
        assert updated_article.status == "analyzed"

        # Verify it was saved to the database
        statement = select(Article).where(Article.id == create_article.id)
        db_article = db_session.exec(
            statement
        ).first()  # Using exec instead of execute for SQLModel
        assert db_article is not None
        assert db_article.status == "analyzed"

    def test_update_status_not_found(self, db_session):
        """Test updating a non-existent article's status."""
        updated_article = article_crud.update_status(db_session, article_id=999, status="analyzed")

        assert updated_article is None

    def test_get_by_status(self, db_session):
        """Test getting articles by status."""
        # Create articles with different statuses
        statuses = ["new", "scraped", "analyzed", "saved", "new"]
        for i, status in enumerate(statuses):
            article = Article(
                title=f"Test Article {i}",
                content=f"This is test article {i}.",
                url=f"https://example.com/test-article-{i}",
                source="test_source",
                published_at=datetime.now(timezone.utc),
                status=status,
                scraped_at=datetime.now(timezone.utc),
            )
            db_session.add(article)
        db_session.commit()

        # Test getting articles with status "new"
        new_articles = article_crud.get_by_status(db_session, status="new")
        assert len(new_articles) == 2
        for article in new_articles:
            assert article.status == "new"

        # Test getting articles with status "analyzed"
        analyzed_articles = article_crud.get_by_status(db_session, status="analyzed")
        assert len(analyzed_articles) == 1
        assert analyzed_articles[0].status == "analyzed"

        # Test getting articles with a non-existent status
        nonexistent_articles = article_crud.get_by_status(db_session, status="nonexistent")
        assert len(nonexistent_articles) == 0

    def test_get_by_date_range(self, db_session):
        """Test getting articles within a date range."""
        # Create base timestamp
        now = datetime.now(timezone.utc)

        # Create articles with different publication dates
        dates = [
            now - timedelta(days=5),  # 5 days ago
            now - timedelta(days=3),  # 3 days ago
            now - timedelta(days=2),  # 2 days ago
            now - timedelta(days=1),  # 1 day ago
            now,  # Today
        ]

        sources = ["source1", "source2", "source1", "source2", "source1"]

        for i, (date, source) in enumerate(zip(dates, sources)):
            article = Article(
                title=f"Test Article {i}",
                content=f"This is test article {i}.",
                url=f"https://example.com/test-article-{i}",
                source=source,
                published_at=date,
                status="new",
                scraped_at=now,
            )
            db_session.add(article)
        db_session.commit()

        # Test getting articles within a date range (last 3 days)
        start_date = now - timedelta(days=3)
        end_date = now
        articles = article_crud.get_by_date_range(
            db_session, start_date=start_date, end_date=end_date
        )

        # Should return 4 articles (from 3 days ago until now)
        assert len(articles) == 4

        # Verify they're ordered by published_at
        for i in range(1, len(articles)):
            assert articles[i - 1].published_at <= articles[i].published_at

        # Test with source filter
        source1_articles = article_crud.get_by_date_range(
            db_session, start_date=start_date, end_date=end_date, source="source1"
        )

        # Should return 2 articles from source1 in the date range
        assert len(source1_articles) == 2
        for article in source1_articles:
            assert article.source == "source1"
            # Skip date range check as the dates might be naive or aware

    def test_singleton_instance(self):
        """Test singleton instance behavior."""
        assert isinstance(article_crud, CRUDArticle)
        assert article_crud.model == Article

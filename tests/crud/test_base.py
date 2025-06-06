"""Tests for the base CRUD module."""

from datetime import datetime, timezone

# We need pytest for fixtures but don't explicitly use it
from pydantic import BaseModel
from sqlmodel import SQLModel, select

from local_newsifier.crud.base import CRUDBase
from local_newsifier.models.article import Article


class TestCRUDBase:
    """Tests for CRUDBase class."""

    def test_get(self, db_session, create_article):
        """Test getting a single item by ID."""
        crud = CRUDBase(Article)
        article = crud.get(db_session, id=create_article.id)

        assert article is not None
        assert article.id == create_article.id
        assert article.title == create_article.title
        assert article.url == create_article.url

    def test_get_not_found(self, db_session):
        """Test getting a non-existent item by ID."""
        crud = CRUDBase(Article)
        article = crud.get(db_session, id=999)

        assert article is None

    def test_get_multi(self, db_session):
        """Test getting multiple items with pagination."""
        # Create multiple articles
        for i in range(5):
            article = Article(
                title=f"Test Article {i}",
                content=f"This is test article {i}.",
                url=f"https://example.com/test-article-{i}",
                source="test_source",
                published_at=datetime.now(timezone.utc),
                status="new",
                scraped_at=datetime.now(timezone.utc),
            )
            db_session.add(article)
        db_session.commit()

        crud = CRUDBase(Article)

        # Test default pagination
        articles = crud.get_multi(db_session)
        assert len(articles) == 5

        # Test with skip
        articles = crud.get_multi(db_session, skip=2)
        assert len(articles) == 3

        # Test with limit
        articles = crud.get_multi(db_session, limit=2)
        assert len(articles) == 2

        # Test with skip and limit
        articles = crud.get_multi(db_session, skip=1, limit=2)
        assert len(articles) == 2
        assert articles[0].title == "Test Article 1"

    def test_create_from_dict(self, db_session, sample_article_data):
        """Test creating a new item from dictionary data."""
        crud = CRUDBase(Article)
        article = crud.create(db_session, obj_in=sample_article_data)

        assert article is not None
        assert article.id is not None
        assert article.title == sample_article_data["title"]
        assert article.url == sample_article_data["url"]

        # Verify it was saved to the database
        statement = select(Article).where(Article.id == article.id)
        db_article = db_session.exec(statement).first()
        assert db_article is not None
        assert db_article.title == sample_article_data["title"]

    def test_create_from_model(self, db_session, sample_article_data):
        """Test creating a new item from SQLModel instance."""
        # Create a SQLModel instance directly
        article_model = Article(**sample_article_data)
        crud = CRUDBase(Article)
        article = crud.create(db_session, obj_in=article_model)

        assert article is not None
        assert article.id is not None
        assert article.title == article_model.title
        assert article.url == article_model.url

    def test_update(self, db_session, create_article):
        """Test updating an existing item."""
        crud = CRUDBase(Article)

        # Get the article from the database
        statement = select(Article).where(Article.id == create_article.id)
        db_obj = db_session.exec(statement).first()

        # Update with a dictionary
        update_data = {"title": "Updated Title", "content": "Updated content."}
        updated_article = crud.update(db_session, db_obj=db_obj, obj_in=update_data)

        assert updated_article is not None
        assert updated_article.id == create_article.id
        assert updated_article.title == "Updated Title"
        assert updated_article.content == "Updated content."
        assert updated_article.url == create_article.url  # Unchanged field

        # Verify it was saved to the database
        statement = select(Article).where(Article.id == create_article.id)
        db_article = db_session.exec(statement).first()
        assert db_article.title == "Updated Title"
        assert db_article.content == "Updated content."

    def test_update_with_model(self, db_session, create_article):
        """Test updating an existing item with a SQLModel instance."""
        # Create an updated model
        updated_model = Article(title="Updated with Model")
        crud = CRUDBase(Article)

        # Get the article from the database
        statement = select(Article).where(Article.id == create_article.id)
        db_obj = db_session.exec(statement).first()

        # Update with a SQLModel instance
        updated_article = crud.update(db_session, db_obj=db_obj, obj_in=updated_model)

        assert updated_article is not None
        assert updated_article.id == create_article.id
        assert updated_article.title == "Updated with Model"
        assert updated_article.content == create_article.content  # Unchanged field

    def test_remove(self, db_session, create_article):
        """Test removing an item."""
        crud = CRUDBase(Article)

        # Remove the article
        removed_article = crud.remove(db_session, id=create_article.id)

        assert removed_article is not None
        assert removed_article.id == create_article.id
        assert removed_article.title == create_article.title

        # Verify it was removed from the database
        statement = select(Article).where(Article.id == create_article.id)
        db_article = db_session.exec(statement).first()
        assert db_article is None

    def test_remove_not_found(self, db_session):
        """Test removing a non-existent item."""
        crud = CRUDBase(Article)

        # Try to remove a non-existent article
        removed_article = crud.remove(db_session, id=999)

        assert removed_article is None

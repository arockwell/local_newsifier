"""Tests for the error-handled CRUD base module."""

from datetime import datetime, timezone
from unittest.mock import patch

import pytest
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlmodel import select

from local_newsifier.crud.error_handled_base import (DatabaseConnectionError,
                                                     DuplicateEntityError,
                                                     EntityNotFoundError,
                                                     ErrorHandledCRUD,
                                                     TransactionError,
                                                     handle_crud_error)
from local_newsifier.models.article import Article


class TestErrorHandledCRUD:
    """Tests for ErrorHandledCRUD base class."""

    def test_get_success(self, db_session, create_article):
        """Test successful get operation."""
        crud = ErrorHandledCRUD(Article)
        article = crud.get(db_session, create_article.id)

        assert article is not None
        assert article.id == create_article.id
        assert article.title == create_article.title

    def test_get_not_found(self, db_session):
        """Test get operation with non-existent ID."""
        crud = ErrorHandledCRUD(Article)

        with pytest.raises(EntityNotFoundError) as excinfo:
            crud.get(db_session, 999)

        assert "Article with id 999 not found" in str(excinfo.value)
        assert excinfo.value.error_type == "not_found"
        assert excinfo.value.context["id"] == 999
        assert excinfo.value.context["model"] == "Article"

    def test_get_multi_success(self, db_session):
        """Test successful get_multi operation."""
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

        crud = ErrorHandledCRUD(Article)
        articles = crud.get_multi(db_session, skip=0, limit=3)

        assert len(articles) == 3
        assert all(isinstance(article, Article) for article in articles)

    def test_create_success(self, db_session, sample_article_data):
        """Test successful create operation."""
        crud = ErrorHandledCRUD(Article)
        article = crud.create(db_session, obj_in=sample_article_data)

        assert article is not None
        assert article.id is not None
        assert article.title == sample_article_data["title"]
        assert article.url == sample_article_data["url"]

    def test_create_duplicate(self, db_session, create_article):
        """Test create operation with duplicate unique field."""
        crud = ErrorHandledCRUD(Article)

        # Try to create with the same URL (which should be unique)
        duplicate_data = {
            "title": "Another Article",
            "content": "This is another test article.",
            "url": create_article.url,  # Same URL as existing article
            "source": "test_source",
            "published_at": datetime.now(timezone.utc),
            "status": "new",
            "scraped_at": datetime.now(timezone.utc),
        }

        # Mock the database error that would occur
        with patch.object(db_session, "commit") as mock_commit:
            # Simulate an IntegrityError for duplicate entry
            mock_commit.side_effect = IntegrityError(
                statement="INSERT INTO articles ...",
                params={},
                orig=Exception("UNIQUE constraint failed: articles.url"),
            )

            with pytest.raises(DuplicateEntityError) as excinfo:
                crud.create(db_session, obj_in=duplicate_data)

            assert "Entity with these attributes already exists" in str(excinfo.value)
            assert excinfo.value.error_type == "validation"

    def test_update_success(self, db_session, create_article):
        """Test successful update operation."""
        crud = ErrorHandledCRUD(Article)

        # Update the article
        update_data = {"title": "Updated Title", "status": "analyzed"}

        updated_article = crud.update(
            db_session, db_obj=create_article, obj_in=update_data
        )

        assert updated_article is not None
        assert updated_article.id == create_article.id
        assert updated_article.title == "Updated Title"
        assert updated_article.status == "analyzed"
        # Other fields should remain unchanged
        assert updated_article.url == create_article.url

    def test_remove_success(self, db_session, create_article):
        """Test successful remove operation."""
        crud = ErrorHandledCRUD(Article)

        # Remove the article
        removed_article = crud.remove(db_session, id=create_article.id)

        assert removed_article is not None
        assert removed_article.id == create_article.id

        # Verify it was removed from the database
        statement = select(Article).where(Article.id == create_article.id)
        result = db_session.exec(statement).first()
        assert result is None

    def test_remove_not_found(self, db_session):
        """Test remove operation with non-existent ID."""
        crud = ErrorHandledCRUD(Article)

        with pytest.raises(EntityNotFoundError) as excinfo:
            crud.remove(db_session, id=999)

        assert "Article with id 999 not found" in str(excinfo.value)
        assert excinfo.value.error_type == "not_found"

    def test_find_by_attributes(self, db_session):
        """Test find_by_attributes operation."""
        # Create multiple articles
        for i in range(3):
            status = "new" if i < 2 else "analyzed"
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

        crud = ErrorHandledCRUD(Article)

        # Find articles with status "new"
        articles = crud.find_by_attributes(db_session, attributes={"status": "new"})

        assert len(articles) == 2
        assert all(article.status == "new" for article in articles)

    def test_get_or_create_existing(self, db_session, create_article):
        """Test get_or_create when entity exists."""
        crud = ErrorHandledCRUD(Article)

        # Try to get or create with the same URL
        data = {
            "title": "Another Title",
            "content": "This is another content.",
            "url": create_article.url,  # Same URL as existing article
            "source": "test_source",
            "published_at": datetime.now(timezone.utc),
            "status": "new",
            "scraped_at": datetime.now(timezone.utc),
        }

        article = crud.get_or_create(db_session, obj_in=data, unique_fields=["url"])

        assert article is not None
        assert article.id == create_article.id
        assert article.title == create_article.title  # Should not be updated
        assert article.url == create_article.url

    def test_get_or_create_new(self, db_session, sample_article_data):
        """Test get_or_create when entity does not exist."""
        crud = ErrorHandledCRUD(Article)

        article = crud.get_or_create(
            db_session, obj_in=sample_article_data, unique_fields=["url"]
        )

        assert article is not None
        assert article.id is not None
        assert article.title == sample_article_data["title"]
        assert article.url == sample_article_data["url"]

        # Verify it was created in the database
        statement = select(Article).where(Article.url == sample_article_data["url"])
        result = db_session.exec(statement).first()
        assert result is not None
        assert result.id == article.id

    def test_database_connection_error(self, db_session):
        """Test handling of database connection errors."""
        crud = ErrorHandledCRUD(Article)

        # Mock the session to raise a connection error
        with patch.object(db_session, "exec") as mock_exec:
            mock_exec.side_effect = OperationalError(
                statement="SELECT * FROM articles",
                params={},
                orig=Exception("connection refused"),
            )

            with pytest.raises(DatabaseConnectionError) as excinfo:
                crud.get(db_session, 1)

            assert "Database connection error" in str(excinfo.value)
            assert excinfo.value.error_type == "network"

    def test_transaction_error(self, db_session, sample_article_data):
        """Test handling of transaction errors."""
        crud = ErrorHandledCRUD(Article)

        # Mock the session to raise a transaction error
        with patch.object(db_session, "commit") as mock_commit:
            mock_commit.side_effect = OperationalError(
                statement="INSERT INTO articles ...",
                params={},
                orig=Exception("database is locked"),
            )

            with pytest.raises(TransactionError) as excinfo:
                crud.create(db_session, obj_in=sample_article_data)

            assert "Database operation error" in str(excinfo.value)
            assert excinfo.value.error_type == "server"


class TestErrorHandledDecorator:
    """Tests for the handle_crud_error decorator."""

    def test_decorator_passes_through_success(self):
        """Test that the decorator passes through successful calls."""

        @handle_crud_error
        def successful_function():
            return "success"

        result = successful_function()
        assert result == "success"

    def test_decorator_handles_sqlalchemy_error(self):
        """Test that the decorator handles SQLAlchemy errors."""

        @handle_crud_error
        def failing_function():
            raise IntegrityError(
                statement="INSERT INTO articles ...",
                params={},
                orig=Exception("UNIQUE constraint failed: articles.url"),
            )

        with pytest.raises(DuplicateEntityError) as excinfo:
            failing_function()

        assert "Entity with these attributes already exists" in str(excinfo.value)
        assert excinfo.value.error_type == "validation"

    def test_decorator_passes_through_crud_errors(self):
        """Test that the decorator passes through CRUDError instances."""

        @handle_crud_error
        def error_raising_function():
            raise EntityNotFoundError("Entity not found")

        with pytest.raises(EntityNotFoundError) as excinfo:
            error_raising_function()

        assert "Entity not found" in str(excinfo.value)
        assert excinfo.value.error_type == "not_found"

"""Refactored tests for the article CRUD module using the enhanced testing infrastructure.

This demonstrates how to use the new testing utilities for more concise and robust tests.
"""

from datetime import datetime, timezone, timedelta

import pytest
from sqlmodel import select

from local_newsifier.crud.article import article as article_crud
from local_newsifier.models.article import Article
from tests.utils.factories import ArticleFactory

class TestArticleCRUDRefactored:
    """Tests for ArticleCRUD class using the enhanced testing infrastructure."""

    def test_create(self, db_function_session, db_verifier):
        """Test creating a new article."""
        # Using the factory to generate test data
        article_data = ArticleFactory.build_dict()
        
        # Create the article using the CRUD module
        article = article_crud.create(db_function_session, obj_in=article_data)

        # Verify with assertions
        assert article is not None
        assert article.id is not None
        assert article.title == article_data["title"]
        assert article.url == article_data["url"]
        assert article.status == article_data["status"]
        assert article.source == article_data["source"]

        # Use the database verifier to check it was saved properly
        db_verifier.assert_exists(Article, id=article.id, title=article_data["title"])
        db_verifier.assert_count(Article, 1)

    def test_create_with_missing_scraped_at(self, db_function_session, db_verifier):
        """Test creating a new article with missing scraped_at field."""
        # Use the factory but remove scraped_at
        article_data = ArticleFactory.build_dict()
        article_data.pop("scraped_at")

        # Create the article
        article = article_crud.create(db_function_session, obj_in=article_data)

        # Verify results
        assert article is not None
        assert article.id is not None
        assert article.scraped_at is not None  # Should be auto-populated

        # Verify database state
        db_article = db_verifier.assert_exists(Article, id=article.id)
        assert db_article.scraped_at is not None

    def test_create_with_model_instance(self, db_function_session, db_verifier):
        """Test creating an article with a model instance."""
        # Create a model instance using the factory
        article_instance = ArticleFactory.build()
        
        # Create using the CRUD module
        article = article_crud.create(db_function_session, obj_in=article_instance)
        
        # Verify results
        assert article is not None
        assert article.id is not None
        assert article.title == article_instance.title

        # Verify database state
        db_verifier.assert_exists(Article, id=article.id, title=article_instance.title)

    def test_get_by_url(self, db_function_session):
        """Test getting an article by URL."""
        # Create a test article using the factory
        ArticleFactory._meta.sqlalchemy_session = db_function_session
        test_article = ArticleFactory.create()
        
        # Test get_by_url
        article = article_crud.get_by_url(db_function_session, url=test_article.url)

        # Verify results
        assert article is not None
        assert article.id == test_article.id
        assert article.title == test_article.title
        assert article.url == test_article.url

    def test_get_by_url_not_found(self, db_function_session):
        """Test getting a non-existent article by URL."""
        article = article_crud.get_by_url(
            db_function_session, url="https://example.com/nonexistent"
        )
        assert article is None

    def test_update_status(self, db_function_session, db_verifier):
        """Test updating an article's status."""
        # Create a test article
        ArticleFactory._meta.sqlalchemy_session = db_function_session
        test_article = ArticleFactory.create(status="new")
        
        # Update the status
        updated_article = article_crud.update_status(
            db_function_session, article_id=test_article.id, status="analyzed"
        )

        # Verify results
        assert updated_article is not None
        assert updated_article.id == test_article.id
        assert updated_article.status == "analyzed"

        # Verify database state
        db_verifier.assert_exists(Article, id=test_article.id, status="analyzed")

    def test_update_status_not_found(self, db_function_session):
        """Test updating a non-existent article's status."""
        updated_article = article_crud.update_status(
            db_function_session, article_id=999, status="analyzed"
        )
        assert updated_article is None

    def test_get_by_status(self, db_function_session):
        """Test getting articles by status."""
        # Create articles with different statuses using the factory
        ArticleFactory._meta.sqlalchemy_session = db_function_session
        
        # Create 2 "new" articles, 1 "analyzed", 1 "scraped", and 1 "saved"
        ArticleFactory.create_batch(2, status="new")
        ArticleFactory.create(status="analyzed")
        ArticleFactory.create(status="scraped") 
        ArticleFactory.create(status="saved")
        
        # Test getting articles with status "new"
        new_articles = article_crud.get_by_status(db_function_session, status="new")
        assert len(new_articles) == 2
        for article in new_articles:
            assert article.status == "new"

        # Test getting articles with status "analyzed"
        analyzed_articles = article_crud.get_by_status(
            db_function_session, status="analyzed"
        )
        assert len(analyzed_articles) == 1
        assert analyzed_articles[0].status == "analyzed"

        # Test getting articles with a non-existent status
        nonexistent_articles = article_crud.get_by_status(
            db_function_session, status="nonexistent"
        )
        assert len(nonexistent_articles) == 0

    def test_get_by_date_range(self, db_function_session):
        """Test getting articles within a date range."""
        # Create base timestamp
        now = datetime.now(timezone.utc)
        
        # Create articles with different publication dates using the factory
        ArticleFactory._meta.sqlalchemy_session = db_function_session
        
        # Create articles with specific dates and sources
        ArticleFactory.create(published_at=now - timedelta(days=5), source="source1")
        ArticleFactory.create(published_at=now - timedelta(days=3), source="source2") 
        ArticleFactory.create(published_at=now - timedelta(days=2), source="source1")
        ArticleFactory.create(published_at=now - timedelta(days=1), source="source2")
        ArticleFactory.create(published_at=now, source="source1")
        
        # Test getting articles within a date range (last 3 days)
        start_date = now - timedelta(days=3)
        end_date = now
        articles = article_crud.get_by_date_range(
            db_function_session, 
            start_date=start_date, 
            end_date=end_date
        )
        
        # Should return 4 articles (from 3 days ago until now)
        assert len(articles) == 4
        
        # Verify they're ordered by published_at
        for i in range(1, len(articles)):
            assert articles[i-1].published_at <= articles[i].published_at
        
        # Test with source filter
        source1_articles = article_crud.get_by_date_range(
            db_function_session,
            start_date=start_date,
            end_date=end_date,
            source="source1"
        )
        
        # Should return 2 articles from source1 in the date range
        assert len(source1_articles) == 2
        for article in source1_articles:
            assert article.source == "source1"

    def test_article_model_tester(self, db_function_session, model_tester):
        """Test the article CRUD operations using the ModelTester utility."""
        # Create a model tester for the Article model
        article_tester = model_tester(Article, db_function_session)
        
        # Test CRUD operations with a single call
        create_data = ArticleFactory.build_dict()
        update_data = {
            "title": "Updated Title",
            "status": "analyzed",
            "content": "This is an updated article content."
        }
        
        # This will test create, get, update, and delete operations
        article_tester.assert_crud_operations(create_data, update_data)

    def test_verify_record_count_change(self, db_function_session, db_verifier):
        """Test database verification with record count change."""
        # Define an action that creates articles
        def create_articles():
            ArticleFactory._meta.sqlalchemy_session = db_function_session
            ArticleFactory.create_batch(3)
        
        # Verify the record count changes by 3 after the action
        db_verifier.assert_record_count_changed(Article, create_articles, 3)

    def test_with_error_handling(self, db_function_session):
        """Test error handling with the transaction-based session."""
        # Create an article
        article = ArticleFactory.build()
        db_function_session.add(article)
        db_function_session.commit()
        
        try:
            # Try to create a duplicate article with the same URL
            duplicate = Article(
                title="Duplicate Article",
                content="This is a duplicate article.",
                url=article.url,  # Same URL should cause a unique constraint violation
                source="test_source",
                published_at=datetime.now(timezone.utc),
                status="new",
                scraped_at=datetime.now(timezone.utc),
            )
            db_function_session.add(duplicate)
            db_function_session.commit()
            pytest.fail("Expected unique constraint violation")
        except Exception:
            # Expected exception, verify the transaction was rolled back
            db_function_session.rollback()
            
            # Verify there's still only one article
            count = db_function_session.exec(select(Article)).all()
            assert len(count) == 1

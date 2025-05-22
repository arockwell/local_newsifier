"""Tests for article model."""

from datetime import datetime, timezone

import pytest
from sqlmodel import Session, SQLModel, create_engine, select

from local_newsifier.models.analysis_result import AnalysisResult
from local_newsifier.models.article import Article
from local_newsifier.models.entity import Entity


def test_article_model():
    """Test Article model basic functionality."""
    # Create an in-memory SQLite database
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    
    # Create a session
    with Session(engine) as session:
        # Create an article
        article = Article(
            title="Test Article",
            content="This is a test article",
            url="https://example.com/test-article",
            source="test",
            status="new",
            published_at=datetime.now(timezone.utc),
            scraped_at=datetime.now(timezone.utc)
        )
        session.add(article)
        session.commit()
        
        # Query the article
        db_article = session.exec(select(Article)).first()
        
        # Verify the fields
        assert db_article is not None
        assert db_article.id is not None
        assert db_article.title == "Test Article"
        assert db_article.content == "This is a test article"
        assert db_article.url == "https://example.com/test-article"
        assert db_article.source == "test"
        assert db_article.status == "new"
        assert db_article.published_at is not None
        assert db_article.scraped_at is not None
        assert db_article.created_at is not None
        assert db_article.updated_at is not None
        
        # Test relationships by adding an entity and analysis result
        entity = Entity(
            article_id=db_article.id,
            text="Test Entity",
            entity_type="TEST"
        )
        analysis_result = AnalysisResult(
            article_id=db_article.id,
            analysis_type="test",
            results={"key": "value"}
        )
        
        session.add(entity)
        session.add(analysis_result)
        session.commit()
        
        # Refresh the article to load relationships
        session.refresh(db_article)
        
        # Test relationship with entities
        assert len(db_article.entities) == 1
        assert db_article.entities[0].text == "Test Entity"
        assert db_article.entities[0].entity_type == "TEST"
        
        # Test relationship with analysis results
        assert len(db_article.analysis_results) == 1
        assert db_article.analysis_results[0].analysis_type == "test"
        assert db_article.analysis_results[0].results == {"key": "value"}


def test_article_unique_url_constraint():
    """Test that Article enforces unique URL constraint."""
    # Create an in-memory SQLite database
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    
    # Create a session
    with Session(engine) as session:
        # Create an article
        article1 = Article(
            title="Test Article 1",
            content="This is test article 1",
            url="https://example.com/test-article",
            source="test",
            status="new",
            published_at=datetime.now(timezone.utc),
            scraped_at=datetime.now(timezone.utc)
        )
        session.add(article1)
        session.commit()
        
        # Try to create another article with the same URL
        article2 = Article(
            title="Test Article 2",
            content="This is test article 2",
            url="https://example.com/test-article",  # Same URL as article1
            source="test",
            status="new",
            published_at=datetime.now(timezone.utc),
            scraped_at=datetime.now(timezone.utc)
        )
        session.add(article2)
        
        # Should raise an integrity error due to unique constraint
        with pytest.raises(Exception) as excinfo:
            session.commit()
        
        # Rollback the failed transaction
        session.rollback()
        
        # Verify we only have one article in the database
        articles = session.exec(select(Article)).all()
        assert len(articles) == 1
        assert articles[0].title == "Test Article 1"

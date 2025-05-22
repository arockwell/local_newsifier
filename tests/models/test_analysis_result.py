"""Tests for analysis_result model."""

from datetime import datetime, timezone

import pytest
from sqlmodel import Session, SQLModel, create_engine, select

from local_newsifier.models.analysis_result import AnalysisResult
from local_newsifier.models.article import Article


def test_analysis_result_model():
    """Test AnalysisResult model basic functionality."""
    # Create an in-memory SQLite database
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    
    # Create a session
    with Session(engine) as session:
        # Create an article first (needed for foreign key)
        article = Article(
            title="Test Article",
            content="This is a test article for analysis result",
            url="https://example.com/test-article",
            source="test",
            status="new",
            published_at=datetime.now(timezone.utc),
            scraped_at=datetime.now(timezone.utc)
        )
        session.add(article)
        session.commit()
        
        # Create an analysis result
        analysis_result = AnalysisResult(
            article_id=article.id,
            analysis_type="sentiment",
            results={"score": 0.8, "label": "positive"}
        )
        session.add(analysis_result)
        session.commit()
        
        # Query the analysis result
        db_result = session.exec(select(AnalysisResult)).first()
        
        # Verify the fields
        assert db_result is not None
        assert db_result.article_id == article.id
        assert db_result.analysis_type == "sentiment"
        assert db_result.results == {"score": 0.8, "label": "positive"}
        assert db_result.id is not None
        assert db_result.created_at is not None
        assert db_result.updated_at is not None
        
        # Test the relationship with article
        assert db_result.article is not None
        assert db_result.article.id == article.id
        assert db_result.article.title == "Test Article"

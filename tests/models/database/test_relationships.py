"""Tests for database relationships."""

from datetime import datetime

from local_newsifier.models.article import Article
from local_newsifier.models.entity import Entity
from local_newsifier.models.analysis_result import AnalysisResult


def test_article_entity_relationship():
    """Test relationship between Article and Entity."""
    # Create test article
    article = Article(
        title="Test Article",
        content="Test content",
        url="https://example.com",
        source="Test Source",
        published_at=datetime.now(),
        status="published",
        scraped_at=datetime.now()
    )
    
    # Create test entity
    entity = Entity(
        text="Test Entity",
        entity_type="PERSON",
        confidence=0.95,
        article=article
    )
    
    # Verify relationships
    assert entity.article == article
    assert article.entities == [entity]


def test_article_analysis_result_relationship():
    """Test relationship between Article and AnalysisResult."""
    # Create test article
    article = Article(
        title="Test Article",
        content="Test content",
        url="https://example.com",
        source="Test Source",
        published_at=datetime.now(),
        status="published",
        scraped_at=datetime.now()
    )
    
    # Create test analysis result
    analysis_result = AnalysisResult(
        analysis_type="sentiment",
        results={"score": 0.8},
        article=article
    )
    
    # Verify relationships
    assert analysis_result.article == article
    assert article.analysis_results == [analysis_result]

"""Tests for database relationships."""

from datetime import datetime

from local_newsifier.models.database.article import ArticleDB
from local_newsifier.models.database.entity import EntityDB
from local_newsifier.models.database.analysis_result import AnalysisResultDB


def test_article_entity_relationship():
    """Test relationship between Article and Entity."""
    # Create test article
    article = ArticleDB(
        title="Test Article",
        content="Test content",
        url="https://example.com",
        source="Test Source",
        published_at=datetime.now(),
        status="published",
        scraped_at=datetime.now()
    )
    
    # Create test entity
    entity = EntityDB(
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
    article = ArticleDB(
        title="Test Article",
        content="Test content",
        url="https://example.com",
        source="Test Source",
        published_at=datetime.now(),
        status="published",
        scraped_at=datetime.now()
    )
    
    # Create test analysis result
    analysis_result = AnalysisResultDB(
        analysis_type="sentiment",
        results={"score": 0.8},
        article=article
    )
    
    # Verify relationships
    assert analysis_result.article == article
    assert article.analysis_results == [analysis_result] 
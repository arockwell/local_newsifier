"""Tests for compatibility between SQLAlchemy models and Pydantic models."""

import pytest
from datetime import datetime, timezone

from local_newsifier.models.database import (
    ArticleDB, EntityDB, AnalysisResultDB,
    Article, Entity, AnalysisResult,
    ArticleCreate, EntityCreate, AnalysisResultCreate,
)
from local_newsifier.models.state import AnalysisStatus


def test_article_pydantic_compatibility():
    """Test that ArticleDB can be validated by Article Pydantic model."""
    # Create an ArticleDB instance
    article_db = ArticleDB(
        id=1,
        url="https://example.com/news/1",
        title="Test Article",
        source="example.com",
        content="This is a test article.",
        status=AnalysisStatus.INITIALIZED.value,
        scraped_at=datetime.now(timezone.utc),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    
    # Convert to Pydantic model
    article = Article.model_validate(article_db)
    
    # Verify
    assert article.id == 1
    assert article.url == "https://example.com/news/1"
    assert article.title == "Test Article"
    assert article.source == "example.com"
    assert article.content == "This is a test article."
    assert article.status == AnalysisStatus.INITIALIZED.value
    assert isinstance(article.scraped_at, datetime)


def test_entity_pydantic_compatibility():
    """Test that EntityDB can be validated by Entity Pydantic model."""
    # Create an EntityDB instance
    entity_db = EntityDB(
        id=1,
        article_id=1,
        text="Test Entity",
        entity_type="CONCEPT",
        confidence=0.9,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    
    # Convert to Pydantic model
    entity = Entity.model_validate(entity_db)
    
    # Verify
    assert entity.id == 1
    assert entity.article_id == 1
    assert entity.text == "Test Entity"
    assert entity.entity_type == "CONCEPT"
    assert entity.confidence == 0.9


def test_analysis_result_pydantic_compatibility():
    """Test that AnalysisResultDB can be validated by AnalysisResult Pydantic model."""
    # Create an AnalysisResultDB instance
    now = datetime.now(timezone.utc)
    analysis_db = AnalysisResultDB(
        id=1,
        article_id=1,
        analysis_type="sentiment",
        results={"score": 0.75, "label": "positive"},
        created_at=now,
        updated_at=now,
    )
    
    # Convert to Pydantic model
    analysis = AnalysisResult.model_validate(analysis_db)
    
    # Verify
    assert analysis.id == 1
    assert analysis.article_id == 1
    assert analysis.analysis_type == "sentiment"
    assert analysis.results["score"] == 0.75
    assert analysis.results["label"] == "positive"
    assert isinstance(analysis.created_at, datetime)


def test_article_create_to_article_db():
    """Test creating ArticleDB from ArticleCreate."""
    # Create an ArticleCreate instance
    article_create = ArticleCreate(
        url="https://example.com/news/1",
        title="Test Article",
        source="example.com",
        content="This is a test article.",
        status=AnalysisStatus.INITIALIZED.value,
    )
    
    # Convert to dictionary
    article_data = article_create.model_dump()
    
    # Create ArticleDB
    article_db = ArticleDB(**article_data)
    
    # Verify
    assert article_db.url == "https://example.com/news/1"
    assert article_db.title == "Test Article"
    assert article_db.source == "example.com"
    assert article_db.content == "This is a test article."
    assert article_db.status == AnalysisStatus.INITIALIZED.value


def test_entity_create_to_entity_db():
    """Test creating EntityDB from EntityCreate."""
    # Create an EntityCreate instance
    entity_create = EntityCreate(
        article_id=1,
        text="Test Entity",
        entity_type="CONCEPT",
        confidence=0.9,
    )
    
    # Convert to dictionary
    entity_data = entity_create.model_dump()
    
    # Create EntityDB
    entity_db = EntityDB(**entity_data)
    
    # Verify
    assert entity_db.article_id == 1
    assert entity_db.text == "Test Entity"
    assert entity_db.entity_type == "CONCEPT"
    assert entity_db.confidence == 0.9


def test_analysis_result_create_to_analysis_result_db():
    """Test creating AnalysisResultDB from AnalysisResultCreate."""
    # Create an AnalysisResultCreate instance
    analysis_create = AnalysisResultCreate(
        article_id=1,
        analysis_type="sentiment",
        results={"score": 0.75, "label": "positive"},
    )
    
    # Convert to dictionary
    analysis_data = analysis_create.model_dump()
    
    # Create AnalysisResultDB
    analysis_db = AnalysisResultDB(**analysis_data)
    
    # Verify
    assert analysis_db.article_id == 1
    assert analysis_db.analysis_type == "sentiment"
    assert analysis_db.results["score"] == 0.75
    assert analysis_db.results["label"] == "positive"
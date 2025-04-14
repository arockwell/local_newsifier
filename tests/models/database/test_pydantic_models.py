"""Tests for Pydantic models."""

from datetime import datetime

import pytest

from src.local_newsifier.models.database.pydantic_models import (
    ArticleBase,
    ArticleCreate,
    Article,
    EntityBase,
    EntityCreate,
    Entity,
    AnalysisResultBase,
    AnalysisResultCreate,
    AnalysisResult,
)


def test_article_base():
    """Test ArticleBase model."""
    article = ArticleBase(
        url="https://example.com",
        title="Test Article",
        source="Test Source",
        published_at=datetime.now(),
        content="Test content",
        status="published"
    )
    assert article.url == "https://example.com"
    assert article.title == "Test Article"
    assert article.source == "Test Source"
    assert article.content == "Test content"
    assert article.status == "published"


def test_article_create():
    """Test ArticleCreate model."""
    article = ArticleCreate(
        url="https://example.com",
        title="Test Article",
        source="Test Source",
        published_at=datetime.now(),
        content="Test content",
        status="published"
    )
    assert article.url == "https://example.com"
    assert article.title == "Test Article"


def test_article():
    """Test Article model."""
    article = Article(
        id=1,
        url="https://example.com",
        title="Test Article",
        source="Test Source",
        published_at=datetime.now(),
        content="Test content",
        status="published",
        scraped_at=datetime.now(),
        entities=[],
        analysis_results=[]
    )
    assert article.id == 1
    assert article.url == "https://example.com"
    assert article.entities == []
    assert article.analysis_results == []


def test_entity_base():
    """Test EntityBase model."""
    entity = EntityBase(
        text="Test Entity",
        entity_type="PERSON",
        confidence=0.95
    )
    assert entity.text == "Test Entity"
    assert entity.entity_type == "PERSON"
    assert entity.confidence == 0.95


def test_entity_create():
    """Test EntityCreate model."""
    entity = EntityCreate(
        text="Test Entity",
        entity_type="PERSON",
        confidence=0.95,
        article_id=1
    )
    assert entity.text == "Test Entity"
    assert entity.article_id == 1


def test_entity():
    """Test Entity model."""
    entity = Entity(
        id=1,
        text="Test Entity",
        entity_type="PERSON",
        confidence=0.95,
        article_id=1
    )
    assert entity.id == 1
    assert entity.text == "Test Entity"
    assert entity.article_id == 1


def test_analysis_result_base():
    """Test AnalysisResultBase model."""
    result = AnalysisResultBase(
        analysis_type="sentiment",
        results={"score": 0.8}
    )
    assert result.analysis_type == "sentiment"
    assert result.results == {"score": 0.8}


def test_analysis_result_create():
    """Test AnalysisResultCreate model."""
    result = AnalysisResultCreate(
        analysis_type="sentiment",
        results={"score": 0.8},
        article_id=1
    )
    assert result.analysis_type == "sentiment"
    assert result.article_id == 1


def test_analysis_result():
    """Test AnalysisResult model."""
    result = AnalysisResult(
        id=1,
        analysis_type="sentiment",
        results={"score": 0.8},
        article_id=1,
        created_at=datetime.now()
    )
    assert result.id == 1
    assert result.analysis_type == "sentiment"
    assert result.article_id == 1 
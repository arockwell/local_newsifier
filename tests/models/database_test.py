"""Tests for database models."""
import datetime
from typing import Generator

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from local_newsifier.models.database import (
    AnalysisResultDB,
    ArticleDB,
    Base,
    EntityDB,
    init_db,
)


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """Create a test database session."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def test_article_model(db_session: Session):
    """Test ArticleDB model."""
    article = ArticleDB(
        url="https://example.com/article1",
        title="Test Article",
        content="Test content",
        published_at=datetime.datetime.now(),
        status="pending"
    )
    
    db_session.add(article)
    db_session.commit()
    
    stmt = select(ArticleDB)
    result = db_session.execute(stmt)
    retrieved = result.scalars().first()
    
    assert retrieved is not None
    assert retrieved.url == "https://example.com/article1"
    assert retrieved.title == "Test Article"
    assert retrieved.content == "Test content"
    assert retrieved.status == "pending"


def test_entity_model(db_session: Session):
    """Test EntityDB model."""
    article = ArticleDB(
        url="https://example.com/article1",
        title="Test Article",
        content="Test content",
        published_at=datetime.datetime.now(),
        status="pending"
    )
    db_session.add(article)
    db_session.commit()
    
    entity = EntityDB(
        article_id=article.id,
        text="John Doe",
        entity_type="PERSON",
        confidence=0.95
    )
    
    db_session.add(entity)
    db_session.commit()
    
    stmt = select(EntityDB)
    result = db_session.execute(stmt)
    retrieved = result.scalars().first()
    
    assert retrieved is not None
    assert retrieved.text == "John Doe"
    assert retrieved.entity_type == "PERSON"
    assert retrieved.confidence == 0.95
    assert retrieved.article_id == article.id


def test_analysis_result_model(db_session: Session):
    """Test AnalysisResultDB model."""
    article = ArticleDB(
        url="https://example.com/article1",
        title="Test Article",
        content="Test content",
        published_at=datetime.datetime.now(),
        status="pending"
    )
    db_session.add(article)
    db_session.commit()
    
    analysis = AnalysisResultDB(
        article_id=article.id,
        analysis_type="sentiment",
        results={"score": 0.8, "label": "positive"}
    )
    
    db_session.add(analysis)
    db_session.commit()
    
    stmt = select(AnalysisResultDB)
    result = db_session.execute(stmt)
    retrieved = result.scalars().first()
    
    assert retrieved is not None
    assert retrieved.analysis_type == "sentiment"
    assert retrieved.results == {"score": 0.8, "label": "positive"}
    assert retrieved.article_id == article.id


def test_relationships(db_session: Session):
    """Test relationships between models."""
    article = ArticleDB(
        url="https://example.com/article1",
        title="Test Article",
        content="Test content",
        published_at=datetime.datetime.now(),
        status="pending"
    )
    db_session.add(article)
    db_session.commit()
    
    entity = EntityDB(
        article_id=article.id,
        text="John Doe",
        entity_type="PERSON",
        confidence=0.95
    )
    analysis = AnalysisResultDB(
        article_id=article.id,
        analysis_type="sentiment",
        results={"score": 0.8, "label": "positive"}
    )
    
    db_session.add_all([entity, analysis])
    db_session.commit()
    
    stmt = select(ArticleDB)
    result = db_session.execute(stmt)
    retrieved = result.scalars().first()
    
    assert retrieved is not None
    assert len(retrieved.entities) == 1
    assert len(retrieved.analysis_results) == 1
    assert retrieved.entities[0].text == "John Doe"
    assert retrieved.analysis_results[0].analysis_type == "sentiment" 
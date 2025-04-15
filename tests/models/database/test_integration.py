"""Integration tests for SQLModel database models."""

import pytest
from sqlalchemy import inspect
from sqlmodel import Session
import datetime
from datetime import timezone

from local_newsifier.models import SQLModel
from local_newsifier.models.article import Article
from local_newsifier.models.entity import Entity
from local_newsifier.models.state import AnalysisStatus


@pytest.fixture
def db_session(test_engine):
    """Create a test database session."""
    # Create all tables
    SQLModel.metadata.create_all(test_engine)
    
    # Create session
    session = Session(test_engine)
    try:
        yield session
    finally:
        session.close()


def test_schema_generation(test_engine):
    """Test that the schema is properly generated."""
    inspector = inspect(test_engine)

    # Check that all tables are created
    tables = inspector.get_table_names()
    assert "articles" in tables
    assert "entities" in tables

    # Check article table columns
    article_cols = {col["name"] for col in inspector.get_columns("articles")}
    assert "id" in article_cols
    assert "url" in article_cols
    assert "title" in article_cols
    assert "source" in article_cols
    assert "content" in article_cols
    assert "status" in article_cols
    assert "created_at" in article_cols
    assert "updated_at" in article_cols

    # Check entity table columns
    entity_cols = {col["name"] for col in inspector.get_columns("entities")}
    assert "id" in entity_cols
    assert "article_id" in entity_cols
    assert "text" in entity_cols
    assert "entity_type" in entity_cols
    assert "sentence_context" in entity_cols
    assert "created_at" in entity_cols
    assert "updated_at" in entity_cols


def test_full_article_entity_workflow(db_session):
    """Test a full workflow of creating an article with entities."""
    now = datetime.datetime.now(timezone.utc)
    # Create an article
    article = Article(
        url="https://example.com/news/1",
        title="Test Article",
        source="Example News",
        content="This is a test article about Gainesville.",
        status=AnalysisStatus.INITIALIZED.value,
        published_at=now,
        scraped_at=now
    )
    db_session.add(article)
    db_session.commit()
    db_session.refresh(article)

    # Create entities
    entities = [
        Entity(
            text="Gainesville",
            entity_type="GPE",
            confidence=0.95,
            article_id=article.id,
            sentence_context=(
                "This is a test article about Gainesville."
            )
        ),
        Entity(
            text="University of Florida",
            entity_type="ORG",
            confidence=0.92,
            article_id=article.id,
            sentence_context=(
                "The University of Florida is located in Gainesville."
            )
        ),
        Entity(
            text="John Smith",
            entity_type="PERSON",
            confidence=0.88,
            article_id=article.id,
            sentence_context=(
                "John Smith is a professor at the University of Florida."
            )
        )
    ]

    for entity in entities:
        article.entities.append(entity)

    db_session.commit()
    db_session.refresh(article)

    # Verify relationships
    assert len(article.entities) == 3
    assert all(e.article_id == article.id for e in article.entities)
    assert all(e.article == article for e in article.entities)

    # Verify entity types
    entity_types = {e.entity_type for e in article.entities}
    assert "GPE" in entity_types
    assert "ORG" in entity_types
    assert "PERSON" in entity_types

    # Verify entity texts
    entity_texts = {e.text for e in article.entities}
    assert "Gainesville" in entity_texts
    assert "University of Florida" in entity_texts
    assert "John Smith" in entity_texts

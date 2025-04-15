"""Tests for the Entity SQLModel."""

import datetime
from datetime import timezone

import pytest
from sqlmodel import Session

from local_newsifier.models.article import Article
from local_newsifier.models.entity import Entity
from local_newsifier.models.state import AnalysisStatus


@pytest.fixture
def article(db_session):
    """Create a test article."""
    now = datetime.datetime.now(timezone.utc)
    article = Article(
        url="https://example.com/news/1",
        title="Test Article",
        source="Example News",
        content="This is a test article.",
        status=AnalysisStatus.INITIALIZED.value,
        published_at=now,
        scraped_at=now
    )
    db_session.add(article)
    db_session.commit()
    db_session.refresh(article)
    return article


def test_entity_creation(db_session, article):
    """Test creating an Entity instance."""
    entity = Entity(
        text="Gainesville",
        entity_type="GPE",
        confidence=0.95,
        sentence_context="This is about Gainesville.",
        article_id=article.id
    )
    article.entities.append(entity)
    db_session.commit()
    db_session.refresh(entity)

    assert entity.id is not None
    assert entity.text == "Gainesville"
    assert entity.entity_type == "GPE"
    assert entity.sentence_context == "This is about Gainesville."
    assert isinstance(entity.created_at, datetime.datetime)
    assert isinstance(entity.updated_at, datetime.datetime)


def test_entity_article_relationship(db_session, article):
    """Test relationship between Entity and Article."""
    entity = Entity(
        text="Gainesville",
        entity_type="GPE",
        confidence=0.95,
        sentence_context="This is about Gainesville.",
        article_id=article.id
    )

    article.entities.append(entity)
    db_session.commit()

    # Refresh the session to ensure we're getting fresh data
    db_session.refresh(entity)
    db_session.refresh(article)

    assert entity.article == article
    assert article.entities[0] == entity


def test_multiple_entities_for_article(db_session, article):
    """Test that an article can have multiple entities."""
    entities = [
        Entity(text="Gainesville", entity_type="GPE", confidence=0.95, article_id=article.id),
        Entity(text="University of Florida", entity_type="ORG", confidence=0.90, article_id=article.id),
        Entity(text="John Smith", entity_type="PERSON", confidence=0.85, article_id=article.id),
    ]

    for entity in entities:
        article.entities.append(entity)

    db_session.commit()

    # Refresh the session
    db_session.refresh(article)

    assert len(article.entities) == 3

    # Check that all entities are properly associated
    entity_texts = [e.text for e in article.entities]
    assert "Gainesville" in entity_texts
    assert "University of Florida" in entity_texts
    assert "John Smith" in entity_texts


def test_entity_default_values(db_session, article):
    """Test default values for Entity fields."""
    entity = Entity(
        text="Gainesville", 
        entity_type="GPE",
        article_id=article.id
    )
    article.entities.append(entity)
    db_session.commit()
    db_session.refresh(entity)

    assert entity.created_at is not None
    assert entity.updated_at is not None
    assert entity.confidence == 1.0  # Default value defined in model

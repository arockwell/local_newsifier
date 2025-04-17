"""Tests for the Entity database model."""

import datetime

import pytest

from local_newsifier.models.database.article import Article
from local_newsifier.models.database.entity import Entity
from local_newsifier.models.state import AnalysisStatus


@pytest.fixture
def article(db_session):
    """Create a test article."""
    now = datetime.datetime.now(datetime.timezone.utc)
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
    return article


def test_entity_creation(db_session, article):
    """Test creating an Entity instance."""
    entity = Entity(
        text="Gainesville",
        entity_type="GPE",
        sentence_context="This is about Gainesville.",
    )
    article.entities.append(entity)
    db_session.commit()

    assert entity.id is not None
    assert str(entity.text) == "Gainesville"
    assert str(entity.entity_type) == "GPE"
    assert str(entity.sentence_context) == "This is about Gainesville."
    assert isinstance(entity.created_at, datetime.datetime)
    assert isinstance(entity.updated_at, datetime.datetime)


def test_entity_article_relationship(db_session, article):
    """Test relationship between Entity and Article."""
    entity = Entity(
        text="Gainesville",
        entity_type="GPE",
        sentence_context="This is about Gainesville.",
    )

    article.entities.append(entity)
    db_session.commit()

    # Refresh the session to ensure we're getting fresh data
    db_session.refresh(entity)

    assert entity.article == article
    assert article.entities[0] == entity


def test_multiple_entities_for_article(db_session, article):
    """Test that an article can have multiple entities."""
    entities = [
        Entity(text="Gainesville", entity_type="GPE"),
        Entity(text="University of Florida", entity_type="ORG"),
        Entity(text="John Smith", entity_type="PERSON"),
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
    entity = Entity(text="Gainesville", entity_type="GPE")
    article.entities.append(entity)
    db_session.commit()

    assert entity.created_at is not None
    assert entity.updated_at is not None

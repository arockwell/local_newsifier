"""Tests for the Article database model."""

import datetime

import pytest

from local_newsifier.models.database.article import ArticleDB
from local_newsifier.models.database.entity import EntityDB
from local_newsifier.models.state import AnalysisStatus


def test_article_creation(db_session):
    """Test creating an Article instance."""
    article = ArticleDB(
        url="https://example.com/news/1",
        title="Test Article",
        source="Example News",
        content="This is a test article.",
        status=AnalysisStatus.INITIALIZED.value,
    )
    db_session.add(article)
    db_session.commit()

    assert article.id is not None
    assert article.url == "https://example.com/news/1"
    assert article.title == "Test Article"
    assert article.source == "Example News"
    assert article.content == "This is a test article."
    assert article.status == AnalysisStatus.INITIALIZED.value
    assert isinstance(article.created_at, datetime.datetime)
    assert isinstance(article.updated_at, datetime.datetime)
    assert isinstance(article.scraped_at, datetime.datetime)


def test_article_entity_relationship(db_session):
    """Test the relationship between Article and Entity."""
    # Create an article
    article = ArticleDB(
        url="https://example.com/test",
        title="Test Article",
        source="Example News",
        content="This is a test article about Gainesville.",
        status=AnalysisStatus.INITIALIZED.value,
    )
    db_session.add(article)
    db_session.commit()

    # Create an entity and associate it with the article
    entity = EntityDB(
        text="Gainesville",
        entity_type="GPE",
        sentence_context=("This is a test article about Gainesville."),
    )
    article.entities.append(entity)
    db_session.commit()

    # Get the article ID and entity ID for later use
    article_id = article.id
    entity_id = entity.id

    # Delete the article
    db_session.delete(article)
    db_session.commit()

    # Check if article is deleted
    remaining_article = (
        db_session.query(ArticleDB).filter_by(id=article_id).first()
    )
    assert remaining_article is None

    # Check if entity is also deleted
    remaining_entity = (
        db_session.query(EntityDB).filter_by(id=entity_id).first()
    )
    assert remaining_entity is None


def test_article_unique_url_constraint(db_session):
    """Test that article URL must be unique."""
    article1 = ArticleDB(
        url="https://example.com/news/1",
        title="Test Article 1",
        source="Example News",
    )
    db_session.add(article1)
    db_session.commit()

    article2 = ArticleDB(
        url="https://example.com/news/1",  # Same URL as article1
        title="Test Article 2",
        source="Example News",
    )
    db_session.add(article2)

    with pytest.raises(Exception):  # PostgreSQL will raise IntegrityError
        db_session.commit()

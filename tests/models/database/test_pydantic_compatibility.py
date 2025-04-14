"""Tests for Pydantic model compatibility."""

import pytest
from sqlalchemy.orm import sessionmaker
import datetime

from local_newsifier.models.database.base import Base
from local_newsifier.models.database.article import ArticleDB
from local_newsifier.models.database.entity import EntityDB
from local_newsifier.models.state import AnalysisStatus


@pytest.fixture
def db_session(test_engine):
    """Create a test database session."""
    TestSession = sessionmaker(bind=test_engine)
    session = TestSession()
    yield session
    session.close()


def test_article_pydantic_compatibility(db_session):
    """Test that ArticleDB can be converted to Pydantic model."""
    now = datetime.datetime.now(datetime.timezone.utc)
    article = ArticleDB(
        url="https://example.com/news/article1",
        title="Test Article",
        source="Example News",
        content="This is a test article.",
        status=AnalysisStatus.INITIALIZED.value,
        published_at=now,
        scraped_at=now
    )
    db_session.add(article)
    db_session.commit()

    article_dict = article.model_dump()
    assert article_dict["url"] == "https://example.com/news/article1"
    assert article_dict["title"] == "Test Article"
    assert article_dict["source"] == "Example News"
    assert article_dict["content"] == "This is a test article."
    assert article_dict["status"] == AnalysisStatus.INITIALIZED.value


def test_entity_pydantic_compatibility(db_session):
    """Test that EntityDB can be converted to Pydantic model."""
    now = datetime.datetime.now(datetime.timezone.utc)
    article = ArticleDB(
        url="https://example.com/news/article2",
        title="Test Article",
        source="Example News",
        content="This is a test article.",
        status=AnalysisStatus.INITIALIZED.value,
        published_at=now,
        scraped_at=now
    )
    db_session.add(article)
    db_session.commit()

    entity = EntityDB(
        text="Gainesville",
        entity_type="GPE",
        sentence_context="This is about Gainesville.",
        article_id=article.id
    )
    db_session.add(entity)
    db_session.commit()

    entity_dict = entity.model_dump()
    assert entity_dict["text"] == "Gainesville"
    assert entity_dict["entity_type"] == "GPE"
    assert entity_dict["sentence_context"] == "This is about Gainesville."
    assert entity_dict["article_id"] == article.id

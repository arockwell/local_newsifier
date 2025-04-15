"""Tests for Pydantic model compatibility."""

import pytest
from sqlalchemy.orm import sessionmaker
import datetime

# Import SQLModel classes
from local_newsifier.models.article import Article
from local_newsifier.models.entity import Entity
from local_newsifier.models.state import AnalysisStatus


@pytest.fixture
def db_session(test_engine):
    """Create a test database session."""
    TestSession = sessionmaker(bind=test_engine)
    session = TestSession()
    yield session
    session.close()


def test_article_pydantic_compatibility(db_session):
    """Test that SQLModel Article can be accessed as a dictionary."""
    now = datetime.datetime.now(datetime.timezone.utc)
    article = Article(
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

    # Access attributes directly from the model
    assert article.url == "https://example.com/news/article1"
    assert article.title == "Test Article"
    assert article.source == "Example News"
    assert article.content == "This is a test article."
    assert article.status == AnalysisStatus.INITIALIZED.value
    
    # Convert to dict using SQLModel's dict method
    article_dict = article.model_dump()
    for key in ["url", "title", "source", "content", "status"]:
        assert key in article_dict


def test_entity_pydantic_compatibility(db_session):
    """Test that SQLModel Entity can be accessed as a dictionary."""
    now = datetime.datetime.now(datetime.timezone.utc)
    article = Article(
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

    entity = Entity(
        text="Gainesville",
        entity_type="GPE",
        confidence=0.95,
        article_id=article.id
    )
    db_session.add(entity)
    db_session.commit()

    # Access attributes directly from the model
    assert entity.text == "Gainesville"
    assert entity.entity_type == "GPE"
    assert entity.confidence == 0.95
    assert entity.article_id == article.id
    
    # Convert to dict using SQLModel's dict method
    entity_dict = entity.model_dump()
    for key in ["text", "entity_type", "confidence", "article_id"]:
        assert key in entity_dict

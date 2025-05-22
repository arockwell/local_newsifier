"""Tests for the Article database model."""

import datetime
from unittest.mock import MagicMock, patch

import pytest
from sqlmodel import Session

from local_newsifier.models.article import Article
from local_newsifier.models.state import AnalysisStatus
from local_newsifier.models.entity import Entity


def test_article_creation():
    """Test creating an Article instance."""
    # Create a mock session
    mock_session = MagicMock(spec=Session)

    # Create article with timestamps
    now = datetime.datetime.now(datetime.timezone.utc)
    article = Article(
        url="https://example.com/news/1",
        title="Test Article",
        source="Example News",
        content="This is a test article.",
        status=AnalysisStatus.INITIALIZED.value,
        created_at=now,
        updated_at=now,
        scraped_at=now,
    )
    mock_session.add(article)

    # Verify attributes using direct attribute access
    assert str(article.url) == "https://example.com/news/1"
    assert str(article.title) == "Test Article"
    assert str(article.source) == "Example News"
    assert str(article.content) == "This is a test article."
    assert str(article.status) == str(AnalysisStatus.INITIALIZED.value)
    assert isinstance(article.created_at, datetime.datetime)
    assert isinstance(article.updated_at, datetime.datetime)
    assert isinstance(article.scraped_at, datetime.datetime)
    assert article.created_at == now
    assert article.updated_at == now
    assert article.scraped_at == now


def test_article_entity_relationship():
    """Test the relationship between Article and Entity."""
    # Create mock session
    mock_session = MagicMock(spec=Session)

    # Create an article with timestamps
    now = datetime.datetime.now(datetime.timezone.utc)
    article = Article(
        url="https://example.com/test",
        title="Test Article",
        source="Example News",
        content="This is a test article about Gainesville.",
        status=AnalysisStatus.INITIALIZED.value,
        created_at=now,
        updated_at=now,
        scraped_at=now,
    )
    mock_session.add(article)

    # Create an entity and associate it with the article
    entity = Entity(
        text="Gainesville",
        entity_type="GPE",
        sentence_context=("This is a test article about Gainesville."),
        created_at=now,
        updated_at=now,
    )
    article.entities.append(entity)
    mock_session.add(entity)

    # Verify relationship using list operations
    assert len(article.entities) == 1
    assert article.entities[0] is entity
    assert entity.article is article


def test_article_unique_url_constraint():
    """Test that article URL must be unique."""
    # Create mock session that raises IntegrityError
    mock_session = MagicMock(spec=Session)
    mock_session.commit.side_effect = Exception("Unique constraint violation")

    # Create first article with timestamps
    now = datetime.datetime.now(datetime.timezone.utc)
    article1 = Article(
        url="https://example.com/news/1",
        title="Test Article 1",
        source="Example News",
        created_at=now,
        updated_at=now,
        scraped_at=now,
    )
    mock_session.add(article1)

    # Create second article with same URL
    article2 = Article(
        url="https://example.com/news/1",  # Same URL as article1
        title="Test Article 2",
        source="Example News",
        created_at=now,
        updated_at=now,
        scraped_at=now,
    )
    mock_session.add(article2)

    # Verify that commit raises an exception
    with pytest.raises(Exception):
        mock_session.commit()

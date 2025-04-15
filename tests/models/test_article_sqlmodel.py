"""Tests for the SQLModel-based Article model."""

import datetime
from unittest.mock import MagicMock

import pytest
from sqlmodel import Session

from local_newsifier.models.article import Article
from local_newsifier.models.state import AnalysisStatus


def test_article_creation():
    """Test creating an Article instance with SQLModel."""
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
        published_at=now,
        created_at=now,
        updated_at=now,
        scraped_at=now,
    )
    mock_session.add(article)
    
    # Verify attributes using direct attribute access
    assert article.url == "https://example.com/news/1"
    assert article.title == "Test Article"
    assert article.source == "Example News"
    assert article.content == "This is a test article."
    assert article.status == AnalysisStatus.INITIALIZED.value
    assert isinstance(article.created_at, datetime.datetime)
    assert isinstance(article.updated_at, datetime.datetime)
    assert isinstance(article.scraped_at, datetime.datetime)
    assert article.created_at == now
    assert article.updated_at == now
    assert article.scraped_at == now


def test_article_model_dict():
    """Test Article model's dict conversion."""
    now = datetime.datetime.now(datetime.timezone.utc)
    article = Article(
        id=1,
        url="https://example.com/news/1",
        title="Test Article",
        source="Example News",
        content="This is a test article.",
        status=AnalysisStatus.INITIALIZED.value,
        published_at=now,
        created_at=now,
        updated_at=now,
        scraped_at=now,
    )
    
    # Convert to dict
    article_dict = article.model_dump()
    
    # Verify dict contents
    assert article_dict["id"] == 1
    assert article_dict["url"] == "https://example.com/news/1"
    assert article_dict["title"] == "Test Article"
    assert article_dict["source"] == "Example News"
    assert article_dict["content"] == "This is a test article."
    assert article_dict["status"] == AnalysisStatus.INITIALIZED.value


def test_article_defaults():
    """Test Article model's default values."""
    now = datetime.datetime.now(datetime.timezone.utc)
    article = Article(
        url="https://example.com/news/1",
        title="Test Article",
        source="Example News",
        content="This is a test article.",
        status=AnalysisStatus.INITIALIZED.value,
        published_at=now,
    )
    
    # Verify default values
    assert article.id is None
    assert isinstance(article.created_at, datetime.datetime)
    assert isinstance(article.updated_at, datetime.datetime)
    assert isinstance(article.scraped_at, datetime.datetime)
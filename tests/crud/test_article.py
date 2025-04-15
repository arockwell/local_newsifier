"""Tests for Article CRUD operations."""

import datetime
from unittest.mock import MagicMock, patch

import pytest
from sqlmodel import Session, select

from local_newsifier.models.article import Article
from local_newsifier.models.state import AnalysisStatus
from local_newsifier.models.base import sqlmodel_metadata
from local_newsifier.crud.article import (
    create_article,
    get_article,
    get_article_by_url,
    update_article_status,
    get_articles_by_status,
)


@pytest.fixture
def mock_article_model():
    """Mock the ArticleModel import."""
    with patch("local_newsifier.crud.article.Article") as mock_article_model:
        yield mock_article_model
        
@pytest.fixture
def mock_session():
    """Create a mock SQLModel session."""
    session = MagicMock(spec=Session)
    return session


def test_create_article(mock_session, mock_article_model):
    """Test creating an article."""
    # Setup
    now = datetime.datetime.now(datetime.timezone.utc)
    article_data = {
        "url": "https://example.com/news/1",
        "title": "Test Article",
        "source": "Example News",
        "content": "This is a test article.",
        "status": AnalysisStatus.INITIALIZED.value,
        "published_at": now,
    }
    
    # Configure the mock
    mock_session.add = MagicMock()
    mock_session.commit = MagicMock()
    mock_session.refresh = MagicMock()
    
    # Call the function
    result = create_article(mock_session, article_data)
    
    # Assertions
    assert isinstance(result, Article)
    assert result.url == "https://example.com/news/1"
    assert result.title == "Test Article"
    assert result.source == "Example News"
    assert result.content == "This is a test article."
    assert result.status == AnalysisStatus.INITIALIZED.value
    assert result.published_at == now
    assert isinstance(result.scraped_at, datetime.datetime)
    
    # Verify mock calls
    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()
    mock_session.refresh.assert_called_once()


def test_get_article(mock_session, mock_article_model):
    """Test getting an article by ID."""
    # Create a test article
    test_article = Article(
        id=1,
        url="https://example.com/news/1",
        title="Test Article",
        source="Example News",
        content="This is a test article.",
        status=AnalysisStatus.INITIALIZED.value,
        published_at=datetime.datetime.now(datetime.timezone.utc),
    )
    
    # Configure the mock
    mock_session.get.return_value = test_article
    
    # Call the function
    result = get_article(mock_session, 1)
    
    # Assertions
    assert result is test_article
    
    # Verify mock calls
    mock_session.get.assert_called_once_with(Article, 1)


def test_get_article_by_url(mock_session, mock_article_model):
    """Test getting an article by URL."""
    # Create a test article
    test_article = Article(
        id=1,
        url="https://example.com/news/1",
        title="Test Article",
        source="Example News",
        content="This is a test article.",
        status=AnalysisStatus.INITIALIZED.value,
        published_at=datetime.datetime.now(datetime.timezone.utc),
    )
    
    # Make mock_article_model available when it's imported inside the function
    mock_exec = MagicMock()
    mock_exec.first.return_value = test_article
    mock_session.exec.return_value = mock_exec
    
    # Simulate the select() query
    mock_where = MagicMock()
    mock_article_model.url = "dummy_attr"  # Needed for the .where(Article.url == url) part
    mock_article_model.return_value = mock_article_model  # Return itself when instantiated
    
    # Call the function
    result = get_article_by_url(mock_session, "https://example.com/news/1")
    
    # Assertions
    assert result is test_article
    
    # Verify mock calls
    mock_session.exec.assert_called_once()
    mock_exec.first.assert_called_once()


def test_update_article_status(mock_session, mock_article_model):
    """Test updating an article's status."""
    # Create a test article
    test_article = Article(
        id=1,
        url="https://example.com/news/1",
        title="Test Article",
        source="Example News",
        content="This is a test article.",
        status=AnalysisStatus.INITIALIZED.value,
        published_at=datetime.datetime.now(datetime.timezone.utc),
    )
    
    # Configure the mock
    mock_session.get.return_value = test_article
    mock_session.add = MagicMock()
    mock_session.commit = MagicMock()
    mock_session.refresh = MagicMock()
    
    # Call the function
    result = update_article_status(mock_session, 1, AnalysisStatus.ANALYSIS_SUCCEEDED.value)
    
    # Assertions
    assert result is test_article
    assert result.status == AnalysisStatus.ANALYSIS_SUCCEEDED.value
    
    # Verify mock calls
    mock_session.get.assert_called_once_with(Article, 1)
    mock_session.add.assert_called_once_with(test_article)
    mock_session.commit.assert_called_once()
    mock_session.refresh.assert_called_once_with(test_article)


def test_update_article_status_not_found(mock_session, mock_article_model):
    """Test updating a non-existent article's status."""
    # Configure the mock
    mock_session.get.return_value = None
    
    # Call the function
    result = update_article_status(mock_session, 999, AnalysisStatus.ANALYSIS_SUCCEEDED.value)
    
    # Assertions
    assert result is None
    
    # Verify mock calls
    mock_session.get.assert_called_once_with(Article, 999)
    mock_session.add.assert_not_called()
    mock_session.commit.assert_not_called()
    mock_session.refresh.assert_not_called()


def test_get_articles_by_status(mock_session, mock_article_model):
    """Test getting articles by status."""
    # Create test articles
    test_articles = [
        Article(
            id=1,
            url="https://example.com/news/1",
            title="Test Article 1",
            source="Example News",
            content="This is test article 1.",
            status=AnalysisStatus.ANALYSIS_SUCCEEDED.value,
            published_at=datetime.datetime.now(datetime.timezone.utc),
        ),
        Article(
            id=2,
            url="https://example.com/news/2",
            title="Test Article 2",
            source="Example News",
            content="This is test article 2.",
            status=AnalysisStatus.ANALYSIS_SUCCEEDED.value,
            published_at=datetime.datetime.now(datetime.timezone.utc),
        ),
    ]
    
    # Configure the mock
    mock_exec = MagicMock()
    mock_exec.all.return_value = test_articles
    mock_session.exec.return_value = mock_exec
    
    # Call the function
    result = get_articles_by_status(mock_session, AnalysisStatus.ANALYSIS_SUCCEEDED.value)
    
    # Assertions
    assert result == test_articles
    
    # Verify mock calls
    mock_session.exec.assert_called_once()
    mock_exec.all.assert_called_once()
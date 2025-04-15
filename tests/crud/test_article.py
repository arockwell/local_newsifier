"""Tests for Article CRUD operations."""

import datetime
from unittest.mock import MagicMock, patch

import pytest
from sqlmodel import Session, select

from local_newsifier.models.article import Article
from local_newsifier.models.state import AnalysisStatus
from local_newsifier.crud.article import (
    create_article,
    get_article,
    get_article_by_url,
    update_article_status,
    get_articles_by_status,
)


@pytest.fixture
def mock_session():
    """Create a mock SQLModel session."""
    session = MagicMock(spec=Session)
    return session


def test_create_article(mock_session):
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
    mock_db_article = MagicMock(spec=Article)
    for key, value in article_data.items():
        setattr(mock_db_article, key, value)
    mock_session.add = MagicMock()
    mock_session.commit = MagicMock()
    mock_session.refresh = MagicMock()
    
    # Use patch to make Article return our mock when instantiated
    with patch("local_newsifier.crud.article.Article", return_value=mock_db_article):
        # Call the function
        result = create_article(mock_session, article_data)
        
        # Assertions
        assert result == mock_db_article
        assert result.url == "https://example.com/news/1"
        assert result.title == "Test Article"
        assert result.source == "Example News"
        assert result.content == "This is a test article."
        assert result.status == AnalysisStatus.INITIALIZED.value
        assert result.published_at == now
        
        # Verify mock calls
        mock_session.add.assert_called_once_with(mock_db_article)
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once_with(mock_db_article)


def test_get_article(mock_session):
    """Test getting an article by ID."""
    # Create a test article
    test_article = MagicMock(spec=Article)
    test_article.id = 1
    test_article.url = "https://example.com/news/1"
    test_article.title = "Test Article"
    
    # Configure the mock
    mock_session.get.return_value = test_article
    
    # Call the function
    result = get_article(mock_session, 1)
    
    # Assertions
    assert result is test_article
    
    # Verify mock calls
    mock_session.get.assert_called_once_with(Article, 1)


def test_get_article_by_url(mock_session):
    """Test getting an article by URL."""
    # Create a test article
    test_article = MagicMock(spec=Article)
    test_article.id = 1
    test_article.url = "https://example.com/news/1"
    test_article.title = "Test Article"
    
    # Configure the mock
    mock_exec = MagicMock()
    mock_exec.first.return_value = test_article
    mock_session.exec.return_value = mock_exec
    
    # Use patch to handle the select query
    with patch("local_newsifier.crud.article.select", autospec=True) as mock_select:
        mock_where = MagicMock()
        mock_where.where.return_value = mock_where
        mock_select.return_value = mock_where
        
        # Call the function
        result = get_article_by_url(mock_session, "https://example.com/news/1")
        
        # Assertions
        assert result is test_article
        
        # Verify mock calls
        mock_session.exec.assert_called_once_with(mock_where)
        mock_exec.first.assert_called_once()


def test_update_article_status(mock_session):
    """Test updating an article's status."""
    # Create a test article
    test_article = MagicMock(spec=Article)
    test_article.id = 1
    test_article.status = AnalysisStatus.INITIALIZED.value
    
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


def test_update_article_status_not_found(mock_session):
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


def test_get_articles_by_status(mock_session):
    """Test getting articles by status."""
    # Create test articles
    test_articles = [
        MagicMock(spec=Article),
        MagicMock(spec=Article),
    ]
    test_articles[0].id = 1
    test_articles[0].status = AnalysisStatus.ANALYSIS_SUCCEEDED.value
    test_articles[1].id = 2
    test_articles[1].status = AnalysisStatus.ANALYSIS_SUCCEEDED.value
    
    # Configure the mock
    mock_exec = MagicMock()
    mock_exec.all.return_value = test_articles
    mock_session.exec.return_value = mock_exec
    
    # Use patch to handle the select query
    with patch("local_newsifier.crud.article.select", autospec=True) as mock_select:
        mock_where = MagicMock()
        mock_where.where.return_value = mock_where
        mock_select.return_value = mock_where
        
        # Call the function
        result = get_articles_by_status(mock_session, AnalysisStatus.ANALYSIS_SUCCEEDED.value)
        
        # Assertions
        assert result == test_articles
        
        # Verify mock calls
        mock_session.exec.assert_called_once_with(mock_where)
        mock_exec.all.assert_called_once()
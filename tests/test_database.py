"""Tests for database functionality."""

import pytest
from sqlalchemy.orm import Session
from sqlalchemy import text

from local_newsifier.database.manager import DatabaseManager
from local_newsifier.models.database import (ArticleCreate, ArticleDB, Base,
                                          EntityCreate, EntityDB, AnalysisResultCreate)


@pytest.fixture(scope="session")
def test_engine():
    """Create a test database engine."""
    from local_newsifier.config.database import get_database
    engine = get_database()
    return engine


@pytest.fixture(autouse=True)
def setup_test_db(test_engine):
    """Set up and tear down the test database for each test."""
    # Drop all tables and recreate schema
    with test_engine.connect() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))
        conn.commit()
    
    # Create all tables
    Base.metadata.create_all(test_engine)
    yield
    
    # Drop all tables after tests
    with test_engine.connect() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))
        conn.commit()


@pytest.fixture
def db_session(test_engine) -> Session:
    """Create a test database session."""
    from local_newsifier.config.database import get_db_session
    session_factory = get_db_session()
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def db_manager(db_session) -> DatabaseManager:
    """Create a database manager for testing."""
    return DatabaseManager(db_session)


def test_create_article(db_manager: DatabaseManager) -> None:
    """Test creating a new article."""
    article_data = ArticleCreate(
        url="https://example.com/test",
        title="Test Article",
        content="Test content",
        source="Test Source",
        published_at="2024-01-01T00:00:00Z"
    )
    
    article = db_manager.create_article(article_data)
    assert article is not None
    assert article.url == article_data.url
    assert article.title == article_data.title
    assert article.content == article_data.content
    assert article.source == article_data.source


def test_get_article(db_manager: DatabaseManager) -> None:
    """Test retrieving an article by ID."""
    # Create a test article
    article_data = ArticleCreate(
        url="https://example.com/test2",
        title="Test Article 2",
        content="Test content 2",
        source="Test Source",
        published_at="2024-01-01T00:00:00Z"
    )
    created_article = db_manager.create_article(article_data)
    
    # Retrieve the article
    retrieved_article = db_manager.get_article(created_article.id)
    assert retrieved_article is not None
    assert retrieved_article.id == created_article.id
    assert retrieved_article.url == article_data.url


def test_get_article_by_url(db_manager: DatabaseManager) -> None:
    """Test retrieving an article by URL."""
    # Create a test article
    article_data = ArticleCreate(
        url="https://example.com/test3",
        title="Test Article 3",
        content="Test content 3",
        source="Test Source",
        published_at="2024-01-01T00:00:00Z"
    )
    created_article = db_manager.create_article(article_data)
    
    # Retrieve the article
    retrieved_article = db_manager.get_article_by_url(article_data.url)
    assert retrieved_article is not None
    assert retrieved_article.id == created_article.id
    assert retrieved_article.url == article_data.url


def test_add_entity(db_manager: DatabaseManager) -> None:
    """Test adding an entity to an article."""
    # Create a test article
    article_data = ArticleCreate(
        url="https://example.com/test4",
        title="Test Article 4",
        content="Test content 4",
        source="Test Source",
        published_at="2024-01-01T00:00:00Z"
    )
    article = db_manager.create_article(article_data)
    
    # Add an entity
    entity_data = EntityCreate(
        text="Test Entity",
        entity_type="PERSON",
        confidence=0.95,
        article_id=article.id
    )
    entity = db_manager.add_entity(entity_data)
    
    assert entity is not None
    assert entity.text == entity_data.text
    assert entity.entity_type == entity_data.entity_type
    assert entity.confidence == entity_data.confidence
    assert entity.article_id == article.id


def test_add_analysis_result(db_manager: DatabaseManager) -> None:
    """Test adding an analysis result to an article."""
    # Create a test article
    article_data = ArticleCreate(
        url="https://example.com/test5",
        title="Test Article 5",
        content="Test content 5",
        source="Test Source",
        published_at="2024-01-01T00:00:00Z"
    )
    article = db_manager.create_article(article_data)
    
    # Add analysis result
    result_data = AnalysisResultCreate(
        article_id=article.id,
        analysis_type="sentiment",
        results={
            "sentiment": "positive",
            "confidence": 0.85,
            "keywords": ["test", "analysis"]
        }
    )
    analysis_result = db_manager.add_analysis_result(result_data)
    
    assert analysis_result is not None
    assert analysis_result.article_id == article.id
    assert analysis_result.results == result_data.results


def test_update_article_status(db_manager: DatabaseManager) -> None:
    """Test updating an article's status."""
    # Create a test article
    article_data = ArticleCreate(
        url="https://example.com/test6",
        title="Test Article 6",
        content="Test content 6",
        source="Test Source",
        published_at="2024-01-01T00:00:00Z"
    )
    article = db_manager.create_article(article_data)
    
    # Update status
    updated_article = db_manager.update_article_status(article.id, "PROCESSED")
    
    assert updated_article is not None
    assert updated_article.id == article.id
    assert updated_article.status == "PROCESSED"


def test_get_articles_by_status(db_manager: DatabaseManager) -> None:
    """Test retrieving articles by status."""
    # Create test articles with different statuses
    article1_data = ArticleCreate(
        url="https://example.com/test7",
        title="Test Article 7",
        content="Test content 7",
        source="Test Source",
        published_at="2024-01-01T00:00:00Z"
    )
    article1 = db_manager.create_article(article1_data)
    db_manager.update_article_status(article1.id, "PROCESSED")
    
    article2_data = ArticleCreate(
        url="https://example.com/test8",
        title="Test Article 8",
        content="Test content 8",
        source="Test Source",
        published_at="2024-01-01T00:00:00Z"
    )
    article2 = db_manager.create_article(article2_data)
    db_manager.update_article_status(article2.id, "PENDING")
    
    # Get processed articles
    processed_articles = db_manager.get_articles_by_status("PROCESSED")
    assert len(processed_articles) == 1
    assert processed_articles[0].id == article1.id
    
    # Get pending articles
    pending_articles = db_manager.get_articles_by_status("PENDING")
    assert len(pending_articles) == 1
    assert pending_articles[0].id == article2.id

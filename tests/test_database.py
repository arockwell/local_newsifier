"""Tests for database functionality."""

from datetime import UTC, datetime
from typing import Generator

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from local_newsifier.config.database import get_engine, get_session
from local_newsifier.database.manager import DatabaseManager
from local_newsifier.models.database import (AnalysisResult,
                                             AnalysisResultCreate,
                                             AnalysisResultDB, Article,
                                             ArticleCreate, ArticleDB, Base,
                                             Entity, EntityCreate, EntityDB)


@pytest.fixture(scope="session")
def test_engine():
    """Create a test database engine."""
    engine = get_engine()
    return engine


@pytest.fixture(autouse=True)
def setup_test_db(test_engine):
    """Set up and tear down the test database for each test."""
    # Create all tables
    Base.metadata.create_all(test_engine)
    yield
    # Drop all tables
    Base.metadata.drop_all(test_engine)


@pytest.fixture
def db_session(test_engine) -> Generator[Session, None, None]:
    """Create a test database session."""
    session_factory = get_session()
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def db_manager(db_session: Session) -> DatabaseManager:
    """Create a database manager instance."""
    return DatabaseManager(db_session)


@pytest.fixture
def sample_article() -> ArticleCreate:
    return ArticleCreate(
        url="https://example.com/test",
        title="Test Article",
        content="This is a test article",
        published_at=datetime.now(UTC),
        status="new",
    )


def test_create_article(db_manager: DatabaseManager, sample_article: ArticleCreate):
    """Test creating an article."""
    # Create article
    article = db_manager.create_article(sample_article)

    # Verify article was created
    assert article.id is not None
    assert article.url == sample_article.url
    assert article.title == sample_article.title
    assert article.status == sample_article.status


def test_get_article(db_manager: DatabaseManager, sample_article: ArticleCreate):
    """Test getting an article by ID."""
    # Create article
    created_article = db_manager.create_article(sample_article)

    # Get article
    retrieved_article = db_manager.get_article(created_article.id)

    # Verify article was retrieved
    assert retrieved_article is not None
    assert retrieved_article.id == created_article.id
    assert retrieved_article.url == sample_article.url


def test_get_article_by_url(db_manager: DatabaseManager, sample_article: ArticleCreate):
    """Test getting an article by URL."""
    # Create article
    db_manager.create_article(sample_article)

    # Get article
    retrieved_article = db_manager.get_article_by_url(sample_article.url)

    # Verify article was retrieved
    assert retrieved_article is not None
    assert retrieved_article.url == sample_article.url


def test_add_entity(db_manager: DatabaseManager, sample_article: ArticleCreate):
    """Test adding an entity to an article."""
    # Create article
    article = db_manager.create_article(sample_article)

    # Add entity
    entity = EntityCreate(
        article_id=article.id, text="Test Entity", entity_type="PERSON", confidence=0.95
    )
    created_entity = db_manager.add_entity(entity)

    # Verify entity was created
    assert created_entity.id is not None
    assert created_entity.article_id == article.id
    assert created_entity.text == entity.text


def test_add_analysis_result(
    db_manager: DatabaseManager, sample_article: ArticleCreate
):
    """Test adding an analysis result to an article."""
    # Create article
    article = db_manager.create_article(sample_article)

    # Add analysis result
    result = AnalysisResultCreate(
        article_id=article.id,
        analysis_type="NER",
        results={"entities": ["Test Entity"]},
    )
    created_result = db_manager.add_analysis_result(result)

    # Verify result was created
    assert created_result.id is not None
    assert created_result.article_id == article.id
    assert created_result.analysis_type == result.analysis_type
    assert created_result.results == result.results


def test_update_article_status(
    db_manager: DatabaseManager, sample_article: ArticleCreate
):
    """Test updating an article's status."""
    # Create article
    article = db_manager.create_article(sample_article)

    # Update status
    new_status = "analyzed"
    updated_article = db_manager.update_article_status(article.id, new_status)

    # Verify status was updated
    assert updated_article is not None
    assert updated_article.id == article.id
    assert updated_article.status == new_status


def test_get_articles_by_status(db_manager, db_session):
    # Create two articles with different statuses
    article1 = ArticleDB(
        url="https://example.com/test1",
        title="Test Article 1",
        content="This is test article 1",
        published_at=datetime.now(UTC),
        status="new",
        scraped_at=datetime.now(UTC),
    )
    article2 = ArticleDB(
        url="https://example.com/test2",
        title="Test Article 2",
        content="This is test article 2",
        published_at=datetime.now(UTC),
        status="analyzed",
        scraped_at=datetime.now(UTC),
    )
    db_session.add_all([article1, article2])
    db_session.commit()

    # Get articles by status
    new_articles = db_manager.get_articles_by_status("new")
    analyzed_articles = db_manager.get_articles_by_status("analyzed")

    # Verify articles were retrieved
    assert len(new_articles) == 1
    assert len(analyzed_articles) == 1
    assert new_articles[0].url == "https://example.com/test1"
    assert analyzed_articles[0].url == "https://example.com/test2"

"""Tests for database functionality."""

import pytest
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import text
from uuid import uuid4
import sqlalchemy.exc

from local_newsifier.database.manager import DatabaseManager
from local_newsifier.models.database import (ArticleCreate, ArticleDB, Base,
                                          EntityCreate, EntityDB, AnalysisResultCreate,
                                          ProcessedURLDB, AnalysisResultDB)
from local_newsifier.models.state import NewsAnalysisState, AnalysisStatus
from local_newsifier.repositories.analysis_repository import AnalysisRepository
from local_newsifier.repositories.rss_cache_repository import RSSCacheRepository


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


@pytest.fixture
def analysis_repo(db_session) -> AnalysisRepository:
    """Create an analysis repository for testing."""
    return AnalysisRepository(db_session)


@pytest.fixture
def rss_cache_repo(db_session) -> RSSCacheRepository:
    """Create an RSS cache repository for testing."""
    return RSSCacheRepository(db_session)


def test_rss_cache_repository(rss_cache_repo: RSSCacheRepository) -> None:
    """Test RSS cache repository functionality."""
    # Test adding and checking URLs
    test_url = "https://example.com/article1"
    test_feed = "https://example.com/feed"
    
    # URL should not be processed initially
    assert not rss_cache_repo.is_processed(test_url)
    
    # Add URL to cache
    rss_cache_repo.add_processed_url(test_url, test_feed)
    
    # URL should now be processed
    assert rss_cache_repo.is_processed(test_url)
    
    # Test getting processed URLs for feed
    processed_urls = rss_cache_repo.get_processed_urls(test_feed)
    assert test_url in processed_urls
    
    # Test getting new URLs
    urls = [test_url, "https://example.com/article2"]
    new_urls = rss_cache_repo.get_new_urls(urls, test_feed)
    assert len(new_urls) == 1
    assert "https://example.com/article2" in new_urls


def test_analysis_repository(analysis_repo: AnalysisRepository, db_session: Session) -> None:
    """Test analysis repository functionality."""
    # Create test state
    state = NewsAnalysisState(
        target_url="https://example.com/article1",
        run_id=uuid4()
    )
    
    # Add some test data
    state.scraped_title = "Test Article"
    state.source = "Example News"
    state.published_at = datetime.now(timezone.utc)
    state.scraped_at = datetime.now(timezone.utc)
    state.scraped_text = "This is a test article."
    state.analysis_config = {"model": "test"}
    state.analysis_results = {"entities": []}
    
    # Save state
    saved_state = analysis_repo.save(state)
    
    # Verify save was successful
    assert saved_state.status == AnalysisStatus.COMPLETED_SUCCESS
    assert saved_state.save_path.startswith("db://analysis_results/")
    
    # Verify article was created
    article = db_session.query(ArticleDB).filter_by(url=state.target_url).first()
    assert article is not None
    assert article.title == state.scraped_title
    assert article.content == state.scraped_text
    
    # Verify analysis result was created
    analysis_result = db_session.query(AnalysisResultDB).filter_by(article_id=article.id).first()
    assert analysis_result is not None
    assert analysis_result.analysis_type == "news_analysis"
    assert analysis_result.results["run_id"] == str(state.run_id)


def test_analysis_repository_error_handling(analysis_repo: AnalysisRepository) -> None:
    """Test analysis repository error handling."""
    # Create test state with invalid data
    state = NewsAnalysisState(
        target_url="https://example.com/article2",
        run_id=uuid4()
    )
    
    # Add invalid data that should cause a database error
    state.scraped_text = "Test content"  # Add some content
    state.analysis_results = {"invalid": object()}  # This will fail JSON serialization
    
    # Attempt to save state
    with pytest.raises(sqlalchemy.exc.StatementError) as exc_info:  # SQLAlchemy wraps the TypeError
        analysis_repo.save(state)
    assert "Object of type object is not JSON serializable" in str(exc_info.value)
    
    assert state.status == AnalysisStatus.SAVE_FAILED
    assert state.error_details is not None
    assert state.error_details.task == "saving"


def test_rss_cache_cleanup(rss_cache_repo: RSSCacheRepository, db_session: Session) -> None:
    """Test RSS cache cleanup functionality."""
    # Add some test URLs
    test_urls = [
        ("https://example.com/article1", "https://example.com/feed1"),
        ("https://example.com/article2", "https://example.com/feed1"),
        ("https://example.com/article3", "https://example.com/feed2")
    ]
    
    for url, feed_url in test_urls:
        rss_cache_repo.add_processed_url(url, feed_url)
    
    # Verify URLs were added
    assert db_session.query(ProcessedURLDB).count() == 3
    
    # Clean up URLs
    rss_cache_repo.cleanup_old_urls(days=0)
    
    # Verify URLs were cleaned up
    assert db_session.query(ProcessedURLDB).count() == 0


def test_save_analysis_result(db_session, analysis_repo):
    """Test saving an analysis result."""
    # First create an article
    article = ArticleDB(
        url="https://example.com",
        title="Test Article",
        content="Test content",
        status="analyzed"
    )
    db_session.add(article)
    db_session.flush()

    # Create a test result
    result = AnalysisResultDB(
        article_id=article.id,
        analysis_type="entity_analysis",
        results={"entities": [{"text": "Test", "type": "PERSON"}]},
        created_at=datetime.now(timezone.utc)
    )
    
    # Save the result
    db_session.add(result)
    db_session.commit()
    
    # Verify the result was saved
    saved_result = db_session.query(AnalysisResultDB).first()
    assert saved_result is not None
    assert saved_result.article_id == article.id
    assert saved_result.analysis_type == "entity_analysis"
    assert saved_result.results == {"entities": [{"text": "Test", "type": "PERSON"}]}

"""Tests for database storage implementation."""

import pytest
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from uuid import uuid4

from local_newsifier.models.database import init_db, Base
from local_newsifier.models.state import NewsAnalysisState, AnalysisStatus
from local_newsifier.repositories.analysis_repository import AnalysisRepository
from local_newsifier.repositories.rss_cache_repository import RSSCacheRepository


@pytest.fixture
def test_db():
    """Create a test database in memory."""
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture
def session(test_db):
    """Create a test database session."""
    Session = sessionmaker(bind=test_db)
    return Session()


@pytest.fixture
def rss_cache_repo(session):
    """Create an RSS cache repository for testing."""
    return RSSCacheRepository(session)


@pytest.fixture
def analysis_repo(session):
    """Create an analysis repository for testing."""
    return AnalysisRepository(session)


def test_rss_cache_repository(rss_cache_repo):
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


def test_analysis_repository(analysis_repo):
    """Test analysis repository functionality."""
    # Create test state
    state = NewsAnalysisState(
        target_url="https://example.com/article1",
        run_id=uuid4(),
        created_at=datetime.now(timezone.utc)
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
    assert saved_state.status == AnalysisStatus.SAVE_SUCCEEDED
    assert saved_state.save_path.startswith("db://analysis_results/")
    
    # Test retrieving state
    retrieved_state = analysis_repo.get(state.run_id)
    assert retrieved_state is not None
    assert retrieved_state.target_url == state.target_url
    assert retrieved_state.run_id == state.run_id
    
    # Test listing results
    results = analysis_repo.list({"status": AnalysisStatus.SAVE_SUCCEEDED})
    assert len(results) > 0
    assert any(r.results["run_id"] == str(state.run_id) for r in results) 
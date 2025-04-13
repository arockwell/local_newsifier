"""Tests for database models using PostgreSQL."""

import os
import uuid
import pytest
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from local_newsifier.config.database import get_cursor_db_name
from local_newsifier.models.database import Base, ArticleDB, EntityDB, AnalysisResultDB
from local_newsifier.models.state import AnalysisStatus


@pytest.fixture(scope="session")
def test_db_name():
    """Create a unique test database name."""
    test_id = str(uuid.uuid4())[:8]
    return f"local_newsifier_test_{test_id}"


@pytest.fixture(scope="session")
def postgres_url(test_db_name):
    """Create a PostgreSQL URL for testing."""
    # Get PostgreSQL connection details from environment or use defaults
    user = os.environ.get("POSTGRES_USER", "postgres")
    password = os.environ.get("POSTGRES_PASSWORD", "postgres")
    host = os.environ.get("POSTGRES_HOST", "localhost")
    port = os.environ.get("POSTGRES_PORT", "5432")
    
    return f"postgresql://{user}:{password}@{host}:{port}/{test_db_name}"


@pytest.fixture(scope="session")
def engine(postgres_url):
    """Create a PostgreSQL engine for testing."""
    # Connect to default postgres database to create test db
    admin_url = postgres_url.rsplit('/', 1)[0] + "/postgres"
    admin_engine = create_engine(admin_url)
    test_db_name = postgres_url.rsplit('/', 1)[1]
    
    # Create test database
    with admin_engine.connect() as conn:
        conn.execute(f"DROP DATABASE IF EXISTS {test_db_name}")
        conn.execute(f"CREATE DATABASE {test_db_name}")
        
    # Connect to test database
    engine = create_engine(postgres_url)
    Base.metadata.create_all(engine)
    
    yield engine
    
    # Drop test database
    engine.dispose()
    with admin_engine.connect() as conn:
        # Terminate all connections to the test database
        conn.execute(f"""
            SELECT pg_terminate_backend(pg_stat_activity.pid)
            FROM pg_stat_activity
            WHERE pg_stat_activity.datname = '{test_db_name}'
            AND pid <> pg_backend_pid();
        """)
        conn.execute(f"DROP DATABASE IF EXISTS {test_db_name}")
    
    admin_engine.dispose()


@pytest.fixture
def session(engine):
    """Create a database session for testing."""
    Session = sessionmaker(bind=engine)
    session = Session()
    
    yield session
    
    # Rollback any changes
    session.rollback()
    session.close()


def test_article_creation(session):
    """Test creating an article in the database."""
    # Create an article
    article = ArticleDB(
        url="https://example.com/news/1",
        title="Test Article",
        source="example.com",
        content="This is a test article about PostgreSQL.",
        status=AnalysisStatus.INITIALIZED.value
    )
    
    # Add to session and commit
    session.add(article)
    session.commit()
    
    # Query to verify
    result = session.query(ArticleDB).filter_by(url="https://example.com/news/1").first()
    
    # Verify
    assert result is not None
    assert result.id is not None
    assert result.url == "https://example.com/news/1"
    assert result.title == "Test Article"
    assert result.source == "example.com"
    assert result.content == "This is a test article about PostgreSQL."
    assert result.status == AnalysisStatus.INITIALIZED.value
    assert isinstance(result.created_at, datetime)
    assert isinstance(result.updated_at, datetime)
    assert isinstance(result.scraped_at, datetime)


def test_entity_creation_and_relationship(session):
    """Test creating entities with relationship to article."""
    # Create an article
    article = ArticleDB(
        url="https://example.com/news/2",
        title="PostgreSQL Article",
        source="example.com",
        content="PostgreSQL is a powerful open-source database.",
        status=AnalysisStatus.SCRAPE_SUCCEEDED.value
    )
    
    # Create entities
    entity1 = EntityDB(
        text="PostgreSQL",
        entity_type="TECHNOLOGY",
        confidence=0.95,
        sentence_context="PostgreSQL is a powerful open-source database."
    )
    
    entity2 = EntityDB(
        text="database",
        entity_type="TECHNOLOGY",
        confidence=0.85,
        sentence_context="PostgreSQL is a powerful open-source database."
    )
    
    # Add entities to article
    article.entities.append(entity1)
    article.entities.append(entity2)
    
    # Add to session and commit
    session.add(article)
    session.commit()
    
    # Query to verify
    result = session.query(ArticleDB).filter_by(url="https://example.com/news/2").first()
    
    # Verify
    assert result is not None
    assert len(result.entities) == 2
    assert result.entities[0].text == "PostgreSQL"
    assert result.entities[1].text == "database"
    assert result.entities[0].article_id == result.id
    assert result.entities[1].article_id == result.id
    
    # Verify entity fields
    assert result.entities[0].confidence == 0.95
    assert result.entities[0].sentence_context == "PostgreSQL is a powerful open-source database."


def test_analysis_result_creation(session):
    """Test creating analysis results for an article."""
    # Create an article
    article = ArticleDB(
        url="https://example.com/news/3",
        title="Analysis Test",
        source="example.com",
        content="This is a test for analysis results.",
        status=AnalysisStatus.ANALYSIS_SUCCEEDED.value
    )
    
    # Create analysis result
    analysis = AnalysisResultDB(
        analysis_type="sentiment",
        results={"score": 0.75, "label": "positive"}
    )
    
    # Add analysis to article
    article.analysis_results.append(analysis)
    
    # Add to session and commit
    session.add(article)
    session.commit()
    
    # Query to verify
    result = session.query(ArticleDB).filter_by(url="https://example.com/news/3").first()
    
    # Verify
    assert result is not None
    assert len(result.analysis_results) == 1
    assert result.analysis_results[0].analysis_type == "sentiment"
    assert result.analysis_results[0].results["score"] == 0.75
    assert result.analysis_results[0].results["label"] == "positive"


def test_cascade_delete(session):
    """Test that deleting an article cascades to its entities and analysis results."""
    # Create an article with entities and analysis results
    article = ArticleDB(
        url="https://example.com/news/4",
        title="Cascade Test",
        source="example.com",
        content="This is a test for cascade delete.",
        status=AnalysisStatus.COMPLETED_SUCCESS.value
    )
    
    # Create entities
    entity = EntityDB(
        text="cascade",
        entity_type="CONCEPT",
        confidence=0.9,
        sentence_context="This is a test for cascade delete."
    )
    
    # Create analysis result
    analysis = AnalysisResultDB(
        analysis_type="keywords",
        results={"keywords": ["cascade", "delete", "test"]}
    )
    
    # Add to article
    article.entities.append(entity)
    article.analysis_results.append(analysis)
    
    # Add to session and commit
    session.add(article)
    session.commit()
    
    # Get IDs for verification
    article_id = article.id
    entity_id = entity.id
    analysis_id = analysis.id
    
    # Delete article
    session.delete(article)
    session.commit()
    
    # Verify article is deleted
    assert session.query(ArticleDB).filter_by(id=article_id).first() is None
    
    # Verify entities are deleted
    assert session.query(EntityDB).filter_by(id=entity_id).first() is None
    
    # Verify analysis results are deleted
    assert session.query(AnalysisResultDB).filter_by(id=analysis_id).first() is None


def test_query_by_status(session):
    """Test querying articles by status."""
    # Create articles with different statuses
    articles = [
        ArticleDB(
            url=f"https://example.com/news/status/{i}",
            title=f"Status Test {i}",
            source="example.com",
            status=status.value
        )
        for i, status in enumerate([
            AnalysisStatus.INITIALIZED,
            AnalysisStatus.SCRAPE_SUCCEEDED,
            AnalysisStatus.ANALYSIS_SUCCEEDED,
            AnalysisStatus.INITIALIZED,  # Duplicate status
        ])
    ]
    
    # Add to session and commit
    session.add_all(articles)
    session.commit()
    
    # Query by status
    initialized = session.query(ArticleDB).filter_by(status=AnalysisStatus.INITIALIZED.value).all()
    
    # Verify
    assert len(initialized) == 2
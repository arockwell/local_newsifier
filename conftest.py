"""Global test configuration for all tests.

This module provides:
1. SQLModel metadata registration in a controlled order
2. Database engine and session fixtures for tests
3. Transaction-based isolation for tests
4. Various test utilities and fixtures
"""

import os
from datetime import datetime, timezone
from typing import Generator, Dict, Any, Optional, List
import uuid
import logging

import pytest
from sqlmodel import SQLModel, Session, create_engine, text, select

# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# First, reset and register all models in a controlled order
# This must run before any database operations
SQLModel.metadata.clear()

# Import and register models in a specific order
# Base models 
from local_newsifier.models.base import TableBase

# Core models
from local_newsifier.models.article import Article
from local_newsifier.models.entity import Entity
from local_newsifier.models.analysis_result import AnalysisResult

# Entity tracking models
from local_newsifier.models.entity_tracking import (
    CanonicalEntity, EntityMention, EntityMentionContext,
    EntityProfile, EntityRelationship
)

# Sentiment models
from local_newsifier.models.sentiment import (
    SentimentAnalysis, OpinionTrend, SentimentShift
)

# State models
from local_newsifier.models.state import AnalysisStatus, NewsAnalysisState

# Trend models
from local_newsifier.models.trend import (
    TrendAnalysis, TrendEntity, TrendEvidenceItem, TrendStatus, TrendType
)

# Import all utilities from tests.utils package
from tests.utils.factories import *
from tests.utils.mocks import *
from tests.utils.api_testing import *
from tests.utils.env_management import *
from tests.utils.db_verification import *

# -------------------------------------------------------------------
# Database fixtures with different scopes
# -------------------------------------------------------------------

@pytest.fixture(scope="session")
def test_db_url() -> str:
    """Get the test database URL.
    
    This fixture:
    1. Uses TEST_DATABASE_URL environment variable if available
    2. Falls back to a SQLite in-memory database if not specified
    3. For CI environments, uses the postgres service configuration
    """
    env_url = os.environ.get("TEST_DATABASE_URL")
    if env_url:
        logger.info(f"Using database URL from environment: {env_url}")
        return env_url
        
    # Check if we're running in a CI environment
    if os.environ.get("CI"):
        # Use PostgreSQL in CI environment
        logger.info("Using PostgreSQL in CI environment")
        return "postgresql://postgres:postgres@localhost:5432/test_db"
    
    # Generate a unique test database name for Cursor
    cursor_id = os.environ.get("CURSOR_DB_ID")
    if cursor_id:
        logger.info(f"Using Cursor database ID: {cursor_id}")
        test_db_name = f"test_local_newsifier_{cursor_id}"
        
        # Try to construct a PostgreSQL URL if PostgreSQL env vars are available
        pg_user = os.environ.get("POSTGRES_USER")
        pg_pass = os.environ.get("POSTGRES_PASSWORD")
        pg_host = os.environ.get("POSTGRES_HOST")
        pg_port = os.environ.get("POSTGRES_PORT")
        
        if all([pg_user, pg_pass, pg_host, pg_port]):
            logger.info(f"Using PostgreSQL with cursor ID: {cursor_id}")
            return f"postgresql://{pg_user}:{pg_pass}@{pg_host}:{pg_port}/{test_db_name}"
    
    # Default to SQLite in-memory
    logger.info("Using SQLite in-memory database")
    return "sqlite:///:memory:"

@pytest.fixture(scope="session")
def test_engine(test_db_url):
    """Create and initialize the test database.
    
    This fixture:
    1. Creates an engine connected to the test database
    2. Creates all tables
    3. Yields the engine for tests
    4. Disposes the engine after all tests
    """
    logger.info(f"Creating test engine with URL: {test_db_url}")
    
    # Create engine with appropriate URL
    if test_db_url.startswith("sqlite"):
        # SQLite-specific connect args
        engine = create_engine(
            test_db_url,
            connect_args={"check_same_thread": False},
        )
    else:
        # Default engine for PostgreSQL or other databases
        engine = create_engine(test_db_url)
    
    # Create all tables
    SQLModel.metadata.create_all(engine)
    
    # Verify tables were created by trying to insert and select
    with Session(engine) as session:
        # Create a test article with all required fields
        test_article = Article(
            title="Test Article",
            content="Test Content",
            url="https://example.com/test",
            source="test_source",
            status="new",
            published_at=datetime.now(timezone.utc),
            scraped_at=datetime.now(timezone.utc),
        )
        session.add(test_article)
        session.commit()
        
        # Query to verify it exists
        statement = select(Article).where(Article.title == "Test Article")
        result = session.exec(statement).first()
        
        if not result:
            pytest.fail("Failed to verify table creation")
        
        # Clean up the test data
        session.delete(result)
        session.commit()
    
    # Yield the engine for tests to use
    yield engine
    
    # Clean up
    engine.dispose()

@pytest.fixture(scope="function")
def db_function_session(test_engine) -> Generator[Session, None, None]:
    """Provide a function-scoped database session with transaction isolation."""
    connection = test_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()

@pytest.fixture(scope="module")
def db_module_session(test_engine) -> Generator[Session, None, None]:
    """Provide a module-scoped database session with transaction isolation."""
    connection = test_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()

@pytest.fixture(scope="class")
def db_class_session(test_engine) -> Generator[Session, None, None]:
    """Provide a class-scoped database session with transaction isolation."""
    connection = test_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()

# For backward compatibility - alias db_function_session as db_session
@pytest.fixture
def db_session(db_function_session) -> Session:
    """Alias for db_function_session for backward compatibility."""
    return db_function_session

# -------------------------------------------------------------------
# Pre-populated data fixtures
# -------------------------------------------------------------------

@pytest.fixture(scope="function")
def populated_db(db_function_session):
    """Create a database with standard test data."""
    # Set the session for all factories
    ArticleFactory._meta.sqlalchemy_session = db_function_session
    EntityFactory._meta.sqlalchemy_session = db_function_session
    CanonicalEntityFactory._meta.sqlalchemy_session = db_function_session
    EntityRelationshipFactory._meta.sqlalchemy_session = db_function_session
    
    # Create standard test data
    articles = ArticleFactory.create_batch(5)
    entities = []
    
    # Create entities for each article
    for article in articles:
        article_entities = EntityFactory.create_batch(3, article=article)
        entities.extend(article_entities)
    
    # Create canonical entities and relationships
    canonical_entities = CanonicalEntityFactory.create_batch(3)
    relationships = []
    
    # Create relationships between canonical entities
    for i in range(len(canonical_entities) - 1):
        relationship = EntityRelationshipFactory.create(
            source_entity=canonical_entities[i],
            target_entity=canonical_entities[i+1]
        )
        relationships.append(relationship)
    
    # Create a circular relationship
    relationship = EntityRelationshipFactory.create(
        source_entity=canonical_entities[-1],
        target_entity=canonical_entities[0]
    )
    relationships.append(relationship)
    
    db_function_session.commit()
    
    # Return a dictionary of created objects for test use
    return {
        "session": db_function_session,
        "articles": articles,
        "entities": entities,
        "canonical_entities": canonical_entities,
        "relationships": relationships
    }

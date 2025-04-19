"""Global test configuration to ensure consistent table registration.

This module handles:
1. SQLModel metadata registration in a controlled order
2. SQLite in-memory database setup for tests
3. Session and transaction management for tests
"""

import os
from datetime import datetime, timezone
from typing import Generator
import uuid

import pytest
from sqlmodel import SQLModel, Session, create_engine, text, select

# First, reset and register all models in a controlled order
# This must run before any database operations
SQLModel.metadata.clear()

# Import and register models in a specific order
# Base models 
from local_newsifier.models.database.base import TableBase

# Core models
from local_newsifier.models.database.article import Article
from local_newsifier.models.database.entity import Entity
from local_newsifier.models.database.analysis_result import AnalysisResult

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

@pytest.fixture(scope="session")
def test_engine():
    """Create a test database engine using SQLite in-memory.
    
    This fixture:
    1. Creates an in-memory SQLite database
    2. Creates all tables
    3. Yields the engine for tests
    """
    # Create SQLite in-memory engine for tests
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    
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
    
    # No cleanup needed for in-memory database
    engine.dispose()

@pytest.fixture
def db_session(test_engine) -> Generator[Session, None, None]:
    """Provide a database session with transaction isolation.
    
    This fixture:
    1. Creates a new connection to the database
    2. Starts a transaction
    3. Yields a session bound to that connection
    4. Rolls back the transaction after the test
    5. Closes the connection
    
    This ensures that tests are isolated from each other and don't affect
    the database state outside of their own transaction.
    """
    # Start a new connection
    connection = test_engine.connect()
    # Start a transaction
    transaction = connection.begin()
    
    # Create a session bound to this connection
    session = Session(bind=connection)
    
    try:
        # Yield the session for test use
        yield session
    finally:
        # Always roll back and close, even if test fails
        session.close()
        transaction.rollback()
        connection.close()
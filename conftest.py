"""Global test configuration to ensure consistent table registration.

This module handles:
1. SQLModel metadata registration in a controlled order
2. PostgreSQL test database creation and cleanup
3. Session and transaction management for tests
"""

import os
from typing import Generator
import uuid

import pytest
from sqlmodel import SQLModel, Session, create_engine, text

# First, reset and register all models in a controlled order
# This must run before any database operations
SQLModel.metadata.clear()

# Import and register models in a specific order
# Base models first
from local_newsifier.models.database.base import TableBase

# Core models next
from local_newsifier.models.database.article import Article
from local_newsifier.models.database.entity import Entity
from local_newsifier.models.database.analysis_result import AnalysisResult

# Entity tracking models
from local_newsifier.models.entity_tracking import (
    CanonicalEntity, EntityMention, EntityMentionContext,
    EntityProfile, EntityRelationship
)

# Sentiment models last
from local_newsifier.models.sentiment import (
    SentimentAnalysis, OpinionTrend, SentimentShift
)

# Utility function to get postgres URL for tests
def get_test_postgres_url() -> str:
    """Get PostgreSQL URL for tests with a unique test database name."""
    # Generate a unique test database name to prevent conflicts
    test_id = str(uuid.uuid4())[:8]
    test_db_name = f"test_local_newsifier_{test_id}"
    
    # Get database connection parameters from environment or use defaults
    user = os.environ.get("POSTGRES_USER", "postgres")
    password = os.environ.get("POSTGRES_PASSWORD", "postgres")
    host = os.environ.get("POSTGRES_HOST", "localhost")
    port = os.environ.get("POSTGRES_PORT", "5432")
    
    # Return the full PostgreSQL URL
    return f"postgresql://{user}:{password}@{host}:{port}/{test_db_name}"

@pytest.fixture(scope="session")
def postgres_url() -> str:
    """Provide the PostgreSQL URL for tests."""
    return get_test_postgres_url()

@pytest.fixture(scope="session")
def test_engine(postgres_url: str):
    """Create a test database engine.
    
    This fixture:
    1. Creates a fresh test database
    2. Creates all tables
    3. Yields the engine for tests
    4. Drops the database afterward
    """
    # Parse the database name from the URL
    test_db_name = postgres_url.rsplit('/', 1)[1]
    
    # Connect to the default postgres database
    admin_url = postgres_url.rsplit('/', 1)[0] + "/postgres"
    admin_engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")
    
    # Create the test database
    try:
        with admin_engine.connect() as conn:
            conn.execute(text(f"DROP DATABASE IF EXISTS {test_db_name}"))
            conn.execute(text(f"CREATE DATABASE {test_db_name}"))
    except Exception as e:
        pytest.fail(f"Failed to create test database: {e}")
    finally:
        admin_engine.dispose()
    
    # Create the engine for the test database
    engine = create_engine(
        postgres_url,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
        connect_args={"application_name": "local_newsifier_test"}
    )
    
    # Create all tables
    try:
        SQLModel.metadata.create_all(engine)
    except Exception as e:
        pytest.fail(f"Failed to create tables: {e}")
    
    # Verify all tables were created
    expected_tables = {
        'article', 'entity', 'analysis_result', 
        'canonical_entity', 'entity_mention', 
        'entity_mention_context', 'entity_profile',
        'entity_relationship', 'sentiment_analysis',
        'opinion_trend', 'sentiment_shift'
    }
    
    with engine.connect() as conn:
        result = conn.execute(text(
            "SELECT table_name FROM information_schema.tables WHERE table_schema='public'"
        ))
        actual_tables = {row[0] for row in result}
        
        missing_tables = expected_tables - actual_tables
        if missing_tables:
            pytest.fail(f"Missing tables in database: {missing_tables}")
    
    # Yield the engine for tests to use
    yield engine
    
    # Cleanup: Drop the test database after all tests
    engine.dispose()
    
    try:
        admin_engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")
        with admin_engine.connect() as conn:
            # Terminate all connections to the test database
            conn.execute(text(f"""
                SELECT pg_terminate_backend(pg_stat_activity.pid)
                FROM pg_stat_activity
                WHERE pg_stat_activity.datname = '{test_db_name}'
                AND pid <> pg_backend_pid();
            """))
            # Drop the test database
            conn.execute(text(f"DROP DATABASE IF EXISTS {test_db_name}"))
    except Exception as e:
        print(f"Warning: Failed to drop test database: {e}")
    finally:
        admin_engine.dispose()

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
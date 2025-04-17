"""Test configuration and fixtures."""

import os
import uuid
from typing import Generator
import time

import pytest
import psycopg2
from sqlmodel import Session, SQLModel, create_engine, text

from local_newsifier.config.database import DatabaseSettings

# Import all models to ensure they're registered with SQLModel.metadata
# Database models
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


def get_test_db_name() -> str:
    """Get a unique test database name.
    
    Returns:
        A unique test database name based on process ID and timestamp
    """
    pid = os.getpid()
    timestamp = int(time.time())
    return f"test_local_newsifier_{pid}_{timestamp}"


@pytest.fixture(scope="session")
def postgres_url():
    """Get PostgreSQL URL for tests."""
    settings = DatabaseSettings()
    test_db_name = get_test_db_name()
    base_url = settings.get_database_url()
    return base_url.replace(settings.POSTGRES_DB, test_db_name)


@pytest.fixture(scope="session")
def test_engine(postgres_url):
    """Create a test database engine.
    
    This version is compatible with both local development and CI environments.
    """
    test_db_name = postgres_url.rsplit('/', 1)[1]
    
    # Connect to default postgres database to create test db
    try:
        # Connect to default postgres database to create test db
        admin_url = postgres_url.rsplit('/', 1)[0] + "/postgres"
        admin_engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")
        
        # Create test database
        with admin_engine.connect() as conn:
            conn.execute(text(f"DROP DATABASE IF EXISTS {test_db_name}"))
            conn.execute(text(f"CREATE DATABASE {test_db_name}"))
    except Exception as e:
        print(f"Error creating test database: {e}")
        # If we can't create the database, try connecting directly
        # (it might already exist in CI)
    
    # Create engine for the test database
    engine = create_engine(postgres_url)
    
    # Create all tables
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)
    
    yield engine
    
    # Cleanup after all tests
    try:
        # Connect to default postgres database to drop test db
        admin_url = postgres_url.rsplit('/', 1)[0] + "/postgres"
        admin_engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")
        
        # Drop test database
        with admin_engine.connect() as conn:
            conn.execute(text(f"""
                SELECT pg_terminate_backend(pg_stat_activity.pid)
                FROM pg_stat_activity
                WHERE pg_stat_activity.datname = '{test_db_name}'
                AND pid <> pg_backend_pid();
            """))
            conn.execute(text(f"DROP DATABASE IF EXISTS {test_db_name}"))
    except Exception as e:
        print(f"Error dropping test database: {e}")
        # In CI, we may not have permissions to drop databases
    
    engine.dispose()  # Close all connections


@pytest.fixture(autouse=True)
def setup_test_db(test_engine) -> Generator[None, None, None]:
    """Set up and tear down the test database for each test."""
    # Clear all data but don't drop tables
    with test_engine.connect() as conn:
        # Clear all data from tables
        conn.execute(text("""
            DO $$ 
            DECLARE
                r RECORD;
            BEGIN
                FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public') LOOP
                    EXECUTE 'TRUNCATE TABLE ' || quote_ident(r.tablename) || ' CASCADE';
                END LOOP;
            END $$;
        """))
        conn.commit()
    yield


@pytest.fixture
def db_session(test_engine) -> Generator[Session, None, None]:
    """Create a test database session."""
    with Session(test_engine) as session:
        yield session
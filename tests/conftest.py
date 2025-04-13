"""Test configuration and fixtures."""

import os
import uuid
from typing import Generator

import pytest
import psycopg2
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from local_newsifier.models.database import Base
from local_newsifier.config.database import DatabaseSettings


def get_test_db_name() -> str:
    """Get a unique test database name for this cursor instance.
    
    Returns:
        A unique test database name based on cursor ID or environment variable
    """
    # Use environment variable if set, otherwise generate a new one
    cursor_id = os.getenv("CURSOR_DB_ID")
    if not cursor_id:
        cursor_id = str(uuid.uuid4())[:8]
        os.environ["CURSOR_DB_ID"] = cursor_id
    return f"test_local_newsifier_{cursor_id}"


@pytest.fixture(scope="session")
def postgres_url():
    """Get PostgreSQL URL for tests."""
    settings = DatabaseSettings()
    test_db_name = get_test_db_name()
    return str(settings.DATABASE_URL).replace(settings.POSTGRES_DB, test_db_name)


@pytest.fixture(scope="session")
def test_engine(postgres_url):
    """Create a test database engine.
    
    This version is compatible with both local development and CI environments.
    """
    settings = DatabaseSettings()
    test_db_name = postgres_url.rsplit('/', 1)[1]
    
    # Connect to default postgres database to create test db
    try:
        # Connect to default postgres database to create test db
        admin_url = postgres_url.rsplit('/', 1)[0] + "/postgres"
        admin_engine = create_engine(admin_url)
        
        # Create test database
        with admin_engine.connect() as conn:
            conn.execute(text(f"DROP DATABASE IF EXISTS {test_db_name}"))
            conn.execute(text(f"CREATE DATABASE {test_db_name}"))
            conn.commit()
    except Exception as e:
        print(f"Error creating test database: {e}")
        # If we can't create the database, try connecting directly
        # (it might already exist in CI)
    
    # Create engine for the test database
    engine = create_engine(postgres_url)
    
    # Create all tables
    Base.metadata.create_all(engine)
    
    yield engine
    
    # Cleanup after all tests
    Base.metadata.drop_all(engine)
    engine.dispose()  # Close all connections
    
    try:
        # Connect to default postgres database to drop test db
        admin_url = postgres_url.rsplit('/', 1)[0] + "/postgres"
        admin_engine = create_engine(admin_url)
        
        # Drop test database
        with admin_engine.connect() as conn:
            conn.execute(text(f"""
                SELECT pg_terminate_backend(pg_stat_activity.pid)
                FROM pg_stat_activity
                WHERE pg_stat_activity.datname = '{test_db_name}'
                AND pid <> pg_backend_pid();
            """))
            conn.execute(text(f"DROP DATABASE IF EXISTS {test_db_name}"))
            conn.commit()
    except Exception as e:
        print(f"Error dropping test database: {e}")
        # In CI, we may not have permissions to drop databases


@pytest.fixture(autouse=True)
def setup_test_db(test_engine) -> Generator[None, None, None]:
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
def db_session(test_engine) -> Generator[Session, None, None]:
    """Create a test database session."""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close() 
"""Test configuration and fixtures."""

import os
import uuid
from typing import Generator
import time

import pytest
import psycopg2
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from local_newsifier.models.database import Base
from local_newsifier.config.database import DatabaseSettings


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
    Base.metadata.create_all(engine)
    
    yield engine
    
    # Cleanup after all tests
    Base.metadata.drop_all(engine)
    engine.dispose()  # Close all connections
    
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


@pytest.fixture(autouse=True)
def setup_test_db(test_engine) -> Generator[None, None, None]:
    """Set up and tear down the test database for each test."""
    # Drop all tables and recreate schema
    with test_engine.connect() as conn:
        # Drop all tables
        conn.execute(text("""
            DO $$ 
            DECLARE
                r RECORD;
            BEGIN
                FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public') LOOP
                    EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.tablename) || ' CASCADE';
                END LOOP;
            END $$;
        """))
        conn.commit()
    
    # Create all tables
    Base.metadata.create_all(test_engine)
    yield
    
    # Drop all tables after tests
    with test_engine.connect() as conn:
        conn.execute(text("""
            DO $$ 
            DECLARE
                r RECORD;
            BEGIN
                FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public') LOOP
                    EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.tablename) || ' CASCADE';
                END LOOP;
            END $$;
        """))
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
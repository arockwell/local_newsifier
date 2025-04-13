"""Test configuration and fixtures."""

import os
import uuid
from typing import Generator

import pytest
import psycopg2
from sqlalchemy import create_engine
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
def test_engine():
    """Create a test database engine."""
    settings = DatabaseSettings()
    test_db_name = get_test_db_name()
    
    # Connect to default postgres database to create test db
    conn = psycopg2.connect(
        host=settings.POSTGRES_HOST,
        port=int(settings.POSTGRES_PORT),
        user=settings.POSTGRES_USER,
        password=settings.POSTGRES_PASSWORD,
        database="postgres"
    )
    conn.autocommit = True
    
    try:
        with conn.cursor() as cur:
            # Drop test database if it exists
            cur.execute(f"DROP DATABASE IF EXISTS {test_db_name}")
            # Create new test database
            cur.execute(f"CREATE DATABASE {test_db_name}")
    finally:
        conn.close()
    
    # Create engine for the test database
    test_db_url = str(settings.DATABASE_URL).replace(settings.POSTGRES_DB, test_db_name)
    engine = create_engine(test_db_url)
    
    # Create all tables
    Base.metadata.create_all(engine)
    
    yield engine
    
    # Cleanup after all tests
    Base.metadata.drop_all(engine)
    conn = psycopg2.connect(
        host=settings.POSTGRES_HOST,
        port=int(settings.POSTGRES_PORT),
        user=settings.POSTGRES_USER,
        password=settings.POSTGRES_PASSWORD,
        database="postgres"
    )
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            cur.execute(f"DROP DATABASE IF EXISTS {test_db_name}")
    finally:
        conn.close()


@pytest.fixture
def db_session(test_engine) -> Generator[Session, None, None]:
    """Create a test database session."""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close() 
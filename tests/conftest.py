"""Global test fixtures."""

from typing import Generator

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from local_newsifier.config.database import get_database, get_db_session
from local_newsifier.models.database import Base


@pytest.fixture(autouse=True)
def mock_openai_api_key():
    """Mock the OpenAI API key for tests."""
    with pytest.MonkeyPatch() as mp:
        mp.setenv("OPENAI_API_KEY", "test-api-key")
        yield


@pytest.fixture(scope="session")
def test_engine():
    """Create a test database engine."""
    engine = get_database(".env.test")
    return engine


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
    session_factory = get_db_session(".env.test")
    session = session_factory()
    try:
        yield session
    finally:
        session.close() 
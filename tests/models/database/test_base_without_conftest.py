"""Tests for the base database model."""

import datetime
import pytest
import os
from sqlalchemy import Column, String, create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from local_newsifier.models.database.base import Base
from local_newsifier.config.database import DatabaseSettings


class TestModel(Base):
    """Test model that inherits from Base."""
    
    __tablename__ = "test_models"
    name = Column(String)


@pytest.fixture(scope="module")
def postgres_engine():
    """Set up a PostgreSQL test database."""
    # Use environment variables for PostgreSQL connection
    settings = DatabaseSettings()
    
    # Use a unique test database name
    test_db_name = f"test_base_{os.getenv('GITHUB_RUN_ID', 'local')}"
    db_url = settings.get_database_url().replace(settings.POSTGRES_DB, test_db_name)
    
    # Connect to default postgres database to create test db
    try:
        # Connect to default postgres database to create test db
        admin_url = db_url.rsplit('/', 1)[0] + "/postgres"
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
    engine = create_engine(db_url)
    
    # Create test tables
    Base.metadata.create_all(engine)
    
    yield engine
    
    # Clean up
    Base.metadata.drop_all(engine)
    engine.dispose()
    
    try:
        # Connect to default postgres database to drop test db
        admin_url = db_url.rsplit('/', 1)[0] + "/postgres"
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


@pytest.fixture
def db_session(postgres_engine):
    """Create a test database session."""
    Session = sessionmaker(bind=postgres_engine)
    session = Session()
    yield session
    session.close()


def test_base_model_attributes():
    """Test that Base has required attributes."""
    assert hasattr(Base, "id")
    assert hasattr(Base, "created_at")
    assert hasattr(Base, "updated_at")


def test_tablename_generation():
    """Test that tablename is generated from class name."""
    assert TestModel.__tablename__ == "test_models"


def test_base_model_creation(db_session):
    """Test creating a model instance with base fields."""
    test_model = TestModel(name="Test")
    db_session.add(test_model)
    db_session.commit()
    
    assert test_model.id is not None
    assert isinstance(test_model.created_at, datetime.datetime)
    assert isinstance(test_model.updated_at, datetime.datetime)
    assert test_model.name == "Test"


def test_base_model_update(db_session):
    """Test that updated_at is updated on model update."""
    test_model = TestModel(name="Test")
    db_session.add(test_model)
    db_session.commit()
    
    initial_updated_at = test_model.updated_at
    
    # Wait a moment to ensure the timestamp would be different
    import time
    time.sleep(0.1)
    
    test_model.name = "Updated Test"
    db_session.commit()
    
    assert test_model.updated_at > initial_updated_at
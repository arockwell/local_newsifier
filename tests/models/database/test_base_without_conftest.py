"""Tests for the base database model."""

import datetime
import pytest
from sqlalchemy import Column, String, create_engine
from sqlalchemy.orm import Session, sessionmaker

from local_newsifier.models.database.base import Base


class TestModel(Base):
    """Test model that inherits from Base."""
    
    __tablename__ = "test_models"
    name = Column(String)


@pytest.fixture(scope="module")
def sqlite_engine():
    """Set up a SQLite in-memory test database."""
    # Create engine for the test database
    engine = create_engine("sqlite:///:memory:")
    
    # Create test tables
    Base.metadata.create_all(engine)
    
    yield engine
    
    # Clean up
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def db_session(sqlite_engine):
    """Create a test database session."""
    Session = sessionmaker(bind=sqlite_engine)
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
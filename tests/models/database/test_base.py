"""Tests for the base database model."""

import datetime
import pytest
from sqlalchemy import Column, String, create_engine
from sqlalchemy.orm import Session, sessionmaker, Mapped, mapped_column

from local_newsifier.models.database.base import Base


class TestModelBase(Base):
    """Test model for testing the base model functionality."""
    __tablename__ = "test_models_base"
    name: Mapped[str] = mapped_column(String)


@pytest.fixture(scope="module")
def engine():
    """Create a SQLite in-memory engine for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture
def session(engine):
    """Create a session for testing."""
    Session = sessionmaker(bind=engine)
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
    assert TestModelBase.__tablename__ == "test_models_base"


def test_base_model_creation(session):
    """Test creating a model instance with base fields."""
    test_model = TestModelBase(name="Test")
    session.add(test_model)
    session.commit()
    
    assert test_model.id is not None
    assert isinstance(test_model.created_at, datetime.datetime)
    assert isinstance(test_model.updated_at, datetime.datetime)
    assert test_model.name == "Test"


def test_base_model_update(session):
    """Test that updated_at is updated on model update."""
    test_model = TestModelBase(name="Test")
    session.add(test_model)
    session.commit()
    
    initial_updated_at = test_model.updated_at
    
    # Wait a moment to ensure the timestamp would be different
    import time
    time.sleep(0.1)
    
    test_model.name = "Updated Test"
    session.commit()
    
    assert test_model.updated_at > initial_updated_at
"""Tests for the Base database model."""

import datetime
import pytest
from sqlalchemy import create_engine, Column, Integer
from sqlalchemy.orm import sessionmaker

from local_newsifier.models.database.base import Base


class TestModel(Base):
    """A test model for testing Base functionality."""

    __tablename__ = "test_model"
    id = Column(Integer, primary_key=True)


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
    TestSession = sessionmaker(bind=sqlite_engine)
    session = TestSession()
    yield session
    session.close()


def test_base_model_timestamps():
    """Test that Base model provides timestamp fields."""
    model = TestModel()
    assert hasattr(model, "created_at")
    assert hasattr(model, "updated_at")


def test_timestamps_are_datetime(db_session):
    """Test that timestamp fields are datetime type."""
    model = TestModel()
    db_session.add(model)
    db_session.commit()
    assert isinstance(model.created_at, datetime.datetime)
    assert isinstance(model.updated_at, datetime.datetime)

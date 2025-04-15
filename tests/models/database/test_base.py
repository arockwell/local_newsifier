"""Tests for the SQLModel TimestampMixin."""

import datetime
import pytest
from sqlmodel import Field, SQLModel, Session
from sqlalchemy.orm import sessionmaker

from local_newsifier.models.base import TimestampMixin


class TestModel(TimestampMixin, table=True):
    """A test model for testing TimestampMixin functionality."""

    __tablename__ = "test_model"
    id: int = Field(default=None, primary_key=True)


@pytest.fixture
def db_session(test_engine):
    """Create a test database session."""
    # Create tables if needed
    SQLModel.metadata.create_all(test_engine)
    
    # Create session using SQLModel's Session
    session = Session(test_engine)
    try:
        yield session
    finally:
        session.close()


def test_timestamps_are_datetime(db_session):
    """Test that created_at and updated_at are datetime objects."""
    model = TestModel()
    db_session.add(model)
    db_session.commit()
    
    assert isinstance(model.created_at, datetime.datetime)
    assert isinstance(model.updated_at, datetime.datetime)
    # Verify that timestamps are not null
    assert model.created_at is not None
    assert model.updated_at is not None

"""Tests for the Base database model."""

import datetime
import pytest
from sqlalchemy import Column, Integer
from sqlalchemy.orm import sessionmaker

from local_newsifier.models.database.base import Base


class TestModel(Base):
    """A test model for testing Base functionality."""

    __tablename__ = "test_model"
    id = Column(Integer, primary_key=True)


@pytest.fixture
def db_session(test_engine):
    """Create a test database session."""
    TestSession = sessionmaker(bind=test_engine)
    session = TestSession()
    yield session
    session.close()


def test_timestamps_are_datetime(db_session):
    """Test that timestamp fields are datetime type."""
    model = TestModel()
    db_session.add(model)
    db_session.commit()
    assert isinstance(model.created_at, datetime.datetime)
    assert isinstance(model.updated_at, datetime.datetime)

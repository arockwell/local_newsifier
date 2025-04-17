"""Tests for the Base database model."""

import datetime
import pytest
from sqlalchemy import Column, Integer
from sqlalchemy.orm import sessionmaker

from local_newsifier.models.database.base import TableBase
from typing import Optional


class TestModel(TableBase, table=True):
    """A test model for testing TableBase functionality."""

    __tablename__ = "test_model"


@pytest.fixture
def db_session(test_engine):
    """Create a test database session."""
    TestSession = sessionmaker(bind=test_engine)
    session = TestSession()
    yield session
    session.close()


def test_timestamps_are_datetime(db_session):
    """Test that created_at and updated_at are datetime objects."""
    model = TestModel()
    db_session.add(model)
    db_session.commit()
    
    assert isinstance(model.created_at, datetime.datetime)
    assert isinstance(model.updated_at, datetime.datetime)

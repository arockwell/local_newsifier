"""Tests for the Base database model."""

import datetime
from typing import Optional

import pytest
from sqlmodel import Field, Session, SQLModel

from local_newsifier.models.base import TableBase


# Note: This is intentionally defined inside a function to avoid polluting the global
# SQLModel metadata when tests are collected but not run
def get_test_model():
    """Return a test model class for testing TableBase functionality."""
    class TestModel(TableBase, table=True):
        """A test model for testing TableBase functionality."""

        __tablename__ = "test_model"
    
    return TestModel


def test_timestamps_are_datetime(db_session, test_engine):
    """Test that created_at and updated_at are datetime objects."""
    # Create TestModel class inside the test
    TestModel = get_test_model()
    
    # Create table specifically for this test
    SQLModel.metadata.create_all(test_engine, tables=[TestModel.__table__])
    
    # Create and test instance
    model = TestModel()
    db_session.add(model)
    db_session.commit()
    
    assert isinstance(model.created_at, datetime.datetime)
    assert isinstance(model.updated_at, datetime.datetime)

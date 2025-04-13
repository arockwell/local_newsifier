"""Tests for the base database model."""

import datetime
import unittest
from sqlalchemy import Column, String, create_engine
from sqlalchemy.orm import Session

from local_newsifier.models.database.base import BaseModel


class TestModel(BaseModel):
    """Test model that inherits from BaseModel."""
    
    __tablename__ = "test_models"
    name = Column(String)


class TestBaseModel(unittest.TestCase):
    """Test case for BaseModel."""
    
    def setUp(self):
        """Set up a test database."""
        self.engine = create_engine("sqlite:///:memory:")
        BaseModel.metadata.create_all(self.engine)
        self.session = Session(self.engine)
    
    def tearDown(self):
        """Tear down the test database."""
        self.session.close()
    
    def test_base_model_attributes(self):
        """Test that BaseModel has required attributes."""
        assert hasattr(BaseModel, "__tablename__")
        assert hasattr(BaseModel, "id")
        assert hasattr(BaseModel, "created_at")
        assert hasattr(BaseModel, "updated_at")
    
    def test_tablename_generation(self):
        """Test that tablename is generated from class name."""
        assert TestModel.__tablename__ == "test_models"
    
    def test_base_model_creation(self):
        """Test creating a model instance with base fields."""
        test_model = TestModel(name="Test")
        self.session.add(test_model)
        self.session.commit()
        
        assert test_model.id is not None
        assert isinstance(test_model.created_at, datetime.datetime)
        assert isinstance(test_model.updated_at, datetime.datetime)
        assert test_model.name == "Test"
    
    def test_base_model_update(self):
        """Test that updated_at is updated on model update."""
        test_model = TestModel(name="Test")
        self.session.add(test_model)
        self.session.commit()
        
        initial_updated_at = test_model.updated_at
        
        # Wait a moment to ensure the timestamp would be different
        import time
        time.sleep(0.1)
        
        test_model.name = "Updated Test"
        self.session.commit()
        
        assert test_model.updated_at > initial_updated_at
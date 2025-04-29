"""Database verification utilities for tests.

This module provides helpers for verifying database state in tests.
"""

from sqlmodel import Session, select
from typing import Type, List, Any, Dict, Optional, TypeVar, Generic
import pytest

# Type variable for database models
T = TypeVar('T')

class DatabaseVerifier:
    """Helper for verifying database state in tests."""
    
    def __init__(self, session: Session):
        """Initialize with a database session.
        
        Args:
            session: SQLModel session for database access
        """
        self.session = session
    
    def count(self, model_class) -> int:
        """Count the number of records for a given model.
        
        Args:
            model_class: SQLModel class
            
        Returns:
            int: Number of records
        """
        statement = select(model_class)
        results = self.session.exec(statement).all()
        return len(results)
    
    def assert_count(self, model_class, expected_count: int):
        """Assert that a model has the expected number of records.
        
        Args:
            model_class: SQLModel class
            expected_count: Expected number of records
        """
        actual_count = self.count(model_class)
        assert actual_count == expected_count, f"Expected {expected_count} records, found {actual_count}"
    
    def find(self, model_class, **filters):
        """Find records matching the given filters.
        
        Args:
            model_class: SQLModel class
            **filters: Attribute filters
            
        Returns:
            List of matching records
        """
        statement = select(model_class)
        
        for attr, value in filters.items():
            statement = statement.where(getattr(model_class, attr) == value)
        
        return self.session.exec(statement).all()
    
    def find_one(self, model_class, **filters):
        """Find a single record matching the given filters.
        
        Args:
            model_class: SQLModel class
            **filters: Attribute filters
            
        Returns:
            Matching record or None
        """
        results = self.find(model_class, **filters)
        return results[0] if results else None
    
    def assert_exists(self, model_class, **filters):
        """Assert that a record matching the filters exists.
        
        Args:
            model_class: SQLModel class
            **filters: Attribute filters
            
        Returns:
            Matching record
        """
        results = self.find(model_class, **filters)
        assert len(results) > 0, f"No {model_class.__name__} found matching {filters}"
        return results[0]
    
    def assert_not_exists(self, model_class, **filters):
        """Assert that no record matching the filters exists.
        
        Args:
            model_class: SQLModel class
            **filters: Attribute filters
        """
        results = self.find(model_class, **filters)
        assert len(results) == 0, f"Found {len(results)} {model_class.__name__} matching {filters}, expected none"
    
    def assert_field_value(self, record: Any, field_name: str, expected_value: Any):
        """Assert that a record's field has the expected value.
        
        Args:
            record: Database record
            field_name: Field to check
            expected_value: Expected field value
        """
        actual_value = getattr(record, field_name)
        assert actual_value == expected_value, f"Expected {field_name}={expected_value}, got {actual_value}"
    
    def assert_fields(self, record: Any, expected_fields: Dict[str, Any]):
        """Assert that a record's fields have the expected values.
        
        Args:
            record: Database record
            expected_fields: Dictionary mapping field names to expected values
        """
        for field_name, expected_value in expected_fields.items():
            self.assert_field_value(record, field_name, expected_value)
    
    def get_all(self, model_class):
        """Get all records for a model.
        
        Args:
            model_class: SQLModel class
            
        Returns:
            List of all records
        """
        statement = select(model_class)
        return self.session.exec(statement).all()
    
    def assert_record_count_changed(self, model_class, action, expected_change: int):
        """Assert that a record count changes by the expected amount after an action.
        
        Args:
            model_class: SQLModel class
            action: Callable that performs the action
            expected_change: Expected change in record count
        """
        initial_count = self.count(model_class)
        action()
        final_count = self.count(model_class)
        
        actual_change = final_count - initial_count
        assert actual_change == expected_change, f"Expected record count to change by {expected_change}, got {actual_change}"
    
    def find_related(self, record: Any, relationship_attr: str):
        """Find records related to a record through a relationship.
        
        Args:
            record: Database record
            relationship_attr: Relationship attribute name
            
        Returns:
            Related records
        """
        return getattr(record, relationship_attr)
    
    def assert_related_count(self, record: Any, relationship_attr: str, expected_count: int):
        """Assert that a record has the expected number of related records.
        
        Args:
            record: Database record
            relationship_attr: Relationship attribute name
            expected_count: Expected number of related records
        """
        related_records = self.find_related(record, relationship_attr)
        actual_count = len(related_records)
        assert actual_count == expected_count, f"Expected {expected_count} related records, found {actual_count}"

@pytest.fixture
def db_verifier(db_function_session):
    """Provide a DatabaseVerifier instance."""
    return DatabaseVerifier(db_function_session)

class ModelTester(Generic[T]):
    """Helper for testing database models with common operations.
    
    This class provides:
    1. Standard CRUD operations for testing models
    2. Verification of model behavior
    3. Helpers for testing relationships
    """
    
    def __init__(self, model_class: Type[T], session: Session):
        """Initialize with a model class and session.
        
        Args:
            model_class: SQLModel class to test
            session: SQLModel session
        """
        self.model_class = model_class
        self.session = session
        self.verifier = DatabaseVerifier(session)
    
    def create(self, **kwargs) -> T:
        """Create a new instance of the model.
        
        Args:
            **kwargs: Model field values
            
        Returns:
            New model instance
        """
        model = self.model_class(**kwargs)
        self.session.add(model)
        self.session.commit()
        self.session.refresh(model)
        return model
    
    def update(self, model_id: int, **kwargs) -> T:
        """Update an existing model instance.
        
        Args:
            model_id: ID of the model to update
            **kwargs: Fields to update
            
        Returns:
            Updated model instance
        """
        model = self.session.get(self.model_class, model_id)
        if not model:
            raise ValueError(f"No {self.model_class.__name__} found with id={model_id}")
        
        for field, value in kwargs.items():
            setattr(model, field, value)
        
        self.session.add(model)
        self.session.commit()
        self.session.refresh(model)
        return model
    
    def delete(self, model_id: int) -> bool:
        """Delete a model instance.
        
        Args:
            model_id: ID of the model to delete
            
        Returns:
            True if deleted, False if not found
        """
        model = self.session.get(self.model_class, model_id)
        if not model:
            return False
        
        self.session.delete(model)
        self.session.commit()
        return True
    
    def get(self, model_id: int) -> Optional[T]:
        """Get a model instance by ID.
        
        Args:
            model_id: ID of the model to get
            
        Returns:
            Model instance or None
        """
        return self.session.get(self.model_class, model_id)
    
    def find(self, **filters) -> List[T]:
        """Find model instances matching filters.
        
        Args:
            **filters: Field filters
            
        Returns:
            List of matching model instances
        """
        return self.verifier.find(self.model_class, **filters)
    
    def assert_crud_operations(self, create_data, update_data):
        """Test basic CRUD operations for the model.
        
        Args:
            create_data: Data for creating a record
            update_data: Data for updating the record
        """
        # Test create
        model = self.create(**create_data)
        assert model is not None, "Failed to create model instance"
        assert model.id is not None, "Created model has no ID"
        
        # Test get
        retrieved = self.get(model.id)
        assert retrieved is not None, f"Failed to get model with id={model.id}"
        
        # Test update
        updated = self.update(model.id, **update_data)
        assert updated is not None, "Failed to update model"
        
        # Verify update
        for field, value in update_data.items():
            assert getattr(updated, field) == value, f"Updated field {field} does not match"
        
        # Test delete
        deleted = self.delete(model.id)
        assert deleted, f"Failed to delete model with id={model.id}"
        
        # Verify delete
        assert self.get(model.id) is None, f"Model with id={model.id} still exists after delete"

@pytest.fixture
def model_tester():
    """Provide a ModelTester factory function."""
    def create_tester(model_class, session):
        return ModelTester(model_class, session)
    return create_tester

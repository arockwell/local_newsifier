"""Tests for the simplified ErrorHandledCRUD implementation."""

import pytest
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlmodel import Session, SQLModel, create_engine, Field
from unittest.mock import patch, MagicMock

from local_newsifier.crud.simple_error_handled_crud import (
    CRUDError,
    DatabaseConnectionError,
    DuplicateEntityError,
    EntityNotFoundError,
    ErrorHandledCRUD,
    ValidationError,
    handle_crud_error,
)


# Simple test model
class TestItem(SQLModel, table=True):
    """Test model for CRUD operations."""
    
    __tablename__ = "test_items"
    
    id: int = Field(default=None, primary_key=True)
    name: str = Field(unique=True)
    description: str = Field(default="")


@pytest.fixture
def in_memory_db():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    
    with Session(engine) as session:
        yield session


@pytest.fixture
def test_crud():
    """Create a test CRUD object."""
    return ErrorHandledCRUD(TestItem)


def test_get_nonexistent_item(in_memory_db, test_crud):
    """Test that getting a nonexistent item raises EntityNotFoundError."""
    with pytest.raises(EntityNotFoundError) as excinfo:
        test_crud.get(in_memory_db, 999)
    
    # Check error details
    assert "TestItem with id 999 not found" in str(excinfo.value)
    assert excinfo.value.error_type == "not_found"
    assert excinfo.value.context["id"] == 999
    assert excinfo.value.context["model"] == "TestItem"


def test_create_and_get_item(in_memory_db, test_crud):
    """Test creating and retrieving an item."""
    # Create an item
    item_data = {"name": "Test Item", "description": "Test Description"}
    created_item = test_crud.create(in_memory_db, obj_in=item_data)
    
    # Check that the item was created with the correct data
    assert created_item.name == "Test Item"
    assert created_item.description == "Test Description"
    assert created_item.id is not None
    
    # Retrieve the item and check that it matches
    retrieved_item = test_crud.get(in_memory_db, created_item.id)
    assert retrieved_item.id == created_item.id
    assert retrieved_item.name == created_item.name
    assert retrieved_item.description == created_item.description


def test_create_duplicate_item(in_memory_db, test_crud):
    """Test that creating a duplicate item raises DuplicateEntityError."""
    # Create an item
    item_data = {"name": "Unique Item", "description": "Test Description"}
    test_crud.create(in_memory_db, obj_in=item_data)
    
    # Create a duplicate item
    with patch.object(in_memory_db, "commit") as mock_commit:
        # Mock commit to raise IntegrityError
        mock_commit.side_effect = IntegrityError(
            "UNIQUE constraint failed: test_items.name", 
            params=None, 
            orig=None
        )
        
        with pytest.raises(DuplicateEntityError) as excinfo:
            test_crud.create(in_memory_db, obj_in=item_data)
    
    # Check error details
    assert "Entity with these attributes already exists" in str(excinfo.value)
    assert excinfo.value.error_type == "integrity"


def test_update_item(in_memory_db, test_crud):
    """Test updating an item."""
    # Create an item
    item_data = {"name": "Original Name", "description": "Original Description"}
    created_item = test_crud.create(in_memory_db, obj_in=item_data)
    
    # Update the item
    update_data = {"description": "Updated Description"}
    updated_item = test_crud.update(
        in_memory_db, db_obj=created_item, obj_in=update_data
    )
    
    # Check that the item was updated with the correct data
    assert updated_item.id == created_item.id
    assert updated_item.name == "Original Name"  # Not updated
    assert updated_item.description == "Updated Description"  # Updated
    
    # Retrieve the item and check that it matches
    retrieved_item = test_crud.get(in_memory_db, created_item.id)
    assert retrieved_item.id == updated_item.id
    assert retrieved_item.name == updated_item.name
    assert retrieved_item.description == updated_item.description


def test_remove_item(in_memory_db, test_crud):
    """Test removing an item."""
    # Create an item
    item_data = {"name": "Item to Remove", "description": "Test Description"}
    created_item = test_crud.create(in_memory_db, obj_in=item_data)
    
    # Remove the item
    removed_item = test_crud.remove(in_memory_db, id=created_item.id)
    assert removed_item.id == created_item.id
    
    # Try to retrieve the item and check that it's gone
    with pytest.raises(EntityNotFoundError):
        test_crud.get(in_memory_db, created_item.id)


def test_get_multi(in_memory_db, test_crud):
    """Test retrieving multiple items with pagination."""
    # Create some items
    for i in range(10):
        item_data = {"name": f"Item {i}", "description": f"Description {i}"}
        test_crud.create(in_memory_db, obj_in=item_data)
    
    # Retrieve items with pagination
    items = test_crud.get_multi(in_memory_db, skip=0, limit=5)
    assert len(items) == 5
    
    # Retrieve next page
    items = test_crud.get_multi(in_memory_db, skip=5, limit=5)
    assert len(items) == 5
    
    # Check that they're different items
    assert items[0].name != "Item 0"


def test_database_connection_error(test_crud):
    """Test that database connection errors are handled correctly."""
    # Create a mock session that raises OperationalError on exec
    mock_session = MagicMock()
    mock_session.exec.side_effect = OperationalError(
        "connection error", params=None, orig=None
    )
    
    # Try to retrieve an item
    with pytest.raises(DatabaseConnectionError) as excinfo:
        test_crud.get(mock_session, 1)
    
    # Check error details
    assert "Database connection error" in str(excinfo.value)
    assert excinfo.value.error_type == "connection"


def test_general_sqlalchemy_error(test_crud):
    """Test that general SQLAlchemy errors are handled correctly."""
    # Create a mock session that raises a general SQLAlchemy error
    mock_session = MagicMock()
    mock_session.exec.side_effect = Exception("General database error")
    
    # Try to retrieve an item
    with pytest.raises(CRUDError) as excinfo:
        test_crud.get(mock_session, 1)
    
    # Check error details
    assert "Unexpected error during database operation" in str(excinfo.value)
    assert excinfo.value.context["function"] == "get"
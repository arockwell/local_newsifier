"""
Example implementation of CRUD operations with error handling.

This file demonstrates how to apply error handling to database operations
using the streamlined error handling framework.
"""

from typing import Optional, List, Dict, Any, Union
from sqlmodel import Session, select

from local_newsifier.crud.base import CRUDBase, ModelType
from local_newsifier.errors import handle_database


class ErrorHandledCRUD(CRUDBase[ModelType]):
    """
    Example CRUD class with error handling.
    
    This class demonstrates how to apply the database error handling
    to CRUD operations without creating a complex inheritance hierarchy.
    """
    
    @handle_database
    def get(self, db: Session, id: int) -> Optional[ModelType]:
        """Get an item by id with error handling."""
        return super().get(db, id)
    
    @handle_database
    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        """Get multiple items with error handling."""
        return super().get_multi(db, skip=skip, limit=limit)
    
    @handle_database
    def create(
        self, db: Session, *, obj_in: Union[Dict[str, Any], ModelType]
    ) -> ModelType:
        """Create a new item with error handling."""
        return super().create(db, obj_in=obj_in)
    
    @handle_database
    def update(
        self,
        db: Session,
        *,
        db_obj: ModelType,
        obj_in: Union[Dict[str, Any], ModelType]
    ) -> ModelType:
        """Update an item with error handling."""
        return super().update(db, db_obj=db_obj, obj_in=obj_in)
    
    @handle_database
    def remove(self, db: Session, *, id: int) -> Optional[ModelType]:
        """Remove an item with error handling."""
        return super().remove(db, id=id)


def create_crud_model(model) -> ErrorHandledCRUD:
    """Create a CRUD instance with error handling for a model."""
    return ErrorHandledCRUD(model)


# Example usage:
"""
# In your code
from local_newsifier.models import User
from examples.crud_with_error_handling import create_crud_model

# Create a CRUD instance for users with error handling
user_crud = create_crud_model(User)

# Use error handling in your service
try:
    user = user_crud.get(db, id=123)
    # Process user...
except ServiceError as e:
    if e.error_type == "not_found":
        # Handle not found case
        print("User not found")
    elif e.error_type == "connection":
        # Handle connection error
        print("Database connection error")
    else:
        # Handle other errors
        print(f"Error: {e}")
"""
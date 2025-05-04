"""
Enhanced CRUD base class with integrated error handling.

This module extends the CRUDBase class with streamlined error handling.
"""

from typing import Any, Dict, List, Optional, Type, TypeVar, Union, Generic

from sqlmodel import SQLModel, Session, select

from local_newsifier.errors.database import handle_database
from .base import CRUDBase, ModelType


class ErrorHandledCRUDBase(CRUDBase[ModelType]):
    """
    Enhanced CRUD base class with integrated error handling.
    
    This class extends the standard CRUDBase with error handling decorators
    that convert database exceptions to ServiceError instances.
    """
    
    @handle_database()
    def get(self, db: Session, id: int) -> Optional[ModelType]:
        """Get an item by id with error handling.
        
        Args:
            db: Database session
            id: Item id
            
        Returns:
            The item if found, None otherwise
            
        Raises:
            ServiceError: If a database error occurs
        """
        return super().get(db, id)
    
    @handle_database()
    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        """Get multiple items with pagination and error handling.
        
        Args:
            db: Database session
            skip: Number of items to skip
            limit: Maximum number of items to return
            
        Returns:
            List of items
            
        Raises:
            ServiceError: If a database error occurs
        """
        return super().get_multi(db, skip=skip, limit=limit)
    
    @handle_database()
    def create(
        self, db: Session, *, obj_in: Union[Dict[str, Any], ModelType]
    ) -> ModelType:
        """Create a new item with error handling.
        
        Args:
            db: Database session
            obj_in: Item data as dict or model instance
            
        Returns:
            Created item
            
        Raises:
            ServiceError: If a database error occurs (e.g., integrity constraint violation)
        """
        return super().create(db, obj_in=obj_in)
    
    @handle_database()
    def update(
        self,
        db: Session,
        *,
        db_obj: ModelType,
        obj_in: Union[Dict[str, Any], ModelType]
    ) -> ModelType:
        """Update an item with error handling.
        
        Args:
            db: Database session
            db_obj: Database object to update
            obj_in: Update data as dict or model instance
            
        Returns:
            Updated item
            
        Raises:
            ServiceError: If a database error occurs
        """
        return super().update(db, db_obj=db_obj, obj_in=obj_in)
    
    @handle_database()
    def remove(self, db: Session, *, id: int) -> Optional[ModelType]:
        """Remove an item with error handling.
        
        Args:
            db: Database session
            id: Item id
            
        Returns:
            Removed item if found, None otherwise
            
        Raises:
            ServiceError: If a database error occurs (e.g., foreign key constraint)
        """
        return super().remove(db, id=id)


def create_error_handled_crud_model(model: Type[ModelType]) -> ErrorHandledCRUDBase:
    """
    Create an instance of ErrorHandledCRUDBase for the given model.
    
    Args:
        model: SQLModel model class
        
    Returns:
        An instance of ErrorHandledCRUDBase for the given model
    """
    return ErrorHandledCRUDBase(model)
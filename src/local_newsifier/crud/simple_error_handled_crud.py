"""Simplified error-handled CRUD operations for SQLModel.

This module provides a minimalistic base class for CRUD operations with standardized 
error handling, designed to work well with the fastapi-injectable pattern.
"""

import functools
import logging
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar, Union

from sqlalchemy.exc import (IntegrityError, NoResultFound, OperationalError,
                            SQLAlchemyError)
from sqlmodel import Session, SQLModel, select

from local_newsifier.crud.base import ModelType
from local_newsifier.errors.error import ServiceError

logger = logging.getLogger(__name__)


# Custom error classes
class CRUDError(ServiceError):
    """Base error for all CRUD operations."""
    
    def __init__(
        self, 
        message: str, 
        original: Optional[Exception] = None, 
        context: Optional[Dict[str, Any]] = None
    ):
        """Initialize a CRUDError.
        
        Args:
            message: Human-readable error message
            original: Original exception that was caught
            context: Additional context information
        """
        super().__init__(
            service="database",
            error_type=self._get_error_type(),
            message=message,
            original=original,
            context=context,
        )
    
    def _get_error_type(self) -> str:
        """Get the error type for this error class."""
        return "unknown"


class EntityNotFoundError(CRUDError):
    """Error raised when an entity is not found."""
    
    def _get_error_type(self) -> str:
        return "not_found"


class DuplicateEntityError(CRUDError):
    """Error raised when trying to create a duplicate entity."""
    
    def _get_error_type(self) -> str:
        return "integrity"


class ValidationError(CRUDError):
    """Error raised when entity validation fails."""
    
    def _get_error_type(self) -> str:
        return "validation"


class DatabaseConnectionError(CRUDError):
    """Error raised when there is a database connection issue."""
    
    def _get_error_type(self) -> str:
        return "connection"


def handle_crud_error(func: Callable) -> Callable:
    """Decorator for handling CRUD operation errors.
    
    Args:
        func: The function to decorate
        
    Returns:
        Decorated function with error handling
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        """Wrapped function with error handling."""
        try:
            return func(*args, **kwargs)
        except CRUDError:
            # Already handled, just re-raise
            raise
        except NoResultFound as e:
            # Get model name from self (first arg)
            crud_instance = args[0] if args else None
            model_name = getattr(getattr(crud_instance, "model", None), "__name__", "Entity")
            
            # Extract identifier from kwargs or args
            identifier = kwargs.get("id") or (args[1] if len(args) > 1 else None)
            
            # Create context with function info
            context = {
                "function": func.__name__,
                "model": model_name,
                "identifier": identifier,
            }
            
            # Build error message
            message = f"{model_name} not found"
            if identifier:
                message += f" (id: {identifier})"
                
            raise EntityNotFoundError(message, original=e, context=context)
        except IntegrityError as e:
            error_message = str(e).lower()
            context = {"function": func.__name__}
            
            if "unique" in error_message or "duplicate" in error_message:
                raise DuplicateEntityError(
                    "Entity with these attributes already exists",
                    original=e,
                    context=context,
                )
            else:
                raise ValidationError(
                    "Database constraint violation", 
                    original=e, 
                    context=context
                )
        except OperationalError as e:
            context = {"function": func.__name__}
            raise DatabaseConnectionError(
                "Database connection error", 
                original=e, 
                context=context
            )
        except SQLAlchemyError as e:
            # Generic SQLAlchemy error handling
            raise CRUDError(
                "Database error", 
                original=e, 
                context={"function": func.__name__}
            )
        except Exception as e:
            # Unexpected error
            raise CRUDError(
                "Unexpected error during database operation",
                original=e,
                context={"function": func.__name__},
            )
    
    return wrapper


class ErrorHandledCRUD:
    """Base class for CRUD operations with error handling.
    
    This is a simplified version of ErrorHandledCRUD that focuses on core functionality
    and is designed to work well with the fastapi-injectable pattern.
    """
    
    def __init__(self, model: Type[SQLModel]):
        """Initialize with model class.
        
        Args:
            model: SQLModel model class
        """
        self.model = model
    
    @handle_crud_error
    def get(self, db: Session, id: int) -> Optional[ModelType]:
        """Get an item by id with error handling.
        
        Args:
            db: Database session
            id: Item id
            
        Returns:
            The item if found
            
        Raises:
            EntityNotFoundError: If the entity with the given id does not exist
            DatabaseConnectionError: If there's a connection issue
            CRUDError: For other database errors
        """
        result = db.exec(select(self.model).where(self.model.id == id)).first()
        if result is None:
            raise EntityNotFoundError(
                f"{self.model.__name__} with id {id} not found",
                context={"id": id, "model": self.model.__name__},
            )
        return result
    
    @handle_crud_error
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
            DatabaseConnectionError: If there's a connection issue
            CRUDError: For other database errors
        """
        return db.exec(select(self.model).offset(skip).limit(limit)).all()
    
    @handle_crud_error
    def create(
        self, db: Session, *, obj_in: Union[Dict[str, Any], SQLModel]
    ) -> ModelType:
        """Create a new item with error handling.
        
        Args:
            db: Database session
            obj_in: Item data as dict or model instance
            
        Returns:
            Created item
            
        Raises:
            DuplicateEntityError: If an entity with the same unique fields already exists
            ValidationError: If the entity data fails validation
            DatabaseConnectionError: If there's a connection issue
            CRUDError: For other database errors
        """
        if isinstance(obj_in, dict):
            obj_data = obj_in
        else:
            # Use SQLModel's model_dump method
            obj_data = obj_in.model_dump()
            
        db_obj = self.model(**obj_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    @handle_crud_error
    def update(
        self,
        db: Session,
        *,
        db_obj: ModelType,
        obj_in: Union[Dict[str, Any], SQLModel],
    ) -> ModelType:
        """Update an item with error handling.
        
        Args:
            db: Database session
            db_obj: Database object to update
            obj_in: Update data as dict or model instance
            
        Returns:
            Updated item
            
        Raises:
            ValidationError: If the updated entity data fails validation
            DuplicateEntityError: If the update would create a duplicate entity
            DatabaseConnectionError: If there's a connection issue
            CRUDError: For other database errors
        """
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            # Use SQLModel's model_dump method
            update_data = obj_in.model_dump(exclude_unset=True)
            
        for field in update_data:
            if hasattr(db_obj, field):
                setattr(db_obj, field, update_data[field])
                
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    @handle_crud_error
    def remove(self, db: Session, *, id: int) -> Optional[ModelType]:
        """Remove an item with error handling.
        
        Args:
            db: Database session
            id: Item id
            
        Returns:
            Removed item if found
            
        Raises:
            EntityNotFoundError: If the entity with the given id does not exist
            DatabaseConnectionError: If there's a connection issue
            CRUDError: For other database errors
        """
        db_obj = db.exec(select(self.model).where(self.model.id == id)).first()
        if db_obj is None:
            raise EntityNotFoundError(
                f"{self.model.__name__} with id {id} not found",
                context={"id": id, "model": self.model.__name__},
            )
            
        db.delete(db_obj)
        db.commit()
        return db_obj
"""Error-handled CRUD operations for SQLModel.

This module provides a base class for CRUD operations with standardized error handling.
"""

import functools
import logging
from typing import Any, Callable, Dict, List, Optional, Union

from sqlalchemy.exc import (IntegrityError, NoResultFound, OperationalError,
                            SQLAlchemyError)
from sqlmodel import Session, SQLModel, select

from local_newsifier.crud.base import CRUDBase, ModelType
from local_newsifier.errors.error import ServiceError

logger = logging.getLogger(__name__)


# Custom database exception types
class CRUDError(ServiceError):
    """Base error for all CRUD operations."""

    def __init__(
        self,
        message: str,
        original: Optional[Exception] = None,
        context: Optional[Dict[str, Any]] = None,
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
        return "validation"


class ValidationError(CRUDError):
    """Error raised when entity validation fails."""

    def _get_error_type(self) -> str:
        return "validation"


class DatabaseConnectionError(CRUDError):
    """Error raised when there is a database connection issue."""

    def _get_error_type(self) -> str:
        return "network"


class TransactionError(CRUDError):
    """Error raised when a transaction fails."""

    def _get_error_type(self) -> str:
        return "server"


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
            # Already handled
            raise
        except NoResultFound as e:
            # Determine the model type from the first arg (self)
            crud_instance = args[0] if args else None
            model_name = (
                getattr(crud_instance, "model", None).__name__
                if hasattr(crud_instance, "model")
                else "Entity"
            )

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
                    "Database constraint violation", original=e, context=context
                )
        except OperationalError as e:
            error_message = str(e).lower()
            context = {"function": func.__name__}

            if any(
                word in error_message
                for word in ["connection", "timeout", "connection refused"]
            ):
                raise DatabaseConnectionError(
                    "Database connection error", original=e, context=context
                )
            else:
                raise TransactionError(
                    "Database operation error", original=e, context=context
                )
        except SQLAlchemyError as e:
            # Generic SQLAlchemy error handling
            raise TransactionError(
                "Database error", original=e, context={"function": func.__name__}
            )
        except Exception as e:
            # Unexpected error
            raise CRUDError(
                "Unexpected error during database operation",
                original=e,
                context={"function": func.__name__},
            )

    return wrapper


class ErrorHandledCRUD(CRUDBase[ModelType]):
    """Base class for CRUD operations with error handling.

    This class extends the standard CRUDBase with comprehensive error handling.
    It catches SQLAlchemy errors and translates them into appropriate domain exceptions.
    """

    @handle_crud_error
    def get(self, db: Session, id: int) -> Optional[ModelType]:
        """Get an item by id with error handling.

        Args:
            db: Database session
            id: Item id

        Returns:
            The item if found, None otherwise

        Raises:
            EntityNotFoundError: If the entity with the given id does not exist
            DatabaseConnectionError: If there's a connection issue
            TransactionError: If there's a database transaction error
        """
        result = super().get(db, id)
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
            TransactionError: If there's a database transaction error
        """
        return super().get_multi(db, skip=skip, limit=limit)

    @handle_crud_error
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
            DuplicateEntityError: If an entity with the same unique fields already exists
            ValidationError: If the entity data fails validation
            DatabaseConnectionError: If there's a connection issue
            TransactionError: If there's a database transaction error
        """
        return super().create(db, obj_in=obj_in)

    @handle_crud_error
    def update(
        self,
        db: Session,
        *,
        db_obj: ModelType,
        obj_in: Union[Dict[str, Any], ModelType],
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
            TransactionError: If there's a database transaction error
        """
        return super().update(db, db_obj=db_obj, obj_in=obj_in)

    @handle_crud_error
    def remove(self, db: Session, *, id: int) -> Optional[ModelType]:
        """Remove an item with error handling.

        Args:
            db: Database session
            id: Item id

        Returns:
            Removed item if found, None otherwise

        Raises:
            EntityNotFoundError: If the entity with the given id does not exist
            DatabaseConnectionError: If there's a connection issue
            TransactionError: If there's a database transaction error
        """
        result = super().remove(db, id=id)
        if result is None:
            raise EntityNotFoundError(
                f"{self.model.__name__} with id {id} not found",
                context={"id": id, "model": self.model.__name__},
            )
        return result

    @handle_crud_error
    def get_or_create(
        self,
        db: Session,
        *,
        obj_in: Union[Dict[str, Any], ModelType],
        unique_fields: List[str],
    ) -> ModelType:
        """Get an existing item or create a new one if it doesn't exist.

        Args:
            db: Database session
            obj_in: Item data as dict or model instance
            unique_fields: List of fields to check for uniqueness

        Returns:
            Existing or newly created item

        Raises:
            ValidationError: If the entity data fails validation
            DatabaseConnectionError: If there's a connection issue
            TransactionError: If there's a database transaction error
        """
        # Convert input to dict if it's a model instance
        if isinstance(obj_in, SQLModel):
            search_data = obj_in.model_dump(include=unique_fields)
        else:
            search_data = {
                field: obj_in.get(field) for field in unique_fields if field in obj_in
            }

        # Construct query with all unique fields
        query = select(self.model)
        for field, value in search_data.items():
            if hasattr(self.model, field) and value is not None:
                query = query.where(getattr(self.model, field) == value)

        # Try to find existing item
        result = db.exec(query).first()
        if result:
            return result

        # Create new item if not found
        return self.create(db, obj_in=obj_in)

    @handle_crud_error
    def find_by_attributes(
        self, db: Session, *, attributes: Dict[str, Any]
    ) -> List[ModelType]:
        """Find items by attribute values.

        Args:
            db: Database session
            attributes: Dictionary of attribute name/value pairs to match

        Returns:
            List of matching items

        Raises:
            DatabaseConnectionError: If there's a connection issue
            TransactionError: If there's a database transaction error
        """
        query = select(self.model)
        for attr, value in attributes.items():
            if hasattr(self.model, attr):
                query = query.where(getattr(self.model, attr) == value)

        return db.exec(query).all()

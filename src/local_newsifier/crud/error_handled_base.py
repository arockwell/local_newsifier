"""Error-handled CRUD operations for SQLModel."""

import functools
import logging
from typing import Any, Callable, Dict, List, Optional, Type, Union

from fastapi_injectable import injectable
from sqlalchemy.exc import IntegrityError, NoResultFound, OperationalError, SQLAlchemyError
from sqlmodel import Session, SQLModel, select

from local_newsifier.crud.base import CRUDBase, ModelType
from local_newsifier.errors.error import ServiceError

logger = logging.getLogger(__name__)


# Custom database exception types
class CRUDError(ServiceError):
    """Base error for all CRUD operations."""
    def __init__(self, message: str, original: Optional[Exception] = None, context: Optional[Dict[str, Any]] = None):
        super().__init__(
            service="database",
            error_type=self._get_error_type(),
            message=message,
            original=original,
            context=context,
        )

    def _get_error_type(self) -> str:
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
    """Decorator for handling CRUD operation errors."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except CRUDError:
            # Already handled
            raise
        except NoResultFound as e:
            # Determine the model type from the first arg (self)
            crud_instance = args[0] if args else None
            model_name = getattr(crud_instance, "model", None).__name__ if hasattr(crud_instance, "model") else "Entity"
            identifier = kwargs.get("id") or (args[1] if len(args) > 1 else None)
            context = {"function": func.__name__, "model": model_name, "identifier": identifier}
            message = f"{model_name} not found" + (f" (id: {identifier})" if identifier else "")
            raise EntityNotFoundError(message, original=e, context=context)
        except IntegrityError as e:
            error_message = str(e).lower()
            context = {"function": func.__name__}
            if "unique" in error_message or "duplicate" in error_message:
                raise DuplicateEntityError("Entity with these attributes already exists", original=e, context=context)
            else:
                raise ValidationError("Database constraint violation", original=e, context=context)
        except OperationalError as e:
            error_message = str(e).lower()
            context = {"function": func.__name__}
            connection_error = any(word in error_message for word in ["connection", "timeout", "connection refused"])
            if connection_error:
                raise DatabaseConnectionError("Database connection error", original=e, context=context)
            else:
                raise TransactionError("Database operation error", original=e, context=context)
        except SQLAlchemyError as e:
            # Generic SQLAlchemy error handling
            raise TransactionError("Database error", original=e, context={"function": func.__name__})
        except Exception as e:
            # Unexpected error
            raise CRUDError("Unexpected error during database operation", original=e, context={"function": func.__name__})
    return wrapper


class ErrorHandledCRUD(CRUDBase[ModelType]):
    """Base class for CRUD operations with error handling."""

    @handle_crud_error
    def get(self, db: Session, id: int) -> Optional[ModelType]:
        result = super().get(db, id)
        if result is None:
            raise EntityNotFoundError(
                f"{self.model.__name__} with id {id} not found",
                context={"id": id, "model": self.model.__name__},
            )
        return result

    @handle_crud_error
    def get_multi(self, db: Session, *, skip: int = 0, limit: int = 100) -> List[ModelType]:
        return super().get_multi(db, skip=skip, limit=limit)

    @handle_crud_error
    def create(self, db: Session, *, obj_in: Union[Dict[str, Any], ModelType]) -> ModelType:
        return super().create(db, obj_in=obj_in)

    @handle_crud_error
    def update(self, db: Session, *, db_obj: ModelType, obj_in: Union[Dict[str, Any], ModelType]) -> ModelType:
        return super().update(db, db_obj=db_obj, obj_in=obj_in)

    @handle_crud_error
    def remove(self, db: Session, *, id: int) -> Optional[ModelType]:
        result = super().remove(db, id=id)
        if result is None:
            raise EntityNotFoundError(
                f"{self.model.__name__} with id {id} not found",
                context={"id": id, "model": self.model.__name__},
            )
        return result

    @handle_crud_error
    def get_or_create(self, db: Session, *, obj_in: Union[Dict[str, Any], ModelType], unique_fields: List[str]) -> ModelType:
        # Convert input to dict if it's a model instance
        if isinstance(obj_in, SQLModel):
            search_data = obj_in.model_dump(include=unique_fields)
        else:
            search_data = {field: obj_in.get(field) for field in unique_fields if field in obj_in}

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
    def find_by_attributes(self, db: Session, *, attributes: Dict[str, Any]) -> List[ModelType]:
        query = select(self.model)
        for attr, value in attributes.items():
            if hasattr(self.model, attr):
                query = query.where(getattr(self.model, attr) == value)
        return db.exec(query).all()


# Cache of created CRUD objects to avoid recreating them
_crud_cache: Dict[str, ErrorHandledCRUD] = {}


@injectable(use_cache=True)
def get_error_handled_crud_factory():
    """Get a factory function for creating error-handled CRUD objects."""
    def create_crud_for_model(model_class: Type[SQLModel]) -> ErrorHandledCRUD:
        model_name = model_class.__name__
        if model_name in _crud_cache:
            return _crud_cache[model_name]
        crud = ErrorHandledCRUD(model_class)
        _crud_cache[model_name] = crud
        return crud
    return create_crud_for_model


@injectable(use_cache=True)
def get_article_crud(crud_factory=get_error_handled_crud_factory()):
    """Get an error-handled CRUD object for the Article model."""
    from local_newsifier.models.article import Article
    return crud_factory(Article)
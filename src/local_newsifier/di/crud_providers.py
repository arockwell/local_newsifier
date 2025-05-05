"""Provider functions for CRUD operations with error handling.

This module provides factory functions for creating error-handled CRUD objects
that can be used with fastapi-injectable.
"""

from typing import Dict, Type, TypeVar

from fastapi_injectable import injectable
from sqlmodel import SQLModel

from local_newsifier.crud.error_handled_base import ErrorHandledCRUD
from local_newsifier.models.article import Article

# Type for the model class
ModelType = TypeVar("ModelType", bound=SQLModel)

# Cache of created CRUD objects to avoid recreating them
# This is intentionally module-level to allow reuse across requests
_crud_cache: Dict[str, ErrorHandledCRUD] = {}


@injectable(use_cache=True)
def get_error_handled_crud_factory():
    """Get a factory function for creating error-handled CRUD objects."""
    def create_crud_for_model(model_class: Type[SQLModel]) -> ErrorHandledCRUD:
        """Create an error-handled CRUD object for a model class."""
        model_name = model_class.__name__
        
        # Check if we already have a CRUD object for this model
        if model_name in _crud_cache:
            return _crud_cache[model_name]
        
        # Create a new CRUD object
        crud = ErrorHandledCRUD(model_class)
        
        # Cache it for future use
        _crud_cache[model_name] = crud
        
        return crud
    
    return create_crud_for_model


@injectable(use_cache=True)
def get_article_crud(crud_factory=get_error_handled_crud_factory()):
    """Get an error-handled CRUD object for the Article model."""
    return crud_factory(Article)
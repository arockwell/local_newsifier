"""Standard exceptions for Local Newsifier."""

import logging
from functools import wraps
from typing import Optional, Type, Any, Callable, TypeVar, cast

from sqlalchemy.exc import SQLAlchemyError


logger = logging.getLogger(__name__)

F = TypeVar('F', bound=Callable[..., Any])


class LocalNewsifierError(Exception):
    """Base exception for all Local Newsifier errors."""

    def __init__(self, message: str, code: Optional[str] = None):
        self.message = message
        self.code = code
        super().__init__(self.message)


class DatabaseError(LocalNewsifierError):
    """Exception for database-related errors."""
    pass


class EntityNotFoundError(DatabaseError):
    """Exception raised when an entity is not found."""
    pass


class ValidationError(LocalNewsifierError):
    """Exception for data validation errors."""
    pass


class ConfigurationError(LocalNewsifierError):
    """Exception for configuration-related errors."""
    pass


class NetworkError(LocalNewsifierError):
    """Exception for network-related errors."""
    pass


class ScrapingError(NetworkError):
    """Exception for web scraping errors."""
    pass


class ProcessingError(LocalNewsifierError):
    """Exception for data processing errors."""
    pass


def handle_db_error(func: F) -> F:
    """Decorator to handle database errors consistently.
    
    This decorator wraps database operations and converts SQLAlchemy exceptions
    to our custom DatabaseError type with appropriate logging.
    
    Args:
        func: The function to decorate
        
    Returns:
        Decorated function that handles database errors
        
    Example:
        @handle_db_error
        def get_entity(session, entity_id):
            return session.query(Entity).filter_by(id=entity_id).first()
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except SQLAlchemyError as e:
            # Log the error with function name for context
            logger.error(f"Database error in {func.__name__}: {str(e)}")
            raise DatabaseError(f"Database operation failed: {str(e)}", code="DB_ERROR")
        except Exception as e:
            # Log unexpected errors but don't convert them
            logger.error(f"Unexpected error in {func.__name__}: {str(e)}")
            raise
    return cast(F, wrapper)


def entity_not_found_check(entity: Any, entity_type: str, entity_id: Any) -> None:
    """Check if an entity exists and raise EntityNotFoundError if not.
    
    Args:
        entity: The entity to check, can be None
        entity_type: String description of the entity type (e.g., "Article", "Entity")
        entity_id: Identifier used to find the entity
        
    Raises:
        EntityNotFoundError: If entity is None
        
    Example:
        article = session.query(Article).filter_by(id=article_id).first()
        entity_not_found_check(article, "Article", article_id)
    """
    if entity is None:
        raise EntityNotFoundError(
            f"{entity_type} with ID {entity_id} not found", 
            code=f"{entity_type.upper()}_NOT_FOUND"
        )

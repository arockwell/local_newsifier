"""
Database-specific error handling.

This module provides error handling for database operations using the 
streamlined error handling framework.
"""

import functools
import logging
from typing import Callable, Dict, Any, Optional, Type, Union

from sqlalchemy.exc import (
    SQLAlchemyError,
    IntegrityError,
    DataError,
    DatabaseError,
    DisconnectionError,
    TimeoutError,
    InvalidRequestError,
    OperationalError,
    ProgrammingError,
)
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

from .error import ServiceError, handle_service_error, with_retry, with_timing

logger = logging.getLogger(__name__)

# Database-specific error messages with troubleshooting hints
DB_ERROR_MESSAGES = {
    "connection": "Could not connect to the database. Check database connection settings.",
    "timeout": "Database operation timed out. The database may be overloaded.",
    "integrity": "Database constraint violation. The operation violates database rules.",
    "not_found": "Requested record not found in the database.",
    "multiple": "Multiple records found where only one was expected.",
    "validation": "Invalid database request. Check input parameters.",
    "transaction": "Transaction error. The operation could not be completed.",
    "unknown": "Unknown database error occurred."
}

def classify_database_error(error: Exception) -> tuple:
    """Classify a database exception into an appropriate error type.
    
    Args:
        error: The database exception to classify
        
    Returns:
        Tuple of (error_type, error_message)
    """
    # Handle SQLAlchemy exceptions
    if isinstance(error, IntegrityError):
        # Check for unique constraint violation
        if "unique constraint" in str(error).lower() or "unique violation" in str(error).lower():
            return "integrity", f"Unique constraint violation: {error}"
        # Check for foreign key constraint
        elif "foreign key constraint" in str(error).lower():
            return "integrity", f"Foreign key constraint violation: {error}"
        # Other integrity errors
        return "integrity", f"Database integrity error: {error}"
    
    elif isinstance(error, DataError):
        return "validation", f"Invalid data format: {error}"
    
    elif isinstance(error, DisconnectionError) or isinstance(error, OperationalError):
        if "connection" in str(error).lower():
            return "connection", f"Database connection error: {error}"
        return "operational", f"Database operational error: {error}"
    
    elif isinstance(error, TimeoutError):
        return "timeout", f"Database operation timed out: {error}"
    
    elif isinstance(error, NoResultFound):
        return "not_found", "Record not found in the database"
    
    elif isinstance(error, MultipleResultsFound):
        return "multiple", "Multiple records found where only one was expected"
    
    elif isinstance(error, InvalidRequestError):
        return "validation", f"Invalid database request: {error}"
    
    elif isinstance(error, ProgrammingError):
        return "validation", f"SQL programming error: {error}"
    
    elif isinstance(error, DatabaseError):
        return "database", f"Database error: {error}"
    
    # Generic SQLAlchemy error
    elif isinstance(error, SQLAlchemyError):
        return "unknown", f"Database error: {error}"
    
    # Default for any other exceptions
    return "unknown", f"Unexpected error during database operation: {error}"


def handle_database_error(func: Callable) -> Callable:
    """Decorator for handling database errors.
    
    This decorator catches database-specific exceptions and converts them
    to ServiceError instances with appropriate error types and context.
    
    Args:
        func: Function to decorate
        
    Returns:
        Decorated function with database error handling
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        """Wrapped function with database error handling."""
        try:
            return func(*args, **kwargs)
        except ServiceError:
            # Already handled
            raise
        except Exception as e:
            # Create context with function info
            context = {
                "function": func.__name__,
                # Safely extract args/kwargs (truncated)
                "args": [str(arg)[:100] for arg in args[:3] if not isinstance(arg, (dict, list))],
                "kwargs": {k: str(v)[:100] for k, v in list(kwargs.items())[:3] 
                           if not isinstance(v, (dict, list))}
            }
            
            # Classify database error
            error_type, error_message = classify_database_error(e)
            
            # Convert to ServiceError
            raise ServiceError(
                service="database",
                error_type=error_type,
                message=error_message,
                original=e,
                context=context
            )
    
    return wrapper


def handle_database(
    retry_attempts: Optional[int] = 3,
    include_timing: bool = True
) -> Callable:
    """Create a combined handler for database operations.
    
    This decorator combines error handling, retry logic, and timing
    for database operations.
    
    Args:
        retry_attempts: Number of retry attempts (None to disable)
        include_timing: Whether to include timing
        
    Returns:
        A decorator that combines error handling, retry, and timing
    """
    def decorator(func: Callable) -> Callable:
        """Combined decorator for database handling."""
        # Start with the original function
        result = func
        
        # Add error handling (innermost decorator)
        result = handle_database_error(result)
        
        # Add retry if requested
        if retry_attempts:
            result = with_retry(retry_attempts)(result)
        
        # Add timing if requested (outermost decorator)
        if include_timing:
            result = with_timing("database")(result)
        
        # Use proper wrapper to maintain function metadata
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return result(*args, **kwargs)
        
        return wrapper
    
    return decorator


# CLI error handler for database commands
def handle_database_cli(func: Callable) -> Callable:
    """Create a decorator for CLI database error handling.
    
    This decorator combines handle_database with CLI-specific error handling.
    
    Args:
        func: Function to decorate
        
    Returns:
        Decorated function with database error handling for CLI
    """
    # Import here to avoid circular imports
    from .cli import handle_cli_errors
    
    # First handle database errors, then handle CLI presentation
    decorated = handle_database()(func)
    return handle_cli_errors("database")(decorated)


def get_database_error_hint(error_type: str) -> str:
    """Get database-specific error message with troubleshooting hints.
    
    Args:
        error_type: Error type
        
    Returns:
        Error message with troubleshooting hints
    """
    return DB_ERROR_MESSAGES.get(error_type, DB_ERROR_MESSAGES["unknown"])
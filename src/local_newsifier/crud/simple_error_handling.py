"""Simple error handling utilities for CRUD operations.

This module provides simplified utilities for handling CRUD errors and converting
them to API responses. It's designed to be used with FastAPI endpoints and the
simplified ErrorHandledCRUD implementation.
"""

import asyncio
import functools
from typing import Any, Callable, Dict, Optional, Type, TypeVar

from fastapi import HTTPException, status
from pydantic import BaseModel

from local_newsifier.crud.simple_error_handled_crud import (CRUDError,
                                                         DatabaseConnectionError,
                                                         DuplicateEntityError,
                                                         EntityNotFoundError,
                                                         ValidationError)

# Map CRUD error types to HTTP status codes
HTTP_STATUS_CODES = {
    EntityNotFoundError: status.HTTP_404_NOT_FOUND,
    DuplicateEntityError: status.HTTP_409_CONFLICT,
    ValidationError: status.HTTP_422_UNPROCESSABLE_ENTITY,
    DatabaseConnectionError: status.HTTP_503_SERVICE_UNAVAILABLE,
    CRUDError: status.HTTP_500_INTERNAL_SERVER_ERROR,
}


class ErrorResponse(BaseModel):
    """Standardized error response model."""
    
    detail: str
    error_type: str
    error_context: Optional[Dict[str, Any]] = None


def crud_error_to_http_exception(error: CRUDError) -> HTTPException:
    """Convert a CRUD error to a FastAPI HTTPException.
    
    Args:
        error: The CRUD error to convert
        
    Returns:
        HTTPException with appropriate status code and details
    """
    # Get the most specific error type
    for error_type, status_code in HTTP_STATUS_CODES.items():
        if isinstance(error, error_type):
            # Create the error response
            response = ErrorResponse(
                detail=str(error),
                error_type=error.full_type,
                error_context=error.context
            )
            
            # Create and return the HTTPException
            return HTTPException(status_code=status_code, detail=response.model_dump())
    
    # Fallback for unknown error types
    response = ErrorResponse(
        detail=str(error),
        error_type="database.unknown",
        error_context=getattr(error, "context", {})
    )
    return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=response.model_dump())


# Function to check if a function is a coroutine
def is_coroutine_function(func: Any) -> bool:
    """Check if a function is a coroutine function.
    
    Args:
        func: The function to check
        
    Returns:
        True if the function is a coroutine function, False otherwise
    """
    try:
        return asyncio.iscoroutinefunction(func)
    except (ImportError, AttributeError):
        return False


F = TypeVar('F', bound=Callable)


def handle_crud_errors(func: F) -> F:
    """Decorator to handle CRUD errors in API endpoints.
    
    This decorator catches CRUD errors and converts them to appropriate
    HTTP exceptions with standardized response formats. It supports both
    synchronous and asynchronous functions.
    
    Args:
        func: The endpoint function to decorate
        
    Returns:
        Decorated function with CRUD error handling
    """
    if is_coroutine_function(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            """Wrapped async function with error handling."""
            try:
                return await func(*args, **kwargs)
            except CRUDError as e:
                # Convert CRUD error to HTTP exception
                raise crud_error_to_http_exception(e)
        return async_wrapper  # type: ignore
    else:
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            """Wrapped sync function with error handling."""
            try:
                return func(*args, **kwargs)
            except CRUDError as e:
                # Convert CRUD error to HTTP exception
                raise crud_error_to_http_exception(e)
        return sync_wrapper  # type: ignore
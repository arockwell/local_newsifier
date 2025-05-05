"""Error handling utilities for CRUD operations.

This module provides utilities for handling CRUD errors and converting them to API responses.
"""

from typing import Any, Dict, Optional

from fastapi import HTTPException, status
from pydantic import BaseModel

from local_newsifier.crud.error_handled_base import (CRUDError,
                                                     DatabaseConnectionError,
                                                     DuplicateEntityError,
                                                     EntityNotFoundError,
                                                     TransactionError,
                                                     ValidationError)

# Map CRUD error types to HTTP status codes
HTTP_STATUS_CODES = {
    EntityNotFoundError: status.HTTP_404_NOT_FOUND,
    DuplicateEntityError: status.HTTP_409_CONFLICT,
    ValidationError: status.HTTP_422_UNPROCESSABLE_ENTITY,
    DatabaseConnectionError: status.HTTP_503_SERVICE_UNAVAILABLE,
    TransactionError: status.HTTP_500_INTERNAL_SERVER_ERROR,
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
    # Get the HTTP status code based on error type
    error_type = type(error)
    status_code = HTTP_STATUS_CODES.get(
        error_type, status.HTTP_500_INTERNAL_SERVER_ERROR
    )

    # Create the error response
    response = ErrorResponse(
        detail=str(error), error_type=error.full_type, error_context=error.context
    )

    # Create and return the HTTPException
    return HTTPException(status_code=status_code, detail=response.model_dump())


def handle_crud_errors(func: Any) -> Any:
    """Decorator to handle CRUD errors in API endpoints.

    This decorator catches CRUD errors and converts them to appropriate
    HTTP exceptions with standardized response formats.

    Args:
        func: The endpoint function to decorate

    Returns:
        Decorated function with CRUD error handling
    """

    async def wrapper(*args, **kwargs):
        """Wrapped function with error handling."""
        try:
            return await func(*args, **kwargs)
        except CRUDError as e:
            # Convert CRUD error to HTTP exception
            raise crud_error_to_http_exception(e)

    # Handle both async and sync functions
    if asyncio_iscoroutinefunction(func):
        return wrapper

    def sync_wrapper(*args, **kwargs):
        """Sync version of the wrapper."""
        try:
            return func(*args, **kwargs)
        except CRUDError as e:
            # Convert CRUD error to HTTP exception
            raise crud_error_to_http_exception(e)

    return sync_wrapper


# Helper function to check if a function is a coroutine
try:
    # Import asyncio only if needed to avoid dependency issues
    import asyncio

    asyncio_iscoroutinefunction = asyncio.iscoroutinefunction
except (ImportError, AttributeError):
    # Fallback if asyncio is not available
    def asyncio_iscoroutinefunction(func: Any) -> bool:
        """Check if a function is a coroutine function."""
        return False

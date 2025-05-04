"""Error types for Apify integration.

This module defines custom error types for handling Apify-related
errors in a consistent way that preserves context and provides
clear error messages.
"""

import logging
import traceback
from typing import Any, Dict, Optional, Union

from apify_client.errors import ApifyApiError
import requests.exceptions

logger = logging.getLogger(__name__)

# Error code mapping to specific error types
ERROR_CODE_MAPPING = {
    401: "AUTH_ERROR",        # Unauthorized
    403: "AUTH_ERROR",        # Forbidden
    429: "RATE_LIMIT_ERROR",  # Too Many Requests
    404: "NOT_FOUND_ERROR",   # Not Found
    400: "VALIDATION_ERROR",  # Bad Request
    500: "SERVER_ERROR",      # Internal Server Error
    503: "SERVER_ERROR",      # Service Unavailable
}


class ApifyError(Exception):
    """Base class for all Apify-related errors.
    
    Provides common functionality for error context preservation,
    user-friendly messages, and error code mapping.
    """
    
    def __init__(
        self,
        message: str,
        original_error: Optional[Exception] = None,
        operation: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        status_code: Optional[int] = None,
    ):
        """Initialize the error with context information.
        
        Args:
            message: Human-readable error message
            original_error: The original exception that caused this error
            operation: The operation being performed when the error occurred
            context: Additional context about the error (e.g., parameters)
            status_code: HTTP status code (if applicable)
        """
        self.original_error = original_error
        self.operation = operation or "apify_operation"
        self.context = context or {}
        self.status_code = status_code
        self.error_code = self._determine_error_code()
        
        # Build the error message with context if available
        error_message = message
        if operation:
            error_message = f"{operation}: {error_message}"
        
        super().__init__(error_message)
        
        # Log the error with context
        self._log_error()
    
    def _determine_error_code(self) -> str:
        """Determine the error code based on status code or original error.
        
        Returns:
            Error code string
        """
        if self.status_code and self.status_code in ERROR_CODE_MAPPING:
            return ERROR_CODE_MAPPING[self.status_code]
        
        if isinstance(self.original_error, ApifyApiError):
            if hasattr(self.original_error, "status_code"):
                code = getattr(self.original_error, "status_code")
                if code in ERROR_CODE_MAPPING:
                    return ERROR_CODE_MAPPING[code]
        
        # Default general error code
        return "APIFY_ERROR"
    
    def _log_error(self) -> None:
        """Log the error with all available context."""
        log_message = f"Apify Error ({self.error_code}): {str(self)}"
        
        # Include context in the log
        if self.context:
            context_str = ", ".join(f"{k}={v}" for k, v in self.context.items())
            log_message += f" | Context: {context_str}"
        
        # Include original error details if available
        if self.original_error:
            log_message += f" | Original error: {type(self.original_error).__name__}: {str(self.original_error)}"
        
        # Get traceback for debugging
        tb = "".join(traceback.format_exception(
            type(self.original_error),
            self.original_error,
            self.original_error.__traceback__
        )) if self.original_error else ""
        
        # Log at error level
        logger.error(log_message)
        if tb:
            logger.debug(f"Traceback: {tb}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the error to a dictionary representation.
        
        Returns:
            Dictionary with error details
        """
        return {
            "error_code": self.error_code,
            "message": str(self),
            "operation": self.operation,
            "status_code": self.status_code,
            "context": self.context
        }


class ApifyAuthError(ApifyError):
    """Error raised for authentication and authorization issues.
    
    This includes invalid tokens, expired tokens, and insufficient permissions.
    """
    
    def __init__(
        self,
        message: str = "Authentication or authorization error",
        original_error: Optional[Exception] = None,
        operation: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        """Initialize with auth-specific defaults."""
        super().__init__(
            message=message,
            original_error=original_error,
            operation=operation,
            context=context,
            status_code=401  # Default to 401 Unauthorized
        )


class ApifyRateLimitError(ApifyError):
    """Error raised when Apify API rate limits are exceeded.
    
    Includes retry-after information when available.
    """
    
    def __init__(
        self,
        message: str = "API rate limit exceeded",
        original_error: Optional[Exception] = None,
        operation: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        retry_after: Optional[int] = None,
    ):
        """Initialize with rate limit specific information.
        
        Args:
            retry_after: Seconds to wait before retrying (if available)
        """
        self.retry_after = retry_after
        
        context = context or {}
        if retry_after:
            context["retry_after"] = retry_after
            message = f"{message} (retry after {retry_after}s)"
        
        super().__init__(
            message=message,
            original_error=original_error,
            operation=operation,
            context=context,
            status_code=429  # 429 Too Many Requests
        )


class ApifyNetworkError(ApifyError):
    """Error raised for network connectivity issues.
    
    This includes connection timeouts, DNS failures, and similar problems.
    """
    
    def __init__(
        self,
        message: str = "Network error connecting to Apify API",
        original_error: Optional[Exception] = None,
        operation: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        """Initialize with network error defaults."""
        super().__init__(
            message=message,
            original_error=original_error,
            operation=operation,
            context=context
        )


class ApifyAPIError(ApifyError):
    """Error raised for general API errors.
    
    Base class for specific API endpoint errors.
    """
    
    def __init__(
        self,
        message: str = "Apify API error",
        original_error: Optional[Exception] = None,
        operation: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        status_code: Optional[int] = None,
    ):
        """Initialize with API error defaults."""
        super().__init__(
            message=message,
            original_error=original_error,
            operation=operation,
            context=context,
            status_code=status_code
        )


class ApifyActorError(ApifyAPIError):
    """Error raised for actor-specific operations.
    
    This includes errors when running actors or accessing actor information.
    """
    
    def __init__(
        self,
        message: str = "Error with Apify actor operation",
        original_error: Optional[Exception] = None,
        operation: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        status_code: Optional[int] = None,
        actor_id: Optional[str] = None,
    ):
        """Initialize with actor-specific information.
        
        Args:
            actor_id: ID of the actor being accessed
        """
        context = context or {}
        if actor_id:
            context["actor_id"] = actor_id
        
        super().__init__(
            message=message,
            original_error=original_error,
            operation=operation,
            context=context,
            status_code=status_code
        )


class ApifyDatasetError(ApifyAPIError):
    """Error raised for dataset-specific operations.
    
    This includes errors when accessing or processing datasets.
    """
    
    def __init__(
        self,
        message: str = "Error with Apify dataset operation",
        original_error: Optional[Exception] = None,
        operation: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        status_code: Optional[int] = None,
        dataset_id: Optional[str] = None,
    ):
        """Initialize with dataset-specific information.
        
        Args:
            dataset_id: ID of the dataset being accessed
        """
        context = context or {}
        if dataset_id:
            context["dataset_id"] = dataset_id
        
        super().__init__(
            message=message,
            original_error=original_error,
            operation=operation,
            context=context,
            status_code=status_code
        )


class ApifyDataProcessingError(ApifyError):
    """Error raised for data processing and transformation issues.
    
    This includes errors parsing API responses or transforming data.
    """
    
    def __init__(
        self,
        message: str = "Error processing Apify data",
        original_error: Optional[Exception] = None,
        operation: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        """Initialize with data processing defaults."""
        super().__init__(
            message=message,
            original_error=original_error,
            operation=operation,
            context=context
        )


def parse_apify_error(error: Exception, operation: str, context: Dict[str, Any]) -> ApifyError:
    """Parse the original exception into an appropriate ApifyError subclass.
    
    Args:
        error: The original exception
        operation: The operation being performed
        context: Additional context about the error
        
    Returns:
        An appropriate ApifyError subclass
    """
    # Check for connection/network errors
    if isinstance(error, (requests.exceptions.ConnectionError,
                         requests.exceptions.Timeout,
                         requests.exceptions.RequestException)):
        return ApifyNetworkError(
            message=f"Network error: {str(error)}",
            original_error=error,
            operation=operation,
            context=context
        )
    
    # Check for Apify API errors
    if isinstance(error, ApifyApiError):
        # Extract status code if available
        status_code = None
        if hasattr(error, "status_code"):
            status_code = getattr(error, "status_code")
        
        # Check for specific error types based on status code
        if status_code in (401, 403):
            return ApifyAuthError(
                message=f"Authentication failed: {str(error)}",
                original_error=error,
                operation=operation,
                context=context
            )
        
        if status_code == 429:
            # Extract retry-after if available
            retry_after = None
            if hasattr(error, "response") and hasattr(error.response, "headers"):
                retry_after = error.response.headers.get("retry-after")
                if retry_after:
                    try:
                        retry_after = int(retry_after)
                    except (ValueError, TypeError):
                        retry_after = None
            
            return ApifyRateLimitError(
                message=f"Rate limit exceeded: {str(error)}",
                original_error=error,
                operation=operation,
                context=context,
                retry_after=retry_after
            )
        
        # Actor-specific or dataset-specific errors based on context
        if "actor_id" in context:
            return ApifyActorError(
                message=f"Actor error: {str(error)}",
                original_error=error,
                operation=operation,
                context=context,
                status_code=status_code,
                actor_id=context["actor_id"]
            )
        
        if "dataset_id" in context:
            return ApifyDatasetError(
                message=f"Dataset error: {str(error)}",
                original_error=error,
                operation=operation,
                context=context,
                status_code=status_code,
                dataset_id=context["dataset_id"]
            )
        
        # General API error
        return ApifyAPIError(
            message=f"API error: {str(error)}",
            original_error=error,
            operation=operation,
            context=context,
            status_code=status_code
        )
    
    # Data processing errors (like JSON parsing)
    if isinstance(error, (ValueError, TypeError)) and "parse" in str(error).lower():
        return ApifyDataProcessingError(
            message=f"Data processing error: {str(error)}",
            original_error=error,
            operation=operation,
            context=context
        )
    
    # Default to base ApifyError for unhandled error types
    return ApifyError(
        message=f"Unexpected error: {str(error)}",
        original_error=error,
        operation=operation,
        context=context
    )
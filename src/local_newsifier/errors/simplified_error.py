"""
Simplified error handling components.

This module defines the ServiceError class and core decorators with reduced line count.
"""

import functools
import logging
import time
from datetime import datetime
from typing import Any, Callable, Dict, Optional, Tuple

# Common error types with their properties
ERROR_TYPES = {
    "network": {"transient": True, "retry": True, "exit_code": 2},
    "timeout": {"transient": True, "retry": True, "exit_code": 3},
    "rate_limit": {"transient": True, "retry": True, "exit_code": 4},
    "auth": {"transient": False, "retry": False, "exit_code": 5},
    "parse": {"transient": False, "retry": False, "exit_code": 6},
    "validation": {"transient": False, "retry": False, "exit_code": 7},
    "not_found": {"transient": False, "retry": False, "exit_code": 8},
    "server": {"transient": True, "retry": True, "exit_code": 9},
    "connection": {"transient": True, "retry": True, "exit_code": 10},
    "integrity": {"transient": False, "retry": False, "exit_code": 11},
    "multiple": {"transient": False, "retry": False, "exit_code": 12},
    "transaction": {"transient": True, "retry": True, "exit_code": 13},
    "unknown": {"transient": False, "retry": False, "exit_code": 1}
}

# Error classification mappings
HTTP_STATUS_ERRORS = {
    401: "auth", 403: "auth", 404: "not_found", 429: "rate_limit",
    500: "server", 502: "server", 503: "server", 504: "server"
}

# Database error classification mappings
DB_ERROR_MAPPINGS = {
    "NoResultFound": ("not_found", "Record not found"),
    "MultipleResultsFound": ("multiple", "Multiple records found"),
    "DisconnectionError": ("connection", "Connection error"),
    "DBAPIError": ("connection", "Operational error"),
    "TimeoutError": ("timeout", "Query timeout"),
    "DataError": ("validation", "Data validation error"),
    "StatementError": ("validation", "Statement error"),
    "TransactionError": ("transaction", "Transaction error"),
    "InvalidRequestError": ("transaction", "Invalid request"),
    "IntegrityError": ("integrity", "Integrity error"),
    "OperationalError": ("connection", "Connection error")
}

logger = logging.getLogger(__name__)


class ServiceError(Exception):
    """Unified error type for all service errors."""
    
    def __init__(
        self, 
        service: str,
        error_type: str, 
        message: str, 
        original: Optional[Exception] = None, 
        context: Optional[Dict[str, Any]] = None
    ):
        self.service = service
        self.error_type = error_type
        self.original = original
        self.context = context or {}
        self.timestamp = datetime.now()
        
        # Get error type properties
        type_info = ERROR_TYPES.get(error_type, ERROR_TYPES["unknown"])
        self.transient = type_info.get("transient", False)
        self.exit_code = type_info.get("exit_code", 1)
        
        # Set full message
        super().__init__(f"{service}.{error_type}: {message}")
    
    @property
    def full_type(self) -> str:
        """Get the full error type (service.type)."""
        return f"{self.service}.{self.error_type}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for serialization."""
        return {
            "service": self.service,
            "error_type": self.error_type,
            "message": str(self),
            "timestamp": self.timestamp.isoformat(),
            "transient": self.transient,
            "context": self.context,
            "original": str(self.original) if self.original else None
        }


def create_handler(
    service: str, 
    retry_attempts: int = 3,
    include_timing: bool = True
) -> Callable:
    """Create a combined error handler with retry and timing.
    
    This single function replaces multiple separate decorators to reduce line count.
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time() if include_timing else None
            
            for attempt in range(1, retry_attempts + 1 if retry_attempts else 2):
                try:
                    result = func(*args, **kwargs)
                    
                    # Log timing on success
                    if include_timing:
                        duration = time.time() - start_time
                        logger.info(f"{service}.{func.__name__} succeeded in {duration:.3f}s")
                    
                    return result
                
                except ServiceError as e:
                    # For transient errors, retry if not the last attempt
                    if e.transient and attempt < (retry_attempts or 1):
                        logger.info(f"Retrying {func.__name__} due to {e.error_type} (attempt {attempt}/{retry_attempts})")
                        time.sleep(2 ** (attempt - 1))  # Exponential backoff
                        continue
                    
                    # Log timing on failure
                    if include_timing:
                        duration = time.time() - start_time
                        logger.info(f"{service}.{func.__name__} failed in {duration:.3f}s")
                    
                    raise
                
                except Exception as e:
                    # Create context with function info
                    context = {
                        "function": func.__name__,
                        "args": [str(arg)[:100] for arg in args[:5] if not isinstance(arg, (dict, list))],
                        "kwargs": {k: str(v)[:100] for k, v in list(kwargs.items())[:5] if not isinstance(v, (dict, list))}
                    }
                    
                    # Add HTTP context if available
                    if hasattr(e, 'response') and hasattr(e.response, 'status_code'):
                        context['status_code'] = e.response.status_code
                        context['url'] = getattr(e.response.request, 'url', 'unknown')
                    
                    # Classify error
                    error_type, message = classify_error(e, service)
                    
                    # Create ServiceError
                    service_error = ServiceError(
                        service=service,
                        error_type=error_type,
                        message=message or str(e),
                        original=e,
                        context=context
                    )
                    
                    # For transient errors, retry if not the last attempt
                    if service_error.transient and attempt < (retry_attempts or 1):
                        logger.info(f"Retrying {func.__name__} due to {error_type} (attempt {attempt}/{retry_attempts})")
                        time.sleep(2 ** (attempt - 1))  # Exponential backoff
                        continue
                    
                    # Log timing on failure
                    if include_timing:
                        duration = time.time() - start_time
                        logger.info(f"{service}.{func.__name__} failed in {duration:.3f}s")
                    
                    raise service_error
                
        return wrapper
    
    return decorator


def classify_error(error: Exception, service: str) -> Tuple[str, str]:
    """Classify an exception into an appropriate error type."""
    # Import here to avoid circular imports
    from .handlers import get_error_message
    
    # Handle database-specific errors
    if service == "database":
        # Check for common database error types
        error_name = type(error).__name__
        for cls_name, (error_type, base_msg) in DB_ERROR_MAPPINGS.items():
            if cls_name in error_name:
                message = get_error_message(service, error_type)
                return error_type, message
        
        # Check for database integrity errors
        if "IntegrityError" in error_name:
            error_str = str(error).lower()
            if "unique constraint" in error_str:
                return "integrity", get_error_message(service, "integrity")
            if "foreign key constraint" in error_str:
                return "integrity", get_error_message(service, "integrity")
        
        return "unknown", get_error_message(service, "unknown")
    
    # Standard HTTP error handling
    if hasattr(error, 'response') and hasattr(error.response, 'status_code'):
        status = error.response.status_code
        error_type = "validation"  # Default for HTTP errors
        
        # Check status code against mapping
        if status in HTTP_STATUS_ERRORS:
            error_type = HTTP_STATUS_ERRORS[status]
        elif status >= 500:
            error_type = "server"
        elif status >= 400:
            error_type = "validation"
        
        return error_type, get_error_message(service, error_type)
    
    # Check common exception types
    error_name = type(error).__name__
    error_str = str(error).lower()
    
    if any(term in error_name for term in ["Timeout", "TimeoutError"]):
        return "timeout", get_error_message(service, "timeout")
    
    if any(term in error_name for term in ["Connection", "Network"]):
        return "network", get_error_message(service, "network")
    
    if "JSON" in error_str or "parse" in error_str:
        return "parse", get_error_message(service, "parse")
        
    if any(term in error_name for term in ["ValueError", "TypeError", "AttributeError"]):
        return "validation", get_error_message(service, "validation")
    
    # Default to unknown
    return "unknown", get_error_message(service, "unknown")
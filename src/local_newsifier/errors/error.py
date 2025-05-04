"""
Core error handling components.

This module defines the ServiceError class and core decorators.
"""

import functools
import logging
import time
from datetime import datetime
from typing import Any, Callable, Dict, Optional, Type, cast

# Common error types for all services
ERROR_TYPES = {
    # Network connectivity issues
    "network": {"transient": True, "retry": True, "exit_code": 2},
    
    # Request timeout errors
    "timeout": {"transient": True, "retry": True, "exit_code": 3},
    
    # Rate limiting errors
    "rate_limit": {"transient": True, "retry": True, "exit_code": 4},
    
    # Authentication errors
    "auth": {"transient": False, "retry": False, "exit_code": 5},
    
    # Response parsing errors
    "parse": {"transient": False, "retry": False, "exit_code": 6},
    
    # Input validation errors
    "validation": {"transient": False, "retry": False, "exit_code": 7},
    
    # Resource not found errors
    "not_found": {"transient": False, "retry": False, "exit_code": 8},
    
    # Server-side errors
    "server": {"transient": True, "retry": True, "exit_code": 9},
    
    # Unknown/unexpected errors
    "unknown": {"transient": False, "retry": False, "exit_code": 1}
}

logger = logging.getLogger(__name__)


class ServiceError(Exception):
    """Unified error type for all external service errors.
    
    A single error class that consolidates all error information,
    instead of using a complex hierarchy of error types.
    """
    
    def __init__(
        self, 
        service: str,
        error_type: str, 
        message: str, 
        original: Optional[Exception] = None, 
        context: Optional[Dict[str, Any]] = None
    ):
        """Initialize a ServiceError.
        
        Args:
            service: Service identifier ("apify", "rss", etc.)
            error_type: Error type ("network", "timeout", etc.)
            message: Human-readable error message
            original: Original exception that was caught
            context: Additional context information
        """
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


def handle_service_error(service: str) -> Callable:
    """Create a decorator for handling service errors.
    
    Args:
        service: Service identifier ("apify", "rss", etc.)
        
    Returns:
        Decorator function for error handling
    """
    def decorator(func: Callable) -> Callable:
        """Decorate a function with service error handling."""
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            """Wrapped function with error handling."""
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
                    "args": [str(arg)[:100] for arg in args[:5] if not isinstance(arg, (dict, list))],
                    "kwargs": {k: str(v)[:100] for k, v in list(kwargs.items())[:5] 
                               if not isinstance(v, (dict, list))}
                }
                
                # Classify error
                error_type, error_message = _classify_error(e, service)
                
                # Add HTTP context if available
                if hasattr(e, 'response') and hasattr(e.response, 'status_code'):
                    context['status_code'] = e.response.status_code
                    context['url'] = getattr(e.response.request, 'url', 'unknown')
                
                # Convert to ServiceError
                raise ServiceError(
                    service=service,
                    error_type=error_type,
                    message=error_message or str(e),
                    original=e,
                    context=context
                )
        
        return wrapper
    
    return decorator


def with_retry(max_attempts: int = 3) -> Callable:
    """Create a decorator for retrying transient errors.
    
    Args:
        max_attempts: Maximum number of retry attempts
        
    Returns:
        Decorator function for retry handling
    """
    def decorator(func: Callable) -> Callable:
        """Decorate a function with retry logic."""
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            """Wrapped function with retry logic."""
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except ServiceError as e:
                    # Only retry transient errors, and only if not the last attempt
                    if e.transient and attempt < max_attempts - 1:
                        logger.info(
                            f"Retrying {func.__name__} due to transient error: {e.error_type} "
                            f"(attempt {attempt + 1}/{max_attempts})"
                        )
                        # Simple backoff: 1s, 2s, 4s, etc.
                        time.sleep(2 ** attempt)
                        continue
                    raise
        
        return wrapper
    
    return decorator


def with_timing(service: str) -> Callable:
    """Create a decorator for timing service calls.
    
    Args:
        service: Service identifier ("apify", "rss", etc.)
        
    Returns:
        Decorator function for timing
    """
    def decorator(func: Callable) -> Callable:
        """Decorate a function with timing logic."""
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            """Wrapped function with timing."""
            start_time = time.time()
            result = None
            error = None
            
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                error = e
                raise
            finally:
                duration = time.time() - start_time
                # Log timing info
                status = "failed" if error else "succeeded"
                logger.info(
                    f"{service}.{func.__name__} {status} in {duration:.3f}s"
                )
        
        return wrapper
    
    return decorator


def _classify_error(error: Exception, service: str) -> tuple:
    """Classify an exception into an appropriate error type.
    
    Args:
        error: The exception to classify
        service: Service identifier
        
    Returns:
        Tuple of (error_type, error_message)
    """
    # Check for HTTP status code
    if hasattr(error, 'response') and hasattr(error.response, 'status_code'):
        status = error.response.status_code
        if status == 401 or status == 403:
            return "auth", f"Authentication failed: {error}"
        elif status == 404:
            return "not_found", f"Resource not found: {error}"
        elif status == 429:
            return "rate_limit", f"Rate limit exceeded: {error}"
        elif status >= 500:
            return "server", f"Server error: {error}"
        elif status >= 400:
            return "validation", f"Request validation failed: {error}"
    
    # Check exception type
    error_name = type(error).__name__
    
    if "Timeout" in error_name or "TimeoutError" in error_name:
        return "timeout", f"Request timed out: {error}"
    
    if "Connection" in error_name or "Network" in error_name:
        return "network", f"Network error: {error}"
    
    # Check for parsing errors
    if "JSON" in str(error) or "parse" in str(error).lower():
        return "parse", f"Failed to parse response: {error}"
        
    # Check for validation errors
    if any(err_type in error_name for err_type in ["ValueError", "TypeError", "AttributeError"]):
        return "validation", f"Validation error: {error}"
    
    # Default to unknown
    return "unknown", f"Unexpected error: {error}"
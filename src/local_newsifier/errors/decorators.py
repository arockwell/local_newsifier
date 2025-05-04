"""
Decorator factories for service error handling.

This module provides decorators for error handling, retry logic, 
and performance monitoring for external service integrations.
"""

import functools
import logging
import time
from typing import Any, Callable, Dict, List, Optional, Type, Union, cast
import re

import tenacity
from tenacity import (
    retry, 
    retry_if_exception, 
    stop_after_attempt, 
    wait_exponential
)

from .service_errors import ServiceError
from .mapping import get_error_mappings, get_error_type_info

logger = logging.getLogger(__name__)

def create_error_handler(service: str) -> Callable:
    """Factory function for creating service-specific error handlers.
    
    This decorator transforms exceptions from external services into
    structured ServiceError instances, ensuring consistent error handling.
    
    Args:
        service: The service identifier (e.g., "apify", "rss").
        
    Returns:
        A decorator that wraps functions to provide error handling.
    """
    error_mappings = get_error_mappings(service)
    
    def handle_service_errors(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            try:
                return func(*args, **kwargs)
            except ServiceError:
                # Already handled, just re-raise
                raise
            except Exception as e:
                # Create context with sanitized args/kwargs
                # Avoid including large objects in the context
                context = {
                    "function": func.__name__,
                    "args": [str(arg)[:100] for arg in args if not isinstance(arg, (dict, list))],
                    "kwargs": {
                        k: (str(v)[:100] if not isinstance(v, (dict, list)) else f"{type(v).__name__}") 
                        for k, v in kwargs.items()
                    }
                }
                
                # Find matching error mapping
                for exc_type, pattern, error_type, msg_template in error_mappings:
                    if isinstance(e, exc_type):
                        error_string = str(e)
                        
                        # Check if pattern matches (if pattern provided)
                        if pattern is None:
                            matches = True
                        elif isinstance(pattern, re.Pattern):
                            matches = bool(pattern.search(error_string))
                        else:  # String pattern
                            matches = pattern in error_string
                        
                        if matches:
                            error_info = get_error_type_info(error_type)
                            is_transient = error_info.get("is_transient", False)
                            
                            # Format the message template
                            format_dict = {"error": str(e)}
                            
                            # Add timeout value if available (for timeout errors)
                            if error_type == "timeout" and hasattr(e, "timeout"):
                                format_dict["timeout"] = e.timeout
                                
                            # Format the message
                            message = msg_template.format(**format_dict)
                            
                            # Add additional context specific to the error type
                            if hasattr(e, "request") and hasattr(e.request, "url"):
                                context["url"] = e.request.url
                                
                            if hasattr(e, "response") and hasattr(e.response, "status_code"):
                                context["status_code"] = e.response.status_code
                                
                            raise ServiceError(
                                service=service,
                                error_type=error_type,
                                message=message,
                                original=e,
                                context=context,
                                is_transient=is_transient
                            )
                
                # If no match found, use unknown error type
                logger.warning(
                    f"No specific error mapping found for {type(e).__name__} in {service} service. "
                    f"Using generic unknown error type."
                )
                raise ServiceError(
                    service=service,
                    error_type="unknown",
                    message=f"Unexpected {service} error: {str(e)}",
                    original=e,
                    context=context
                )
                
        return wrapper
    
    return handle_service_errors

# Create service-specific error handlers
handle_apify_errors = create_error_handler("apify")
handle_rss_errors = create_error_handler("rss")
handle_web_scraper_errors = create_error_handler("web_scraper")

def create_retry_handler(
    service: str,
    max_attempts: int = 3,
    max_wait: int = 30
) -> Callable:
    """Create a retry decorator for transient service errors.
    
    This decorator automatically retries operations that fail with
    transient errors, using exponential backoff.
    
    Args:
        service: The service identifier.
        max_attempts: Maximum number of retry attempts.
        max_wait: Maximum wait time in seconds.
        
    Returns:
        A decorator that provides retry functionality.
    """
    
    def is_transient_error(exception: Exception) -> bool:
        """Determine if an exception is transient and should be retried.
        
        Args:
            exception: The exception to check.
            
        Returns:
            True if the exception is transient, False otherwise.
        """
        if isinstance(exception, ServiceError):
            return exception.is_transient
        return False
    
    def retry_service_calls(func: Callable) -> Callable:
        """Decorator that applies retry logic to a function.
        
        Args:
            func: The function to wrap with retry logic.
            
        Returns:
            The wrapped function with retry logic.
        """
        @tenacity.retry(
            retry=tenacity.retry_if_exception(is_transient_error),
            stop=tenacity.stop_after_attempt(max_attempts),
            wait=tenacity.wait_exponential(multiplier=1, max=max_wait),
            before_sleep=lambda retry_state: logger.info(
                f"Retrying {func.__name__} due to transient {service} error "
                f"(attempt {retry_state.attempt_number}/{max_attempts})"
            )
        )
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            """Wrapped function with retry logic.
            
            Args:
                *args: Positional arguments to pass to the function.
                **kwargs: Keyword arguments to pass to the function.
                
            Returns:
                The result of the function call.
            """
            return func(*args, **kwargs)
        return wrapper
    
    return retry_service_calls

# Create service-specific retry handlers
retry_apify_calls = create_retry_handler("apify")
retry_rss_calls = create_retry_handler("rss")
retry_web_scraper_calls = create_retry_handler("web_scraper")

def time_service_calls(service: str) -> Callable:
    """Creates a timing decorator for performance monitoring.
    
    This decorator measures the execution time of service calls
    and logs performance metrics.
    
    Args:
        service: The service identifier.
        
    Returns:
        A decorator that provides timing functionality.
    """
    
    def decorator(func: Callable) -> Callable:
        """Decorator that applies timing logic to a function.
        
        Args:
            func: The function to wrap with timing logic.
            
        Returns:
            The wrapped function with timing logic.
        """
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            """Wrapped function with timing logic.
            
            Args:
                *args: Positional arguments to pass to the function.
                **kwargs: Keyword arguments to pass to the function.
                
            Returns:
                The result of the function call.
            """
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
                # Log performance metrics
                metrics = {
                    "service": service,
                    "operation": func.__name__,
                    "duration_ms": int(duration * 1000),
                    "success": error is None,
                }
                
                if error:
                    if isinstance(error, ServiceError):
                        metrics["error_type"] = error.error_type
                    else:
                        metrics["error_type"] = type(error).__name__
                
                log_level = logging.INFO if error is None else logging.WARNING
                logger.log(
                    log_level, 
                    f"{service}.{func.__name__} completed in {metrics['duration_ms']}ms "
                    f"(success={metrics['success']})"
                )
                
                # Log detailed metrics at debug level
                logger.debug(f"{service} call metrics: {metrics}")
                
        return wrapper
    
    return decorator

# Create combined decorator factory
def create_service_handler(service: str, with_retry: bool = True) -> Callable:
    """Create a combined decorator for error handling, retry and timing.
    
    This function combines error handling, retry logic, and timing
    into a single decorator for convenience.
    
    Args:
        service: The service identifier.
        with_retry: Whether to include retry logic.
        
    Returns:
        A decorator that combines error handling, retry, and timing.
    """
    
    def full_service_handler(func: Callable) -> Callable:
        """Combined decorator for full service handling.
        
        Args:
            func: The function to wrap.
            
        Returns:
            The wrapped function with full service handling.
        """
        handlers = []
        
        # Apply in reverse order (bottom decorator will execute first)
        # Error handler should be closest to the function
        handlers.append(create_error_handler(service))
        
        if with_retry:
            handlers.append(create_retry_handler(service))
        
        handlers.append(time_service_calls(service))
        
        # Apply all handlers
        result = func
        for handler in handlers:
            result = handler(result)
        
        return result
    
    return full_service_handler

# Combined handlers for specific services
handle_apify = create_service_handler("apify")
handle_rss = create_service_handler("rss")
handle_web_scraper = create_service_handler("web_scraper")
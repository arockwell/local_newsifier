"""Utility functions and decorators for error handling.

This module provides reusable utilities for error handling, including
decorators that can be applied to service methods to standardize
error handling patterns.
"""

import functools
import inspect
import logging
import time
from typing import Any, Callable, Dict, Optional, Type, TypeVar, cast, get_type_hints

from apify_client.errors import ApifyApiError
import requests.exceptions
from tenacity import retry, stop_after_attempt, wait_exponential
from tenacity.retry import retry_if_exception_type

from local_newsifier.errors.apify import (
    ApifyError,
    ApifyNetworkError,
    ApifyRateLimitError,
    parse_apify_error
)

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


def with_apify_error_handling(
    operation_name: Optional[str] = None,
    include_args: bool = True,
) -> Callable[[F], F]:
    """Decorator to standardize Apify error handling.
    
    This decorator catches Apify-related exceptions and transforms them
    into appropriate ApifyError subclasses with context preservation.
    
    Args:
        operation_name: Name of the operation being performed (defaults to function name)
        include_args: Whether to include function arguments in error context
        
    Returns:
        Decorated function
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Determine operation name
            op_name = operation_name or f"{func.__module__}.{func.__name__}"
            
            # Extract context from arguments if requested
            context: Dict[str, Any] = {}
            if include_args:
                # Add kwargs to context directly
                context.update({k: v for k, v in kwargs.items() if k != "token"})
                
                # Add positional args based on function signature
                sig = inspect.signature(func)
                param_names = list(sig.parameters.keys())
                
                # Skip 'self' in methods
                start_idx = 1 if param_names and param_names[0] == "self" else 0
                
                # Map positional args to parameter names
                for i, arg in enumerate(args[start_idx:], start_idx):
                    if i < len(param_names):
                        param_name = param_names[i]
                        # Skip sensitive parameters and complex objects
                        if param_name != "token" and isinstance(arg, (str, int, float, bool, type(None))):
                            context[param_name] = arg
            
            try:
                return func(*args, **kwargs)
            except (ApifyApiError, requests.exceptions.RequestException) as e:
                # Parse the original exception into an appropriate ApifyError
                apify_error = parse_apify_error(e, op_name, context)
                raise apify_error from e
            except Exception as e:
                # For other unexpected errors, wrap in a general ApifyError
                if isinstance(e, ApifyError):
                    # If it's already an ApifyError, just raise it
                    raise
                else:
                    error = ApifyError(
                        message=f"Unexpected error during {op_name}: {str(e)}",
                        original_error=e,
                        operation=op_name,
                        context=context
                    )
                    raise error from e
                
        return cast(F, wrapper)
    return decorator


def with_apify_retry(
    max_attempts: int = 3,
    min_wait: float = 1.0,
    max_wait: float = 10.0,
    retry_network_errors: bool = True,
    retry_rate_limit_errors: bool = True,
    retry_other_errors: bool = False,
) -> Callable[[F], F]:
    """Decorator to add retry logic for Apify operations.
    
    This decorator adds tenacity-based retry logic for specific
    error types that are considered transient.
    
    Args:
        max_attempts: Maximum number of retry attempts
        min_wait: Minimum wait time between retries in seconds
        max_wait: Maximum wait time between retries in seconds
        retry_network_errors: Whether to retry on network errors
        retry_rate_limit_errors: Whether to retry on rate limit errors
        retry_other_errors: Whether to retry on other Apify errors
        
    Returns:
        Decorated function
    """
    def decorator(func: F) -> F:
        # Build list of exceptions to retry on
        retry_exceptions: list[Type[Exception]] = []
        
        if retry_network_errors:
            retry_exceptions.extend([
                requests.exceptions.ConnectionError,
                requests.exceptions.Timeout,
                requests.exceptions.RequestException,
                ApifyNetworkError,
            ])
        
        if retry_rate_limit_errors:
            retry_exceptions.append(ApifyRateLimitError)
        
        if retry_other_errors:
            retry_exceptions.append(ApifyError)
        
        # Apply tenacity retry with wait calculation
        @retry(
            retry=retry_if_exception_type(tuple(retry_exceptions)),
            stop=stop_after_attempt(max_attempts),
            wait=wait_exponential(
                multiplier=1,
                min=min_wait,
                max=max_wait
            ),
            before_sleep=lambda retry_state: logger.info(
                f"Retrying {func.__name__} after error: "
                f"{retry_state.outcome.exception()}, "
                f"attempt {retry_state.attempt_number}/{max_attempts}"
            ),
        )
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return func(*args, **kwargs)
        
        return cast(F, wrapper)
    return decorator


def with_apify_timing(
    operation_name: Optional[str] = None,
    log_level: int = logging.DEBUG,
) -> Callable[[F], F]:
    """Decorator to add timing information for Apify operations.
    
    This decorator logs the execution time of operations, which
    is useful for performance monitoring and debugging.
    
    Args:
        operation_name: Name of the operation being performed (defaults to function name)
        log_level: Logging level to use for timing logs
        
    Returns:
        Decorated function
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Determine operation name
            op_name = operation_name or f"{func.__module__}.{func.__name__}"
            
            # Record start time
            start_time = time.time()
            
            try:
                # Call the function
                result = func(*args, **kwargs)
                
                # Calculate and log execution time
                execution_time = time.time() - start_time
                logger.log(log_level, f"Apify operation '{op_name}' took {execution_time:.3f}s")
                
                return result
            except Exception as e:
                # Log execution time even on error
                execution_time = time.time() - start_time
                logger.log(log_level, f"Apify operation '{op_name}' failed after {execution_time:.3f}s: {str(e)}")
                raise
                
        return cast(F, wrapper)
    return decorator


def apply_full_apify_handling(
    operation_name: Optional[str] = None,
    include_args: bool = True,
    max_attempts: int = 3,
    min_wait: float = 1.0,
    max_wait: float = 10.0,
    retry_network_errors: bool = True,
    retry_rate_limit_errors: bool = True,
    retry_other_errors: bool = False,
) -> Callable[[F], F]:
    """Apply all Apify error handling decorators at once.
    
    This convenience function applies timing, error handling, and retry logic
    in the correct order with a single decorator.
    
    Args:
        (All parameters from the individual decorators)
        
    Returns:
        Function with all decorators applied
    """
    def decorator(func: F) -> F:
        # Apply decorators in the correct order (inside-out):
        # 1. Error handling (innermost - runs first)
        # 2. Retry logic (middle - runs if error handling raises)
        # 3. Timing (outermost - measures total time including retries)
        
        # Handle errors first
        error_handled = with_apify_error_handling(
            operation_name=operation_name,
            include_args=include_args
        )(func)
        
        # Then add retry logic
        retry_added = with_apify_retry(
            max_attempts=max_attempts,
            min_wait=min_wait,
            max_wait=max_wait,
            retry_network_errors=retry_network_errors,
            retry_rate_limit_errors=retry_rate_limit_errors,
            retry_other_errors=retry_other_errors
        )(error_handled)
        
        # Finally add timing
        timed = with_apify_timing(
            operation_name=operation_name
        )(retry_added)
        
        return cast(F, timed)
    
    return decorator
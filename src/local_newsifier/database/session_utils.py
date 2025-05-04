"""
Database session utilities for standardized session management.

This module provides utilities for consistent database session access and management
across the application via the dependency injection container.
"""

import logging
import functools
import sys
from typing import TypeVar, Callable, Any, Optional, Dict

from sqlmodel import Session

# Import container at runtime to avoid circular imports

# Set up logger
logger = logging.getLogger(__name__)

# Type variables for the with_container_session decorator
F = TypeVar('F', bound=Callable[..., Any])
T = TypeVar('T')


def get_container_session(container=None, test_mode: bool = False, **kwargs):
    """Get a session from the container's session factory.
    
    This function obtains the session factory from the container
    and returns a session context manager.
    
    Args:
        container: The DI container instance (optional, will be imported if not provided)
        test_mode: If True, use optimized settings for tests
        **kwargs: Additional parameters to pass to the session factory
        
    Returns:
        A session context manager
    """
    # Lazy import to avoid circular dependency
    if container is None:
        # Import only when needed to avoid circular imports
        from local_newsifier.container import container
        
    session_factory = container.get("session_factory")
    if session_factory is None:
        logger.error("Session factory not available in container")
        raise ValueError("Session factory not available in container")
    
    # Detect if we're running in a test environment
    if 'pytest' in sys.modules:
        test_mode = True
        
    return session_factory(test_mode=test_mode)


def with_container_session(func: F = None, *, container=None) -> F:
    """Decorator that provides a container-managed session to the decorated function.
    
    If a session is already provided as a keyword argument, it will be used directly.
    Otherwise, a new session will be obtained from the container.
    
    Args:
        func: The function to decorate
        container: Optional container instance to use
        
    Returns:
        The decorated function with session management
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, session: Optional[Session] = None, **kwargs):
            # If a session is already provided, use it directly
            if session is not None:
                return func(*args, session=session, **kwargs)
            
            # Otherwise, get a new session from the container
            try:
                with get_container_session(container=container) as new_session:
                    if new_session is None:
                        logger.error("Failed to obtain a valid session from container")
                        return None
                    return func(*args, session=new_session, **kwargs)
            except Exception as e:
                logger.exception(f"Error in with_container_session: {e}")
                return None
                
        return wrapper
        
    # The decorator can be used both with and without arguments
    if func is None:
        return decorator
    return decorator(func)

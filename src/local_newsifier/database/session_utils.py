"""
Database session utilities for standardized session management.

This module provides utilities for consistent database session access and management
across the application via the dependency injection container. It serves as the
single source of truth for database session management in the application.
"""

import logging
import functools
import warnings
from typing import TypeVar, Callable, Any, Optional, Dict, Generator

from sqlmodel import Session

# Import container at runtime to avoid circular imports

# Set up logger
logger = logging.getLogger(__name__)

# Type variables for the decorators
F = TypeVar('F', bound=Callable[..., Any])
T = TypeVar('T')


def get_db_session(container=None, **kwargs):
    """Get a database session from the container.
    
    This is the standard way to get a database session throughout the application.
    
    Args:
        container: Optional container instance (will be imported if not provided)
        **kwargs: Additional parameters to pass to the session factory
        
    Returns:
        A session context manager
    """
    if container is None:
        # Import only when needed to avoid circular imports
        from local_newsifier.container import container
        
    session_factory = container.get("session_factory")
    if session_factory is None:
        logger.error("Session factory not available in container")
        raise ValueError("Session factory not available in container")
    return session_factory()


def with_db_session(func: F = None, *, container=None) -> F:
    """Decorator that provides a database session to the decorated function.
    
    This is the standard decorator for functions that need a database session.
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
                with get_db_session(container=container) as new_session:
                    if new_session is None:
                        logger.error("Failed to obtain a valid session from container")
                        return None
                    return func(*args, session=new_session, **kwargs)
            except Exception as e:
                logger.exception(f"Error in with_db_session: {e}")
                return None
                
        return wrapper
        
    # The decorator can be used both with and without arguments
    if func is None:
        return decorator
    return decorator(func)


# Legacy functions with deprecation warnings

def get_container_session(container=None, **kwargs):
    """Get a session from the container's session factory (DEPRECATED).
    
    This function is deprecated. Use get_db_session instead.
    
    Args:
        container: The DI container instance (optional)
        **kwargs: Additional parameters to pass to the session factory
        
    Returns:
        A session context manager
    """
    warnings.warn(
        "get_container_session() is deprecated. Use get_db_session() instead.",
        DeprecationWarning, 
        stacklevel=2
    )
    return get_db_session(container=container, **kwargs)


def with_container_session(func: F = None, *, container=None) -> F:
    """Decorator that provides a container-managed session (DEPRECATED).
    
    This decorator is deprecated. Use with_db_session instead.
    
    Args:
        func: The function to decorate
        container: Optional container instance to use
        
    Returns:
        The decorated function with session management
    """
    warnings.warn(
        "with_container_session() is deprecated. Use with_db_session() instead.",
        DeprecationWarning, 
        stacklevel=2
    )
    return with_db_session(func, container=container)

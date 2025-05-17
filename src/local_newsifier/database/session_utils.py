"""
Database session utilities for standardized session management.

This module provides utilities for consistent database session access and management
using fastapi-injectable.
"""

import logging
import functools
from typing import TypeVar, Callable, Any, Optional

from sqlmodel import Session
from fastapi_injectable import get_injected_obj
from local_newsifier.di.providers import get_session

# Set up logger
logger = logging.getLogger(__name__)

# Type variables for the with_session decorator
F = TypeVar('F', bound=Callable[..., Any])
T = TypeVar('T')


def with_session(func: F = None) -> F:
    """Decorator that provides a session to the decorated function.
    
    If a session is already provided as a keyword argument, it will be used directly.
    Otherwise, a new session will be obtained from the injectable provider.
    
    Args:
        func: The function to decorate
        
    Returns:
        The decorated function with session management
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, session: Optional[Session] = None, **kwargs):
            # If a session is already provided, use it directly
            if session is not None:
                return func(*args, session=session, **kwargs)
            
            # Otherwise, get a new session from the injectable provider
            try:
                session_generator = get_injected_obj(get_session)
                with session_generator as new_session:
                    if new_session is None:
                        logger.error("Failed to obtain a valid session from injectable provider")
                        return None
                    return func(*args, session=new_session, **kwargs)
            except Exception as e:
                logger.exception(f"Error in with_session: {e}")
                return None
                
        return wrapper
        
    # The decorator can be used both with and without arguments
    if func is None:
        return decorator
    return decorator(func)


def get_session_factory():
    """Get a session factory function from the injectable provider.
    
    Returns:
        A callable that yields a database session when called
    """
    return get_injected_obj(get_session)
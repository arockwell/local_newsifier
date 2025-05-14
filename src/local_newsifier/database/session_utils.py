"""
Database session utilities for standardized session management.

This module provides legacy utilities for consistent database session access and 
management. These functions are deprecated and will be removed in a future version.
Please use the fastapi-injectable pattern for new code.
"""

import logging
import functools
import sys
from typing import TypeVar, Callable, Any, Optional, Dict

from sqlmodel import Session
from fastapi_injectable import get_injected_obj
from local_newsifier.di.providers import get_session

# Set up logger
logger = logging.getLogger(__name__)

# Type variables for the with_container_session decorator
F = TypeVar('F', bound=Callable[..., Any])
T = TypeVar('T')


def get_container_session(container=None, test_mode: bool = False, **kwargs):
    """Get a session using the injectable session provider.
    
    This function is deprecated. Use fastapi-injectable's get_session directly
    in new code.
    
    Args:
        container: No longer used, kept for backward compatibility
        test_mode: If True, use optimized settings for tests
        **kwargs: Additional parameters (no longer used)
        
    Returns:
        A database session
    """
    logger.warning("get_container_session is deprecated. Use fastapi-injectable's get_session instead.")
    
    # Use the injectable get_session provider
    session_generator = get_injected_obj(get_session)
    
    # Return the session context
    return session_generator


def with_container_session(func: F = None, *, container=None) -> F:
    """Decorator that provides a session to the decorated function.
    
    This function is deprecated. Use fastapi-injectable's get_session directly
    in new code.
    
    If a session is already provided as a keyword argument, it will be used directly.
    Otherwise, a new session will be obtained from the injectable provider.
    
    Args:
        func: The function to decorate
        container: No longer used, kept for backward compatibility
        
    Returns:
        The decorated function with session management
    """
    logger.warning("with_container_session is deprecated. Use fastapi-injectable's get_session instead.")
    
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
                logger.exception(f"Error in with_container_session: {e}")
                return None
                
        return wrapper
        
    # The decorator can be used both with and without arguments
    if func is None:
        return decorator
    return decorator(func)

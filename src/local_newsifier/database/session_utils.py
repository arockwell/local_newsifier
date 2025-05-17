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


# Set up logger
logger = logging.getLogger(__name__)

# Type variables for the with_container_session decorator
F = TypeVar('F', bound=Callable[..., Any])
T = TypeVar('T')


def get_container_session(*, test_mode: bool = False, **kwargs):
    """Get a session generator using the injectable provider."""
    # Detect if we're running in a test environment
    if 'pytest' in sys.modules:
        test_mode = True

    from local_newsifier.di.providers import get_session

    # The provider already handles session creation and cleanup
    return get_session()


def with_container_session(func: F = None) -> F:
    """Decorator that provides a managed session to the decorated function.

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

            try:
                session_gen = get_container_session()
                new_session = next(session_gen)
                try:
                    return func(*args, session=new_session, **kwargs)
                finally:
                    session_gen.close()
            except Exception as e:
                logger.exception(f"Error in with_container_session: {e}")
                return None
                
        return wrapper
        
    # The decorator can be used both with and without arguments
    if func is None:
        return decorator
    return decorator(func)

"""Database engine and session management using SQLModel."""

import logging
import traceback
import time
import warnings
from contextlib import contextmanager
from typing import Generator, Optional, Callable, TypeVar, Any

from sqlmodel import create_engine, Session, SQLModel
from sqlalchemy import text

# Import common settings to avoid circular imports
from local_newsifier.config.common import (
    DEFAULT_DB_POOL_SIZE,
    DEFAULT_DB_MAX_OVERFLOW,
    DEFAULT_DB_ECHO,
)

# Re-export get_settings for backward compatibility
from local_newsifier.config.settings import get_settings
from local_newsifier.database.session_utils import get_db_session, with_db_session

# Set up logger
logger = logging.getLogger(__name__)

# Type variables for the with_session decorator
F = TypeVar('F', bound=Callable[..., Any])
T = TypeVar('T')


def get_engine(url: Optional[str] = None, max_retries: int = 3, retry_delay: int = 2, 
               test_mode: bool = False):
    """Get SQLModel engine with enhanced logging and retry logic.

    Args:
        url: Database URL (if None, uses settings)
        max_retries: Maximum number of connection retries
        retry_delay: Seconds to wait between retries
        test_mode: If True, use faster retry logic for tests

    Returns:
        SQLModel engine or None if connection fails after retries
    """
    # Use faster retry for tests
    if test_mode:
        retry_delay = 0.01  # Use milliseconds instead of seconds for tests
    
    for attempt in range(max_retries + 1):
        try:
            # Import settings here to avoid circular imports
            from local_newsifier.config.settings import get_settings
            settings = get_settings()
            url = url or str(settings.DATABASE_URL)
            
            # Log database connection attempt (without password)
            safe_url = url
            if settings.POSTGRES_PASSWORD and settings.POSTGRES_PASSWORD in url:
                safe_url = url.replace(settings.POSTGRES_PASSWORD, "********")
            
            if attempt > 0:
                logger.info(f"Retry {attempt}/{max_retries} connecting to database: {safe_url}")
            else:
                logger.info(f"Connecting to database: {safe_url}")
            
            # Only add application_name for PostgreSQL
            connect_args = {}
            if url.startswith("postgresql:"):
                connect_args = {
                    "application_name": "local_newsifier",
                    "connect_timeout": 10,  # Timeout after 10 seconds
                }
                
            # Use settings or default values from common module
            pool_size = getattr(settings, 'DB_POOL_SIZE', DEFAULT_DB_POOL_SIZE)
            max_overflow = getattr(settings, 'DB_MAX_OVERFLOW', DEFAULT_DB_MAX_OVERFLOW)
            echo = getattr(settings, 'DB_ECHO', DEFAULT_DB_ECHO)
                
            engine = create_engine(
                url,
                pool_size=pool_size,
                max_overflow=max_overflow,
                connect_args=connect_args,
                echo=echo,
                # Added for better connection stability
                pool_pre_ping=True,
                pool_recycle=300,  # Recycle connections after 5 minutes
            )
            
            # Verify connection works with a simple query
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                
            logger.info("Database engine created and verified successfully")
            return engine
        except Exception as e:
            logger.error(f"Failed to create database engine (attempt {attempt+1}/{max_retries+1}): {str(e)}")
            
            if attempt < max_retries:
                logger.info(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                logger.error(f"All connection attempts failed. Last error: {str(e)}")
                logger.error(f"Exception details: {traceback.format_exc()}")
                # Instead of raising, return None so the application can continue
                return None


def get_session() -> Generator[Session, None, None]:
    """Get a database session (DEPRECATED).

    This function is deprecated. Use get_db_session from session_utils instead.

    Yields:
        Database session or None if engine creation fails
    """
    warnings.warn(
        "get_session() is deprecated. Use get_db_session() from session_utils instead.",
        DeprecationWarning, 
        stacklevel=2
    )
    
    # Use the new standardized approach internally
    session_ctx = get_db_session()
    try:
        with session_ctx as session:
            yield session
    except Exception as e:
        logger.error(f"Error during session: {str(e)}")
        logger.error(traceback.format_exc())
        yield None


@contextmanager
def transaction(session: Session):
    """Transaction context manager.

    Args:
        session: Database session

    Yields:
        None

    Raises:
        Exception: Any exception that occurs during the transaction
    """
    try:
        yield
        session.commit()
    except Exception:
        session.rollback()
        raise


def create_db_and_tables(engine=None):
    """Create all tables in the database with detailed logging.

    Args:
        engine: SQLModel engine (if None, creates one)
    """
    try:
        logger.info("Starting database tables creation")
        if engine is None:
            logger.debug("No engine provided, creating new engine")
            try:
                # Use runtime import to avoid circular dependencies
                engine = get_engine()
            except Exception as e:
                logger.error(f"Failed to create engine: {str(e)}")
                logger.error(f"Exception details: {traceback.format_exc()}")
                return False

        # Using SQLModel's metadata to create tables
        logger.debug("Creating database tables using SQLModel metadata")
        try:
            SQLModel.metadata.create_all(engine)
            logger.info("Successfully created all database tables")
            return True
        except Exception as e:
            logger.error(f"Failed to create database tables: {str(e)}")
            logger.error(f"Exception details: {traceback.format_exc()}")
            return False
    except Exception as e:
        logger.error(f"Unexpected error in create_db_and_tables: {str(e)}")
        logger.error(f"Exception details: {traceback.format_exc()}")
        return False


class SessionManager:
    """Session manager for database operations (DEPRECATED).
    
    This class is deprecated. Use get_db_session from session_utils instead.
    """

    def __init__(self, test_mode: bool = False):
        """Initialize the session manager.
        
        Args:
            test_mode: If True, use optimized database settings for tests
        """
        warnings.warn(
            "SessionManager is deprecated. Use get_db_session() from session_utils instead.",
            DeprecationWarning, 
            stacklevel=2
        )
        self.session = None
        self.engine = None
        self.test_mode = test_mode

    def __enter__(self):
        """Enter the context manager.

        Returns:
            Session: Database session or None if engine creation fails
        """
        try:
            # Use the new standardized approach internally
            session_ctx = get_db_session()
            self.session = session_ctx.__enter__()
            return self.session
        except Exception as e:
            logger.error(f"SessionManager: Error creating session: {str(e)}")
            logger.error(traceback.format_exc())
            return None

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the context manager.

        Args:
            exc_type: Exception type
            exc_val: Exception value
            exc_tb: Exception traceback
        """
        if self.session:
            try:
                if exc_type:
                    logger.debug("SessionManager: Rolling back transaction due to exception")
                    self.session.rollback()
                else:
                    logger.debug("SessionManager: Committing transaction")
                    self.session.commit()
            except Exception as e:
                logger.error(f"SessionManager: Error during commit/rollback: {str(e)}")
                logger.error(traceback.format_exc())
            finally:
                try:
                    self.session.close()
                except Exception as e:
                    logger.error(f"SessionManager: Error closing session: {str(e)}")


def with_session(func: F) -> F:
    """Add session management to database functions (DEPRECATED).

    This decorator is deprecated. Use with_db_session from session_utils instead.

    Args:
        func: Function to decorate

    Returns:
        Decorated function
    """
    warnings.warn(
        "with_session() is deprecated. Use with_db_session() from session_utils instead.",
        DeprecationWarning, 
        stacklevel=2
    )
    
    # Use the new standardized approach internally
    return with_db_session(func)

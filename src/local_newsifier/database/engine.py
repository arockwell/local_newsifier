"""Database engine and session management using SQLModel."""

import logging
import time
import traceback
from contextlib import contextmanager
from typing import Any, Callable, Generator, Optional, TypeVar

from sqlalchemy import text
from sqlmodel import Session, SQLModel, create_engine

# Import common settings to avoid circular imports
from local_newsifier.config.common import (DEFAULT_DB_ECHO, DEFAULT_DB_MAX_OVERFLOW,
                                           DEFAULT_DB_POOL_SIZE)

# Set up logger
logger = logging.getLogger(__name__)

# Type variables for the with_session decorator
F = TypeVar("F", bound=Callable[..., Any])
T = TypeVar("T")


def get_engine(
    url: Optional[str] = None, max_retries: int = 3, retry_delay: int = 2, test_mode: bool = False
):
    """Get SQLModel engine with enhanced logging and retry logic.

    Args:
        url: Database URL (if None, uses settings)
        max_retries: Maximum number of connection retries
        retry_delay: Seconds to wait between retries
        test_mode: If True, use faster retry logic for tests

    Returns:
        SQLModel engine or None if connection fails after retries
    """
    # Check if we're running in test mode
    if test_mode:
        logger.info("Running in test mode")
        # Try to get the shared test engine from pytest plugin
        try:
            import pytest

            if hasattr(pytest, "test_engine_plugin"):
                # First try to get a worker-specific engine when running with pytest-xdist
                try:
                    # For pytest-xdist parallel execution, we can figure out the worker ID
                    # from sys.argv or environment variable if available
                    import os
                    import sys

                    # Check for xdist worker ID patterns
                    worker_id = None
                    # Look for gw0, gw1, etc. in sys.argv for xdist workers
                    for arg in sys.argv:
                        if arg.startswith("gw"):
                            worker_id = arg
                            break

                    # If we didn't find it in sys.argv, check for PYTEST_XDIST_WORKER env var
                    if not worker_id:
                        worker_id = os.environ.get("PYTEST_XDIST_WORKER")

                    engine = pytest.test_engine_plugin.get_engine(worker_id)
                except (ImportError, AttributeError):
                    # Fallback to the standard method if we can't determine worker ID
                    engine = pytest.test_engine_plugin.get_engine()

                if engine:
                    worker_name = worker_id or "master"
                    logger.info(
                        f"Using shared test engine from pytest plugin (worker: {worker_name})"
                    )
                    return engine
        except (ImportError, AttributeError):
            # We're not running under pytest or plugin isn't registered
            logger.debug("Test engine plugin not available")

        # Use faster retry for tests if we don't get a test engine
        retry_delay = 0.01  # Use milliseconds instead of seconds for tests

    for attempt in range(max_retries + 1):
        try:
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
            pool_size = getattr(settings, "DB_POOL_SIZE", DEFAULT_DB_POOL_SIZE)
            max_overflow = getattr(settings, "DB_MAX_OVERFLOW", DEFAULT_DB_MAX_OVERFLOW)
            echo = getattr(settings, "DB_ECHO", DEFAULT_DB_ECHO)

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
            logger.error(
                f"Failed to create database engine "
                f"(attempt {attempt + 1}/{max_retries + 1}): {str(e)}"
            )

            if attempt < max_retries:
                logger.info(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                logger.error(f"All connection attempts failed. Last error: {str(e)}")
                logger.error(f"Exception details: {traceback.format_exc()}")
                # Instead of raising, return None so the application can continue
                return None


def get_session() -> Generator[Session, None, None]:
    """Get a database session.

    Yields:
        Database session or None if engine creation fails
    """
    engine = get_engine()
    if engine is None:
        logger.warning("Cannot create session - database engine is None")
        yield None
    else:
        try:
            with Session(engine) as session:
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
    """Session manager for database operations."""

    def __init__(self, test_mode: bool = False):
        """Initialize the session manager.

        Args:
            test_mode: If True, use optimized database settings for tests
        """
        self.session = None
        self.engine = None
        self.test_mode = test_mode

    def __enter__(self):
        """Enter the context manager.

        Returns:
            Session: Database session or None if engine creation fails
        """
        try:
            # Pass test_mode to enable faster database connections in tests
            self.engine = get_engine(test_mode=self.test_mode)
            if self.engine is None:
                logger.warning("SessionManager: Cannot create session - database engine is None")
                return None

            self.session = Session(self.engine)
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
    """Add session management to database functions.

    This decorator ensures that a database session is available to the
    decorated function. If a session is provided as a keyword argument,
    it is used directly. Otherwise, a new session is created and managed
    for the duration of the function call.

    Args:
        func: Function to decorate

    Returns:
        Decorated function
    """

    def wrapper(*args, session: Optional[Session] = None, **kwargs):
        """Execute function with session management.

        Args:
            session: SQLModel session
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Result of the decorated function or None if session creation fails
        """
        if session is not None:
            try:
                return func(*args, session=session, **kwargs)
            except Exception as e:
                logger.error(f"Error in with_session (provided session): {str(e)}")
                logger.error(traceback.format_exc())
                return None

        try:
            with SessionManager() as new_session:
                if new_session is None:
                    logger.warning(
                        "with_session: SessionManager returned None, cannot execute function"
                    )
                    return None
                return func(*args, session=new_session, **kwargs)
        except Exception as e:
            logger.error(f"Error in with_session (new session): {str(e)}")
            logger.error(traceback.format_exc())
            return None

    return wrapper

"""Database configuration and connection management."""

import warnings
from typing import Any

from sqlmodel import Session

from local_newsifier.config.settings import get_settings
from local_newsifier.database.session_utils import get_db_session as get_standardized_db_session


class DatabaseSettings:
    """Database configuration settings."""

    def __init__(self):
        """Initialize the database settings wrapper."""
        self._settings = get_settings()

    @property
    def POSTGRES_USER(self) -> str:
        """Get PostgreSQL username."""
        return self._settings.POSTGRES_USER

    @property
    def POSTGRES_PASSWORD(self) -> str:
        """Get PostgreSQL password."""
        return self._settings.POSTGRES_PASSWORD

    @property
    def POSTGRES_HOST(self) -> str:
        """Get PostgreSQL host."""
        return self._settings.POSTGRES_HOST

    @property
    def POSTGRES_PORT(self) -> str:
        """Get PostgreSQL port."""
        return self._settings.POSTGRES_PORT

    @property
    def POSTGRES_DB(self) -> str:
        """Get PostgreSQL database name."""
        return self._settings.POSTGRES_DB

    @property
    def DATABASE_URL(self) -> str:
        """Get the database URL."""
        return str(self._settings.DATABASE_URL)

    def get_database_url(self) -> str:
        """Get the database URL.

        Returns:
            str: The database URL
        """
        return str(self._settings.DATABASE_URL)


def get_database() -> Any:
    """Get a database engine instance.

    Returns:
        SQLModel engine instance
    """
    # Import here to avoid circular imports
    from local_newsifier.database.engine import get_engine
    
    settings = get_settings()
    return get_engine(str(settings.DATABASE_URL))


def get_database_settings() -> DatabaseSettings:
    """Get database settings instance.

    Returns:
        DatabaseSettings instance
    """
    return DatabaseSettings()


def get_db_session() -> Session:
    """Get a new database session (DEPRECATED).
    
    This function is deprecated. Use get_db_session from session_utils instead.
    
    Returns:
        Session: Database session
    """
    warnings.warn(
        "get_db_session() in config/database.py is deprecated. Use get_db_session() from database/session_utils instead.",
        DeprecationWarning, 
        stacklevel=2
    )
    
    # Use the standardized approach internally
    session_ctx = get_standardized_db_session()
    return session_ctx.__enter__()

"""Database configuration and connection management."""

from typing import Any, Optional

from sqlmodel import Session

# Import common settings to avoid circular imports
from local_newsifier.config.common import (
    get_database_url as build_database_url,
    get_cursor_db_name,
)


class DatabaseSettings:
    """Database configuration settings."""

    def __init__(self):
        """Initialize the database settings wrapper."""
        # Import settings here to avoid circular imports
        from local_newsifier.config.settings import get_settings
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
    from local_newsifier.config.settings import get_settings
    
    settings = get_settings()
    return get_engine(str(settings.DATABASE_URL))


def get_database_settings() -> DatabaseSettings:
    """Get database settings instance.

    Returns:
        DatabaseSettings instance
    """
    return DatabaseSettings()


def get_db_session() -> Session:
    """Get a new database session.
    
    Returns:
        Session: Database session
    """
    engine = get_database()
    return Session(engine)


def get_database_url_from_components(
    user: Optional[str] = None,
    password: Optional[str] = None,
    host: Optional[str] = None,
    port: Optional[str] = None,
    db_name: Optional[str] = None
) -> str:
    """Get a database URL from components or settings.
    
    If any component is None, it will be fetched from settings.
    
    Args:
        user: PostgreSQL username
        password: PostgreSQL password
        host: PostgreSQL host
        port: PostgreSQL port
        db_name: PostgreSQL database name
        
    Returns:
        Database URL string
    """
    # Import settings here to avoid circular imports
    from local_newsifier.config.settings import get_settings
    
    settings = get_settings()
    
    # Use provided values or defaults from settings
    user = user or settings.POSTGRES_USER
    password = password or settings.POSTGRES_PASSWORD
    host = host or settings.POSTGRES_HOST
    port = port or settings.POSTGRES_PORT
    db_name = db_name or settings.POSTGRES_DB
    
    return build_database_url(user, password, host, port, db_name)

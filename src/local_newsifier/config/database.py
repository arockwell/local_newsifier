"""Database configuration and connection management."""

from typing import Any
from sqlmodel import Session, create_engine, SQLModel
from sqlalchemy.orm import sessionmaker

from local_newsifier.database.init import init_db, get_session
from local_newsifier.config.settings import get_settings


class DatabaseSettings:
    """Database configuration settings (compatibility wrapper).

    This class exists for backward compatibility. It wraps the main Settings class
    to provide the same interface as before.
    """

    def __init__(self):
        self._settings = get_settings()

    @property
    def POSTGRES_USER(self) -> str:
        return self._settings.POSTGRES_USER

    @property
    def POSTGRES_PASSWORD(self) -> str:
        return self._settings.POSTGRES_PASSWORD

    @property
    def POSTGRES_HOST(self) -> str:
        return self._settings.POSTGRES_HOST

    @property
    def POSTGRES_PORT(self) -> str:
        return self._settings.POSTGRES_PORT

    @property
    def POSTGRES_DB(self) -> str:
        return self._settings.POSTGRES_DB

    @property
    def DATABASE_URL(self) -> str:
        """Get the database URL."""
        return str(self._settings.DATABASE_URL)

    def get_database_url(self) -> str:
        """Get the database URL (legacy method).

        Returns:
            str: The database URL
        """
        return str(self._settings.DATABASE_URL)


def get_database() -> Any:
    """Get a database engine instance.

    Returns:
        SQLAlchemy engine instance
    """
    settings = get_settings()
    return init_db(str(settings.DATABASE_URL))


def get_db_session() -> sessionmaker:
    """Get a database session factory.

    Returns:
        SQLAlchemy session factory
    """
    engine = get_database()
    return get_session(engine)


def get_database_settings() -> DatabaseSettings:
    """Get database settings instance.

    Returns:
        DatabaseSettings instance
    """
    return DatabaseSettings()

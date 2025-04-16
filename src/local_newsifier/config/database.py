"""Database configuration and connection management."""

from contextlib import contextmanager
from typing import Any, Generator

from sqlmodel import Session, create_engine

from local_newsifier.config.settings import get_settings
from local_newsifier.models.database import init_db


class DatabaseSettings:
    """Database configuration settings (compatibility wrapper).

    This class exists for backward compatibility. It wraps the main Settings
    class to provide the same interface as before.
    """

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
        """Get the database URL (legacy method).

        Returns:
            str: The database URL
        """
        return str(self._settings.DATABASE_URL)


def get_database() -> Any:
    """Get a database engine instance.

    Returns:
        SQLModel engine instance
    """
    settings = get_settings()
    return init_db(str(settings.DATABASE_URL))


def create_session_factory(engine=None):
    """Create a session factory.

    Args:
        engine: SQLModel engine (if None, creates one)

    Returns:
        Session factory
    """
    if engine is None:
        engine = get_database()
    return Session


def get_db() -> Generator[Session, None, None]:
    """Get database session.

    Yields:
        Session: Database session
    """
    engine = get_database()
    session = Session(engine)
    try:
        yield session
    finally:
        session.close()


@contextmanager
def transaction(db: Session):
    """Transaction context manager.

    Args:
        db: Database session

    Yields:
        None

    Raises:
        Exception: Any exception that occurs during the transaction
    """
    try:
        yield
        db.commit()
    except Exception:
        db.rollback()
        raise


def get_database_settings() -> DatabaseSettings:
    """Get database settings instance.

    Returns:
        DatabaseSettings instance
    """
    return DatabaseSettings()

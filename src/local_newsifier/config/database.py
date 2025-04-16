"""Database configuration and connection management."""

from contextlib import contextmanager
from typing import Any, Generator

from sqlalchemy.orm import sessionmaker, Session

from local_newsifier.models.database import Base, init_db
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
    return sessionmaker(bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Get database session.
    
    Yields:
        Session: Database session
    """
    SessionLocal = get_db_session()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


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

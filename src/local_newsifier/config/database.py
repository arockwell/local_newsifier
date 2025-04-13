"""Database configuration and connection management."""

from typing import Any
from sqlalchemy.orm import sessionmaker

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
    
    def get_database_url(self) -> str:
        """Get the database URL."""
        return self._settings.get_database_url()


def get_database() -> Any:
    """Get a database engine instance.
    
    Returns:
        SQLAlchemy engine instance
    """
    settings = get_settings()
    return init_db(settings.get_database_url())


def get_db_session() -> sessionmaker:
    """Get a database session factory.
    
    Returns:
        SQLAlchemy session factory
    """
    engine = get_database()
    return sessionmaker(bind=engine)
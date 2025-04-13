"""Database configuration and connection management."""

import os
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from local_newsifier.models.database import Base, init_db


def get_cursor_db_name() -> str:
    """Get the database name for the current cursor instance.
    
    Returns:
        Database name with cursor ID
    """
    cursor_id = os.environ.get("CURSOR_DB_ID", "default")
    return f"local_newsifier_{cursor_id}"


class DatabaseSettings(BaseSettings):
    """Database configuration settings."""
    
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: str = "5432"
    POSTGRES_DB: str = get_cursor_db_name()
    
    @property
    def DATABASE_URL(self) -> str:
        """Get the database URL."""
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"


def get_database(env_file: Optional[str] = None) -> create_engine:
    """Get a database engine instance.
    
    Args:
        env_file: Optional path to .env file to load settings from
        
    Returns:
        SQLAlchemy engine instance
    """
    settings = DatabaseSettings(_env_file=env_file)
    return init_db(str(settings.DATABASE_URL))


def get_db_session(env_file: Optional[str] = None) -> sessionmaker:
    """Get a database session factory.
    
    Args:
        env_file: Optional path to .env file to load settings from
        
    Returns:
        SQLAlchemy session factory
    """
    engine = get_database(env_file)
    return sessionmaker(bind=engine)


def get_database_settings(env_file: Optional[str] = None) -> DatabaseSettings:
    """Get database settings.
    
    Args:
        env_file: Optional path to .env file to load settings from
        
    Returns:
        DatabaseSettings instance
    """
    return DatabaseSettings(_env_file=env_file)

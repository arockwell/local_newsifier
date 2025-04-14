"""Database configuration and connection management."""

import os
from pathlib import Path
from typing import Any, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from local_newsifier.models.database import Base, init_db
from local_newsifier.config.settings import get_settings, get_cursor_db_name


class DatabaseSettings(BaseSettings):
    """Database settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="allow",  # Allow extra fields from environment
    )

    # PostgreSQL Database settings
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: str = "5432"
    POSTGRES_DB: str = get_cursor_db_name()

    @property
    def DATABASE_URL(self) -> str:
        """Construct database URL from components."""
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    def get_database_url(self) -> str:
        """Get the database URL (legacy method).

        Returns:
            str: The database URL
        """
        return self.DATABASE_URL


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
        sessionmaker: SQLAlchemy session factory
    """
    engine = get_database()
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_database_settings() -> DatabaseSettings:
    """Get database settings.

    Returns:
        DatabaseSettings: Database settings instance
    """
    return DatabaseSettings()

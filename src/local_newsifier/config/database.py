"""Database configuration settings."""

from typing import Any, Optional

from pydantic import validator
from pydantic_settings import BaseSettings
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

from ..models.database import get_session, init_db


class DatabaseSettings(BaseSettings):
    """Database configuration settings."""

    DATABASE_URL: str = "sqlite:///local_newsifier.db"

    model_config = {
        "case_sensitive": True,
        "env_file_encoding": "utf-8",
        "validate_assignment": True,
        "extra": "ignore",  # Allow extra attributes like _env_file
        "env_prefix": "",  # Don't use any prefix for env vars
        "use_enum_values": True,
        "protected_namespaces": (),  # Allow setting private attrs like _env_file
    }


def get_database_settings(env_file: str = ".env") -> DatabaseSettings:
    """Get database settings.

    Args:
        env_file: Environment file to use

    Returns:
        Database settings instance
    """
    return DatabaseSettings(_env_file=env_file)


def get_database(env_file: str = ".env") -> Engine:
    """Get database engine instance.

    Args:
        env_file: Environment file to use

    Returns:
        SQLAlchemy engine instance
    """
    settings = get_database_settings(env_file)
    return init_db(str(settings.DATABASE_URL))


def get_db_session(env_file: str = ".env") -> sessionmaker:
    """Get database session factory.

    Args:
        env_file: Environment file to use

    Returns:
        SQLAlchemy session factory
    """
    engine = get_database(env_file)
    return get_session(engine)

"""Database configuration settings."""

from typing import Any, Optional
import os
import uuid

from pydantic import PostgresDsn, validator
from pydantic_settings import BaseSettings
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

from ..models.database import get_session, init_db


def get_cursor_db_name() -> str:
    """Get a unique database name for this cursor instance.
    
    Returns:
        A unique database name based on cursor ID or environment variable
    """
    # Use environment variable if set, otherwise generate a new one
    cursor_id = os.getenv("CURSOR_DB_ID")
    if not cursor_id:
        cursor_id = str(uuid.uuid4())[:8]
        os.environ["CURSOR_DB_ID"] = cursor_id
    return f"local_newsifier_{cursor_id}"


class DatabaseSettings(BaseSettings):
    """Database configuration settings."""

    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: str = "5432"
    POSTGRES_DB: str = get_cursor_db_name()

    DATABASE_URL: Optional[PostgresDsn] = None

    @validator("DATABASE_URL", pre=True)
    def assemble_db_connection(cls, v: Optional[str], values: dict[str, Any]) -> Any:
        """Assemble database connection URL.

        Args:
            v: Optional database URL
            values: Other settings values

        Returns:
            Assembled database URL
        """
        if isinstance(v, str):
            return v
        return PostgresDsn.build(
            scheme="postgresql",
            username=values.get("POSTGRES_USER"),
            password=values.get("POSTGRES_PASSWORD"),
            host=values.get("POSTGRES_HOST"),
            port=int(values.get("POSTGRES_PORT", "5432")),
            path=values.get("POSTGRES_DB"),
        )

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


def get_engine() -> Engine:
    """Get database engine.

    Returns:
        Database engine
    """
    settings = get_database_settings()
    return create_engine(str(settings.DATABASE_URL))


def get_session() -> sessionmaker:
    """Get session factory.

    Returns:
        Session factory
    """
    engine = get_engine()
    return sessionmaker(bind=engine)

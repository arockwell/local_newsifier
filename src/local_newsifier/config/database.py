"""Database configuration settings."""

from typing import Any, Optional

from pydantic import PostgresDsn, validator
from pydantic_settings import BaseSettings
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

from ..models.database import get_session, init_db


class DatabaseSettings(BaseSettings):
    """Database configuration settings."""

    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: str = "5432"
    POSTGRES_DB: str = "local_newsifier"

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


def get_database(env_file: str = ".env") -> Engine:
    """Get database engine instance.

    Args:
        env_file: Environment file to use

    Returns:
        SQLAlchemy engine instance
    """
    settings = DatabaseSettings(_env_file=env_file)
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

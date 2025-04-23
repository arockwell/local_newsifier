"""Application settings configuration."""

import os
import uuid
from pathlib import Path
from typing import List, Optional

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


def get_cursor_db_name() -> str:
    """Get a cursor-specific database name.

    Returns:
        Database name with cursor ID
    """
    cursor_id = os.environ.get("CURSOR_DB_ID")
    if not cursor_id:
        cursor_id = str(uuid.uuid4())[:8]
        os.environ["CURSOR_DB_ID"] = cursor_id
    return f"local_newsifier_{cursor_id}"


class Settings(BaseSettings):
    """Application settings using Pydantic BaseSettings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        validate_default=True,
        extra="allow",  # Allow extra fields like computed DATABASE_URL
    )

    # OpenAI API key
    OPENAI_API_KEY: Optional[str] = None

    # Database settings
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: str = "5432"
    POSTGRES_DB: str = Field(default_factory=get_cursor_db_name)
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_ECHO: bool = False

    # Directory settings
    OUTPUT_DIR: Path = Field(default_factory=lambda: Path("output"))
    CACHE_DIR: Path = Field(default_factory=lambda: Path("cache"))
    TEMP_DIR: Path = Field(default_factory=lambda: Path("temp"))

    # Logging settings
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE: Optional[Path] = None

    # Scraping settings
    USER_AGENT: str = "Local-Newsifier/1.0"
    REQUEST_TIMEOUT: int = 30
    MAX_RETRIES: int = 3
    RETRY_DELAY: int = 5

    # NER analysis settings
    NER_MODEL: str = "en_core_web_lg"
    ENTITY_TYPES: List[str] = Field(default_factory=lambda: ["PERSON", "ORG", "GPE"])

    # Authentication settings
    SECRET_KEY: str = Field(default_factory=lambda: str(uuid.uuid4()))
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "development_password"  # Default for development only

    @computed_field
    def DATABASE_URL(self) -> str:
        """Get the database URL based on environment.

        Checks for DATABASE_URL environment variable first (commonly used by Railway and other platforms)
        and falls back to constructing one from individual components if not present.
        """
        # Check if DATABASE_URL is provided directly (common in Railway and other cloud platforms)
        env_db_url = os.environ.get("DATABASE_URL")
        if env_db_url:
            return env_db_url

        # Otherwise construct from individual components
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@"
            f"{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    def get_database_url(self) -> str:
        """Get the database URL based on environment."""
        return str(self.DATABASE_URL)

    def create_directories(self) -> None:
        """Create necessary directories if they don't exist."""
        for directory in [self.OUTPUT_DIR, self.CACHE_DIR, self.TEMP_DIR]:
            directory.mkdir(parents=True, exist_ok=True)


# Create global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get the settings instance.

    Returns:
        Settings: The global settings instance
    """
    return settings

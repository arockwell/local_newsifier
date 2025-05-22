"""Application settings configuration."""

import os
import uuid
from pathlib import Path
from typing import List, Optional

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

from local_newsifier.config.common import (DEFAULT_CACHE_DIR, DEFAULT_DB_ECHO,
                                           DEFAULT_DB_MAX_OVERFLOW, DEFAULT_DB_POOL_SIZE,
                                           DEFAULT_LOG_FORMAT, DEFAULT_LOG_LEVEL,
                                           DEFAULT_OUTPUT_DIR, DEFAULT_POSTGRES_HOST,
                                           DEFAULT_POSTGRES_PASSWORD, DEFAULT_POSTGRES_PORT,
                                           DEFAULT_POSTGRES_USER, DEFAULT_TEMP_DIR,
                                           get_cursor_db_name)
from local_newsifier.config.common import get_database_url as build_database_url


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
    POSTGRES_USER: str = DEFAULT_POSTGRES_USER
    POSTGRES_PASSWORD: str = DEFAULT_POSTGRES_PASSWORD
    POSTGRES_HOST: str = DEFAULT_POSTGRES_HOST
    POSTGRES_PORT: str = DEFAULT_POSTGRES_PORT
    POSTGRES_DB: str = Field(default_factory=get_cursor_db_name)
    DB_POOL_SIZE: int = DEFAULT_DB_POOL_SIZE
    DB_MAX_OVERFLOW: int = DEFAULT_DB_MAX_OVERFLOW
    DB_ECHO: bool = DEFAULT_DB_ECHO

    # Directory settings
    OUTPUT_DIR: Path = Field(default_factory=lambda: DEFAULT_OUTPUT_DIR)
    CACHE_DIR: Path = Field(default_factory=lambda: DEFAULT_CACHE_DIR)
    TEMP_DIR: Path = Field(default_factory=lambda: DEFAULT_TEMP_DIR)

    # Logging settings
    LOG_LEVEL: str = DEFAULT_LOG_LEVEL
    LOG_FORMAT: str = DEFAULT_LOG_FORMAT
    LOG_FILE: Optional[Path] = None

    # Celery settings
    CELERY_TASK_SERIALIZER: str = "json"
    CELERY_RESULT_SERIALIZER: str = "json"
    CELERY_ACCEPT_CONTENT: List[str] = ["json"]
    CELERY_TIMEZONE: str = "UTC"
    CELERY_TASK_TRACK_STARTED: bool = True
    CELERY_TASK_TIME_LIMIT: int = 30 * 60  # 30 minutes
    CELERY_WORKER_MAX_TASKS_PER_CHILD: int = 100  # Restart worker after 100 tasks
    CELERY_WORKER_HIJACK_ROOT_LOGGER: bool = False
    CELERY_WORKER_PREFETCH_MULTIPLIER: int = 1  # Prefetch one task at a time

    # Celery Beat settings
    CELERY_BEAT_SCHEDULE: dict = {
        "fetch_rss_feeds_hourly": {
            "task": "local_newsifier.tasks.fetch_rss_feeds",
            "schedule": 3600.0,  # Every hour
            "args": (None,),
            "options": {"expires": 3500},
        },
        "analyze_entity_trends_daily": {
            "task": "local_newsifier.tasks.analyze_entity_trends",
            "schedule": 86400.0,  # Every day
            "kwargs": {"time_interval": "day", "days_back": 7},
            "options": {"expires": 86000},
        },
    }

    # Task-specific settings
    ARTICLE_PROCESSING_TIMEOUT: int = 600  # 10 minutes timeout for article processing
    RSS_FEED_URLS: List[str] = Field(
        default_factory=lambda: [
            "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml",
            "https://feeds.washingtonpost.com/rss/national",
            "https://www.theguardian.com/us/rss",
        ]
    )

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

    # Apify settings
    APIFY_TOKEN: Optional[str] = Field(default=None, description="Token for Apify API")
    APIFY_WEBHOOK_SECRET: Optional[str] = Field(
        default=None, description="Secret for validating Apify webhook requests"
    )

    def validate_apify_token(self, skip_validation_in_test=False) -> str:
        """Validate that APIFY_TOKEN is set and return it.

        Args:
            skip_validation_in_test: If True and in test mode, skip validation

        Raises:
            ValueError: If APIFY_TOKEN is not set (and not in test mode when skipping)

        Returns:
            str: The validated APIFY_TOKEN or a dummy token in test mode
        """
        # Check if we're in a test environment
        import os

        in_test_env = os.environ.get("PYTEST_CURRENT_TEST") is not None

        # Skip validation if requested and in test mode
        if skip_validation_in_test and in_test_env:
            if not self.APIFY_TOKEN:
                import logging

                logging.warning("Using dummy Apify token for testing")
                return "test_dummy_token"

        # Standard validation
        if not self.APIFY_TOKEN:
            raise ValueError(
                "APIFY_TOKEN is required but not set. "
                "Please set the APIFY_TOKEN environment variable. "
                "See the 'Getting started > Secrets' section in README.md for instructions."
            )
        return self.APIFY_TOKEN

    @computed_field
    def DATABASE_URL(self) -> str:
        """Get the database URL based on environment.

        Checks for DATABASE_URL environment variable first (commonly used by Railway
        and other platforms) and falls back to constructing one from individual
        components if not present.
        """
        # Check if DATABASE_URL is provided directly (common in Railway and other cloud platforms)
        env_db_url = os.environ.get("DATABASE_URL")
        if env_db_url:
            return env_db_url

        # Otherwise construct from individual components
        return build_database_url(
            self.POSTGRES_USER,
            self.POSTGRES_PASSWORD,
            self.POSTGRES_HOST,
            self.POSTGRES_PORT,
            self.POSTGRES_DB,
        )

    @computed_field
    def CELERY_BROKER_URL(self) -> str:
        """Get the Celery broker URL based on environment.

        Uses Redis as the message broker.
        """
        # Use dedicated environment variable if available
        broker_url = os.environ.get("CELERY_BROKER_URL")
        if broker_url:
            return broker_url

        # Use Redis with default settings
        return "redis://localhost:6379/0"

    @computed_field
    def CELERY_RESULT_BACKEND(self) -> str:
        """Get the Celery result backend URL based on environment.

        Uses Redis as the result backend.
        """
        # Use dedicated environment variable if available
        result_backend = os.environ.get("CELERY_RESULT_BACKEND")
        if result_backend:
            return result_backend

        # Use Redis with default settings
        return "redis://localhost:6379/0"

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

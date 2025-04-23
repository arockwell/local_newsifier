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
    
    @computed_field
    def CELERY_BROKER_URL(self) -> str:
        """Get the Celery broker URL based on environment.
        Uses DATABASE_URL with specific query parameters for PostgreSQL broker.
        """
        # Use dedicated environment variable if available
        broker_url = os.environ.get("CELERY_BROKER_URL")
        if broker_url:
            return broker_url
            
        # Otherwise construct from database URL
        db_url = str(self.DATABASE_URL)
        return f"{db_url}?prepared_statements=False"
    
    @computed_field
    def CELERY_RESULT_BACKEND(self) -> str:
        """Get the Celery result backend URL based on environment.
        Uses DATABASE_URL with db+ prefix for SQLAlchemy backend.
        """
        # Use dedicated environment variable if available
        result_backend = os.environ.get("CELERY_RESULT_BACKEND")
        if result_backend:
            return result_backend
            
        # Otherwise construct from database URL
        db_url = str(self.DATABASE_URL)
        # Convert to SQLAlchemy format by adding "db+" prefix
        if db_url.startswith("postgresql://"):
            return f"db+{db_url}"
        return f"db+{db_url}"

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

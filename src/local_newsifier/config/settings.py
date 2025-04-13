"""Application settings configuration."""

import os
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Union

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings


def get_cursor_db_name() -> str:
    """Get a cursor-specific database name.
    
    Returns:
        Database name with cursor ID
    """
    cursor_id = os.getenv("CURSOR_DB_ID")
    if not cursor_id:
        cursor_id = str(uuid.uuid4())[:8]
        os.environ["CURSOR_DB_ID"] = cursor_id
    return f"local_newsifier_{cursor_id}"


class Settings(BaseSettings):
    """Application settings using Pydantic BaseSettings."""
    
    # Database settings
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: str = "5432"
    POSTGRES_DB: str = "local_newsifier"  # Default value will be overridden by validator
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    
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
    
    @model_validator(mode='before')
    @classmethod
    def set_db_name(cls, values: Dict) -> Dict:
        """Set the database name if not provided."""
        if 'POSTGRES_DB' not in values or values['POSTGRES_DB'] == "local_newsifier":
            values['POSTGRES_DB'] = get_cursor_db_name()
        return values
    
    def get_database_url(self) -> str:
        """Get the database URL."""
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    def create_directories(self) -> None:
        """Create necessary directories if they don't exist."""
        self.OUTPUT_DIR.mkdir(exist_ok=True, parents=True)
        self.CACHE_DIR.mkdir(exist_ok=True, parents=True)
        self.TEMP_DIR.mkdir(exist_ok=True, parents=True)
        
        if self.LOG_FILE:
            self.LOG_FILE.parent.mkdir(exist_ok=True, parents=True)
    
    model_config = {
        "env_prefix": "",
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
        "extra": "allow",  # Allow extra fields
    }


def get_settings() -> Settings:
    """Get application settings singleton.
    
    Returns:
        Settings instance
    """
    settings = Settings()
    settings.create_directories()
    return settings
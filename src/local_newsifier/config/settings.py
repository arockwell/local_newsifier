"""Application settings for local_newsifier."""

from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    # OpenAI API key
    openai_api_key: Optional[str] = None

    # Database settings
    DATABASE_URL: str = "sqlite:///./local_newsifier.db"


# Create global settings instance
settings = Settings() 
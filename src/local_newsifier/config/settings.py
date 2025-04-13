"""Settings configuration for the application."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
    
    # OpenAI API settings
    openai_api_key: str
    
    # Database settings
    database_url: str = "sqlite:///local_newsifier.db"
    
    # Other settings can be added here as needed


# Create a global settings instance
settings = Settings() 
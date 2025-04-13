"""Tests for application settings."""

import os
from pathlib import Path
import pytest

from local_newsifier.config.settings import Settings, get_settings


@pytest.fixture
def clean_env():
    """Fixture to clean environment variables."""
    # Store original environment values
    original_env = {
        key: os.environ.get(key)
        for key in [
            "POSTGRES_USER", "POSTGRES_PASSWORD", "POSTGRES_HOST",
            "POSTGRES_PORT", "POSTGRES_DB", "USE_SQLITE",
            "OUTPUT_DIR", "CACHE_DIR", "TEMP_DIR", "LOG_LEVEL",
            "CURSOR_DB_ID",
        ]
    }
    
    # Clear environment variables for test
    for key in original_env:
        if key in os.environ:
            del os.environ[key]
    
    yield
    
    # Restore original environment
    for key, value in original_env.items():
        if value is not None:
            os.environ[key] = value
        elif key in os.environ:
            del os.environ[key]


def test_default_settings(clean_env):
    """Test default settings values."""
    settings = Settings()
    
    # Test default database settings
    assert settings.POSTGRES_USER == "postgres"
    assert settings.POSTGRES_PASSWORD == "postgres"
    assert settings.POSTGRES_HOST == "localhost"
    assert settings.POSTGRES_PORT == "5432"
    assert "local_newsifier" in settings.POSTGRES_DB  # Should include cursor ID
    assert settings.SQLITE_URL == "sqlite:///local_newsifier.db"
    
    # Test default directories
    assert isinstance(settings.OUTPUT_DIR, Path)
    assert isinstance(settings.CACHE_DIR, Path)
    assert isinstance(settings.TEMP_DIR, Path)
    
    # Test default logging settings
    assert settings.LOG_LEVEL == "INFO"
    assert settings.LOG_FORMAT == "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    assert settings.LOG_FILE is None
    
    # Test default scraping settings
    assert settings.USER_AGENT == "Local-Newsifier/1.0"
    assert settings.REQUEST_TIMEOUT == 30
    assert settings.MAX_RETRIES == 3
    assert settings.RETRY_DELAY == 5
    
    # Test default NER settings
    assert settings.NER_MODEL == "en_core_web_lg"
    assert settings.ENTITY_TYPES == ["PERSON", "ORG", "GPE"]


def test_database_url_postgres(clean_env):
    """Test DATABASE_URL property with PostgreSQL default."""
    settings = Settings(
        POSTGRES_USER="testuser",
        POSTGRES_PASSWORD="testpass",
        POSTGRES_HOST="testhost",
        POSTGRES_PORT="5433",
        POSTGRES_DB="testdb"
    )
    
    expected_url = "postgresql://testuser:testpass@testhost:5433/testdb"
    assert settings.DATABASE_URL == expected_url


def test_database_url_sqlite(clean_env):
    """Test DATABASE_URL property with SQLite."""
    # Set environment to use SQLite
    os.environ["USE_SQLITE"] = "true"
    
    settings = Settings(SQLITE_URL="sqlite:///test.db")
    assert settings.DATABASE_URL == "sqlite:///test.db"


def test_environment_variable_override(clean_env):
    """Test that environment variables override defaults."""
    # Set environment variables
    os.environ["POSTGRES_USER"] = "envuser"
    os.environ["POSTGRES_PASSWORD"] = "envpass"
    os.environ["LOG_LEVEL"] = "DEBUG"
    
    settings = Settings()
    
    assert settings.POSTGRES_USER == "envuser"
    assert settings.POSTGRES_PASSWORD == "envpass"
    assert settings.LOG_LEVEL == "DEBUG"


def test_directory_creation(clean_env, tmp_path):
    """Test that directories are created if they don't exist."""
    test_output_dir = tmp_path / "output"
    test_cache_dir = tmp_path / "cache"
    
    assert not test_output_dir.exists()
    assert not test_cache_dir.exists()
    
    settings = Settings(
        OUTPUT_DIR=test_output_dir,
        CACHE_DIR=test_cache_dir
    )
    settings.create_directories()
    
    assert test_output_dir.exists()
    assert test_cache_dir.exists()


def test_get_settings(clean_env):
    """Test get_settings function."""
    settings = get_settings()
    assert isinstance(settings, Settings)
    assert settings.POSTGRES_USER == "postgres"
    
    # Check that directories are created
    assert settings.OUTPUT_DIR.exists()
    assert settings.CACHE_DIR.exists()
    assert settings.TEMP_DIR.exists()
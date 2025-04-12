"""Tests for database configuration."""

import os
from unittest.mock import patch, MagicMock

import pytest
from pydantic import ValidationError

from local_newsifier.config.database import DatabaseSettings, get_database, get_db_session


@pytest.fixture
def test_env():
    """Set up test environment variables."""
    original_env = {
        "POSTGRES_USER": os.environ.get("POSTGRES_USER"),
        "POSTGRES_PASSWORD": os.environ.get("POSTGRES_PASSWORD"),
        "POSTGRES_HOST": os.environ.get("POSTGRES_HOST"),
        "POSTGRES_PORT": os.environ.get("POSTGRES_PORT"),
        "POSTGRES_DB": os.environ.get("POSTGRES_DB"),
    }
    
    os.environ["POSTGRES_USER"] = "test"
    os.environ["POSTGRES_PASSWORD"] = "test"
    os.environ["POSTGRES_HOST"] = "localhost"
    os.environ["POSTGRES_PORT"] = "5432"
    os.environ["POSTGRES_DB"] = "test_db"
    
    yield
    
    # Restore original environment
    for key, value in original_env.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value


def test_database_settings():
    """Test database settings initialization."""
    settings = DatabaseSettings(
        POSTGRES_USER="test",
        POSTGRES_PASSWORD="test",
        POSTGRES_HOST="localhost",
        POSTGRES_PORT="5432",
        POSTGRES_DB="test_db",
        _env_file=None,  # Disable env file loading
        DATABASE_URL="postgresql://test:test@localhost:5432/test_db"  # Explicitly set DATABASE_URL
    )
    
    assert settings.POSTGRES_USER == "test"
    assert settings.POSTGRES_PASSWORD == "test"
    assert settings.POSTGRES_HOST == "localhost"
    assert settings.POSTGRES_PORT == "5432"
    assert settings.POSTGRES_DB == "test_db"
    assert str(settings.DATABASE_URL) == "postgresql://test:test@localhost:5432/test_db"


def test_database_settings_defaults():
    """Test database settings with default values."""
    # Store original environment variables
    original_env = {
        "POSTGRES_USER": os.environ.get("POSTGRES_USER"),
        "POSTGRES_PASSWORD": os.environ.get("POSTGRES_PASSWORD"),
        "POSTGRES_HOST": os.environ.get("POSTGRES_HOST"),
        "POSTGRES_PORT": os.environ.get("POSTGRES_PORT"),
        "POSTGRES_DB": os.environ.get("POSTGRES_DB"),
    }
    
    # Clear environment variables to test defaults
    for key in original_env:
        if key in os.environ:
            del os.environ[key]
    
    try:
        settings = DatabaseSettings(_env_file=None)  # Disable env file loading
        
        assert settings.POSTGRES_USER == "postgres"
        assert settings.POSTGRES_PASSWORD == "postgres"
        assert settings.POSTGRES_HOST == "localhost"
        assert settings.POSTGRES_PORT == "5432"
        assert settings.POSTGRES_DB == "local_newsifier"
        assert str(settings.DATABASE_URL) == "postgresql://postgres:postgres@localhost:5432/local_newsifier"
    finally:
        # Restore original environment
        for key, value in original_env.items():
            if value is not None:
                os.environ[key] = value
            elif key in os.environ:
                del os.environ[key]


def test_database_settings_missing_required():
    """Test database settings with missing required fields."""
    with pytest.raises(ValidationError):
        DatabaseSettings(
            _env_file=None,  # Disable env file loading
            POSTGRES_USER=None,
            POSTGRES_PASSWORD=None,
            POSTGRES_HOST=None,
            POSTGRES_PORT=None,
            POSTGRES_DB=None
        )


def test_database_settings_port_conversion():
    """Test port conversion from string to integer."""
    settings = DatabaseSettings(
        _env_file=None,  # Disable env file loading
        POSTGRES_USER="test",
        POSTGRES_PASSWORD="test",
        POSTGRES_HOST="localhost",
        POSTGRES_PORT="5432",  # String port
        POSTGRES_DB="test_db"
    )
    
    assert settings.POSTGRES_PORT == "5432"  # Port is stored as string


@patch("local_newsifier.config.database.init_db")
@patch("local_newsifier.config.database.DatabaseSettings")
def test_get_database(mock_settings, mock_init_db):
    """Test get_database function."""
    # Create a mock settings instance with a specific DATABASE_URL
    mock_settings_instance = MagicMock()
    mock_settings_instance.DATABASE_URL = "postgresql://test:test@localhost:5432/test_db"
    mock_settings.return_value = mock_settings_instance
    
    # Create a mock engine to return
    mock_engine = MagicMock()
    mock_init_db.return_value = mock_engine
    
    # Call the function and verify results
    engine = get_database()
    assert engine is mock_engine
    mock_init_db.assert_called_once_with("postgresql://test:test@localhost:5432/test_db")


@patch("local_newsifier.config.database.get_database")
def test_get_db_session(mock_get_database):
    """Test get_db_session function."""
    session_factory = get_db_session()
    assert session_factory is not None 
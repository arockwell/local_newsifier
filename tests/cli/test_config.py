"""Tests for the CLI environment configuration system."""

# json is used in several test methods
import tempfile
from pathlib import Path

import pytest

from local_newsifier.cli.config import EnvConfig


class TestEnvConfig:
    """Tests for the EnvConfig class."""

    @pytest.fixture
    def temp_config_dir(self):
        """Create a temporary directory for configuration files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_init_creates_default_config(self, temp_config_dir):
        """Test that initialization creates default configuration."""
        config = EnvConfig(config_dir=str(temp_config_dir))

        # Config file should have been created
        assert (temp_config_dir / "config.ini").exists()

        # Should have global section with current_env
        assert "global" in config.config
        assert "current_env" in config.config["global"]
        assert config.config["global"]["current_env"] == "dev"

        # Should have dev environment
        assert "dev" in config.config
        assert "name" in config.config["dev"]
        assert "DATABASE_URL" in config.config["dev"]

    def test_get_current_env(self, temp_config_dir):
        """Test getting the current environment."""
        config = EnvConfig(config_dir=str(temp_config_dir))
        assert config.get_current_env() == "dev"

    def test_set_current_env(self, temp_config_dir):
        """Test setting the current environment."""
        config = EnvConfig(config_dir=str(temp_config_dir))

        # Create a new environment
        config.create_env(
            "staging", {"name": "Staging", "DATABASE_URL": "postgresql://staging"}
        )

        # Set current environment
        assert config.set_current_env("staging") is True
        assert config.get_current_env() == "staging"

        # Try to set to non-existent environment
        assert config.set_current_env("non-existent") is False
        assert config.get_current_env() == "staging"

    def test_get_env_names(self, temp_config_dir):
        """Test getting list of environment names."""
        config = EnvConfig(config_dir=str(temp_config_dir))

        # Default should have just dev
        env_names = config.get_env_names()
        assert "dev" in env_names
        assert len(env_names) == 1

        # Add another environment
        config.create_env("prod", {"name": "Production"})
        env_names = config.get_env_names()
        assert "dev" in env_names
        assert "prod" in env_names
        assert len(env_names) == 2

    def test_get_env_config(self, temp_config_dir):
        """Test getting environment configuration."""
        config = EnvConfig(config_dir=str(temp_config_dir))

        # Get dev environment config
        env_config = config.get_env_config("dev")
        assert env_config["name"] == "Development"
        assert "DATABASE_URL" in env_config

        # Get current environment config (should be dev)
        env_config = config.get_env_config()
        assert env_config["name"] == "Development"

        # Get non-existent environment config
        env_config = config.get_env_config("non-existent")
        assert env_config == {}

    def test_create_env(self, temp_config_dir):
        """Test creating a new environment."""
        config = EnvConfig(config_dir=str(temp_config_dir))

        # Create new environment
        result = config.create_env(
            "prod",
            {
                "name": "Production",
                "DATABASE_URL": "postgresql://prod",
                "is_production": "true",
            },
        )
        assert result is True

        # Environment should exist
        assert "prod" in config.get_env_names()
        env_config = config.get_env_config("prod")
        assert env_config["name"] == "Production"
        assert env_config["DATABASE_URL"] == "postgresql://prod"
        assert env_config["is_production"] == "true"

        # Try to create existing environment
        result = config.create_env("prod", {"name": "Another Production"})
        assert result is False

        # Try to create reserved environment
        result = config.create_env("global", {"name": "Global"})
        assert result is False

    def test_update_env(self, temp_config_dir):
        """Test updating an environment."""
        config = EnvConfig(config_dir=str(temp_config_dir))

        # Create environment to update
        config.create_env(
            "staging", {"name": "Staging", "DATABASE_URL": "postgresql://staging"}
        )

        # Update environment
        result = config.update_env(
            "staging", {"name": "Updated Staging", "API_URL": "https://api.staging"}
        )
        assert result is True

        # Check updated values
        env_config = config.get_env_config("staging")
        assert env_config["name"] == "Updated Staging"
        assert env_config["DATABASE_URL"] == "postgresql://staging"
        assert env_config["API_URL"] == "https://api.staging"

        # Try to update non-existent environment
        result = config.update_env("non-existent", {"name": "Non-existent"})
        assert result is False

    def test_delete_env(self, temp_config_dir):
        """Test deleting an environment."""
        config = EnvConfig(config_dir=str(temp_config_dir))

        # Create environments
        config.create_env("staging", {"name": "Staging"})
        config.create_env("prod", {"name": "Production"})
        assert "staging" in config.get_env_names()
        assert "prod" in config.get_env_names()

        # Delete environment
        result = config.delete_env("staging")
        assert result is True
        assert "staging" not in config.get_env_names()
        assert "prod" in config.get_env_names()

        # Try to delete non-existent environment
        result = config.delete_env("non-existent")
        assert result is False

        # Set current environment to one that will be deleted
        config.set_current_env("prod")
        assert config.get_current_env() == "prod"

        # Delete current environment
        result = config.delete_env("prod")
        assert result is True
        assert "prod" not in config.get_env_names()
        # Should revert to default
        assert config.get_current_env() == "dev"

    def test_apply_env_to_settings(self, temp_config_dir, monkeypatch):
        """Test applying environment settings to system."""
        config = EnvConfig(config_dir=str(temp_config_dir))

        # Create environment with variables
        config.create_env(
            "test_env",
            {
                "name": "Test Environment",
                "DATABASE_URL": "postgresql://test",
                "APIFY_TOKEN": "test_token",
            },
        )

        # Track environment variables that get set
        env_vars = {}

        def mock_setenv(name, value):
            env_vars[name] = value

        # Mock os.environ.__setitem__
        monkeypatch.setattr("os.environ.__setitem__", mock_setenv)

        # Apply environment settings
        applied = config.apply_env_to_settings("test_env")

        # Check applied variables
        assert "DATABASE_URL" in applied
        assert "APIFY_TOKEN" in applied
        assert applied["DATABASE_URL"] == "postgresql://test"
        assert applied["APIFY_TOKEN"] == "test_token"

        # Check that environment variables were set
        assert "DATABASE_URL" in env_vars
        assert "APIFY_TOKEN" in env_vars
        assert env_vars["DATABASE_URL"] == "postgresql://test"
        assert env_vars["APIFY_TOKEN"] == "test_token"

    def test_format_config_for_display(self, temp_config_dir):
        """Test formatting configuration for display."""
        config = EnvConfig(config_dir=str(temp_config_dir))

        # Create environment with sensitive info
        config.create_env(
            "prod",
            {
                "name": "Production",
                "DATABASE_URL": "postgresql://user:password@host:5432/db",
                "APIFY_TOKEN": "secret_token",
            },
        )

        # Get formatted config with masked secrets
        formatted = config.format_config_for_display("prod", mask_secrets=True)
        assert "DATABASE_URL" in formatted
        assert "APIFY_TOKEN" in formatted
        assert ":password" not in formatted["DATABASE_URL"]
        assert "********" in formatted["DATABASE_URL"]
        assert formatted["APIFY_TOKEN"] == "********"

        # Get formatted config without masking
        formatted = config.format_config_for_display("prod", mask_secrets=False)
        assert "DATABASE_URL" in formatted
        assert "APIFY_TOKEN" in formatted
        assert "password" in formatted["DATABASE_URL"]
        assert formatted["APIFY_TOKEN"] == "secret_token"

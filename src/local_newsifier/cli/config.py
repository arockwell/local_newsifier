"""
CLI configuration management system.

This module provides functionality for managing CLI environments and configuration,
including reading/writing environment settings, selecting environments, and storing
credentials securely.
"""

import configparser
import logging
import os
import pathlib
from typing import Dict, List, Optional

# Set up logger
logger = logging.getLogger(__name__)

# Constants
DEFAULT_CONFIG_DIR = "~/.nf"
DEFAULT_CONFIG_FILE = "config.ini"
DEFAULT_ENV = "dev"
RESERVED_SECTIONS = ["global"]  # Sections in config file that aren't environments

# Environment variables that can be loaded from config (uppercase)
ENV_VARS = [
    "DATABASE_URL",
    "APIFY_TOKEN",
    "REDIS_URL",
    "API_URL",
    "LOG_LEVEL",
]

# Lowercase versions of environment variables for configparser compatibility
ENV_VARS_LOWER = [var.lower() for var in ENV_VARS]


class EnvConfig:
    """Environment configuration manager for CLI."""

    def __init__(self, config_dir: Optional[str] = None):
        """Initialize configuration system.

        Args:
            config_dir: Custom configuration directory path (default: ~/.nf)
        """
        # Set up config directory
        self.config_dir = pathlib.Path(config_dir or DEFAULT_CONFIG_DIR).expanduser()
        self.config_file = self.config_dir / DEFAULT_CONFIG_FILE

        # Ensure config directory exists
        self.config_dir.mkdir(parents=True, exist_ok=True)

        # Load config
        self.config = configparser.ConfigParser()
        if self.config_file.exists():
            self.config.read(self.config_file)

        # Initialize global section if not exists
        if "global" not in self.config:
            self.config["global"] = {"current_env": DEFAULT_ENV}

        # Initialize default environment if not exists
        if DEFAULT_ENV not in self.config:
            self.config[DEFAULT_ENV] = {
                "name": "Development",
                "database_url": "sqlite:///local_newsifier.db",  # Config lowercases keys
            }

        # Save if we made changes
        if "global" not in self.config or DEFAULT_ENV not in self.config:
            self.save_config()

    def save_config(self) -> bool:
        """Save current configuration to file.

        Returns:
            bool: True if save was successful, False otherwise
        """
        try:
            with open(self.config_file, "w") as f:
                self.config.write(f)
            return True
        except Exception as e:
            logger.error(f"Failed to save configuration: {str(e)}")
            return False

    def get_current_env(self) -> str:
        """Get the name of the currently active environment.

        Returns:
            str: Name of current environment
        """
        return self.config["global"].get("current_env", DEFAULT_ENV)

    def set_current_env(self, env_name: str) -> bool:
        """Set the current active environment.

        Args:
            env_name: Name of environment to set as current

        Returns:
            bool: True if successful, False if environment doesn't exist
        """
        if env_name not in self.config or env_name in RESERVED_SECTIONS:
            return False

        self.config["global"]["current_env"] = env_name
        return self.save_config()

    def get_env_names(self) -> List[str]:
        """Get list of configured environment names.

        Returns:
            List[str]: List of environment names
        """
        return [
            section
            for section in self.config.sections()
            if section not in RESERVED_SECTIONS
        ]

    def get_env_config(self, env_name: Optional[str] = None) -> Dict[str, str]:
        """Get configuration for a specific environment.

        Args:
            env_name: Name of environment to get, or None for current environment

        Returns:
            Dict[str, str]: Environment configuration
        """
        env = env_name or self.get_current_env()

        # Return empty dict if environment doesn't exist
        if env not in self.config:
            return {}

        return dict(self.config[env])

    def create_env(self, env_name: str, config_data: Dict[str, str]) -> bool:
        """Create a new environment configuration.

        Args:
            env_name: Name of environment to create
            config_data: Configuration data for the environment

        Returns:
            bool: True if successful, False if environment already exists
        """
        if env_name in self.config or env_name in RESERVED_SECTIONS:
            return False

        self.config[env_name] = config_data
        return self.save_config()

    def update_env(self, env_name: str, config_data: Dict[str, str]) -> bool:
        """Update an existing environment configuration.

        Args:
            env_name: Name of environment to update
            config_data: New configuration data for the environment

        Returns:
            bool: True if successful, False if environment doesn't exist
        """
        if env_name not in self.config or env_name in RESERVED_SECTIONS:
            return False

        # Update values
        for key, value in config_data.items():
            self.config[env_name][key] = value

        return self.save_config()

    def delete_env(self, env_name: str) -> bool:
        """Delete an environment configuration.

        Args:
            env_name: Name of environment to delete

        Returns:
            bool: True if successful, False if environment doesn't exist
        """
        if env_name not in self.config or env_name in RESERVED_SECTIONS:
            return False

        # If deleting current environment, switch to default
        if self.get_current_env() == env_name:
            self.set_current_env(DEFAULT_ENV)

        self.config.remove_section(env_name)
        return self.save_config()

    def apply_env_to_settings(self, env_name: Optional[str] = None) -> Dict[str, str]:
        """Apply environment configuration to system settings.

        This function loads environment variables from the configuration
        and applies them to the current process environment.

        Args:
            env_name: Name of environment to apply, or None for current

        Returns:
            Dict[str, str]: Applied environment variables
        """
        env = env_name or self.get_current_env()
        applied_vars = {}

        # Check if environment exists
        if env not in self.config:
            return applied_vars

        # Apply environment variables
        for i, var_name in enumerate(ENV_VARS):
            # Look for the lowercase version in the config
            lower_var = ENV_VARS_LOWER[i]
            if lower_var in self.config[env]:
                value = self.config[env][lower_var]
                # Set the environment variable with uppercase name
                try:
                    os.environ[var_name] = value
                except Exception as e:
                    logger.warning(
                        f"Failed to set environment variable {var_name}: {e}"
                    )
                applied_vars[lower_var] = (
                    value  # Keep lowercase key in returned dict for consistency
                )

        return applied_vars

    def format_config_for_display(
        self, env_name: str, mask_secrets: bool = True
    ) -> Dict[str, str]:
        """Format environment configuration for display to the user.

        Args:
            env_name: Name of environment to format
            mask_secrets: Whether to mask sensitive information

        Returns:
            Dict[str, str]: Formatted configuration
        """
        if env_name not in self.config:
            return {}

        result = dict(self.config[env_name])

        # Mask sensitive information
        if mask_secrets:
            # Check for password in database URL (looking for lowercase key)
            db_url_key = "database_url"
            if db_url_key in result and "password" in result[db_url_key].lower():
                db_url = result[db_url_key]
                # Parse the URL to mask the password
                if "://" in db_url:
                    prefix, rest = db_url.split("://", 1)
                    if "@" in rest:
                        auth, host_part = rest.split("@", 1)
                        if ":" in auth:
                            username, _ = auth.split(":", 1)
                            # Replace with masked version
                            masked_url = f"{prefix}://{username}:********@{host_part}"
                            result[db_url_key] = masked_url

            # Mask tokens (using lowercase keys)
            for key in ["apify_token"]:  # Use lowercase keys
                if key in result:
                    result[key] = "********"

        return result


# Global config instance for CLI use
_config_instance = None


def get_config() -> EnvConfig:
    """Get the global configuration instance.

    Returns:
        EnvConfig: Global configuration instance
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = EnvConfig()
    return _config_instance

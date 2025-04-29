"""Environment variable management for tests.

This module provides utilities for managing environment variables in tests
to ensure proper isolation and cleanup.
"""

import os
import pytest
from typing import Dict, Optional, List, Set, Callable

class EnvironmentManager:
    """Helper for managing environment variables in tests."""
    
    @staticmethod
    def save_environment(keys: List[str]) -> Dict[str, Optional[str]]:
        """Save the current values of specified environment variables.
        
        Args:
            keys: List of environment variable names to save
            
        Returns:
            Dictionary mapping keys to their current values
        """
        return {key: os.environ.get(key) for key in keys}
    
    @staticmethod
    def restore_environment(saved_values: Dict[str, Optional[str]]):
        """Restore environment variables to saved values.
        
        Args:
            saved_values: Dictionary mapping keys to values
        """
        for key, value in saved_values.items():
            if value is None:
                if key in os.environ:
                    del os.environ[key]
            else:
                os.environ[key] = value
    
    @staticmethod
    def clear_variables(keys: List[str]):
        """Clear specified environment variables.
        
        Args:
            keys: List of environment variable names to clear
        """
        for key in keys:
            if key in os.environ:
                del os.environ[key]
    
    @staticmethod
    def set_variables(variables: Dict[str, str]):
        """Set environment variables to specified values.
        
        Args:
            variables: Dictionary mapping keys to values
        """
        for key, value in variables.items():
            os.environ[key] = value
    
    @staticmethod
    def get_database_env_keys() -> List[str]:
        """Get a list of database-related environment variable keys.
        
        Returns:
            List of environment variable names
        """
        return [
            "POSTGRES_USER", "POSTGRES_PASSWORD", "POSTGRES_HOST", 
            "POSTGRES_PORT", "POSTGRES_DB", "DATABASE_URL",
            "TEST_DATABASE_URL", "CURSOR_DB_ID"
        ]
    
    @staticmethod
    def get_api_env_keys() -> List[str]:
        """Get a list of API-related environment variable keys.
        
        Returns:
            List of environment variable names
        """
        return ["SECRET_KEY", "API_HOST", "API_PORT", "DEBUG", "ENVIRONMENT"]
    
    @staticmethod
    def get_all_app_env_keys() -> List[str]:
        """Get a list of all application environment variable keys.
        
        Returns:
            List of environment variable names
        """
        return EnvironmentManager.get_database_env_keys() + EnvironmentManager.get_api_env_keys()

@pytest.fixture
def env_manager():
    """Provide an EnvironmentManager instance."""
    return EnvironmentManager

@pytest.fixture
def clean_environment():
    """Run a test with a clean environment.
    
    This fixture:
    1. Clears all environment variables related to the application
    2. Yields control to the test
    3. Restores the original environment variables
    """
    # Get all application environment variables
    env_keys = EnvironmentManager.get_all_app_env_keys()
    
    # Save current environment
    saved_env = EnvironmentManager.save_environment(env_keys)
    
    try:
        # Clear environment for test
        EnvironmentManager.clear_variables(env_keys)
        yield
    finally:
        # Restore original environment
        EnvironmentManager.restore_environment(saved_env)

@pytest.fixture
def clean_db_environment():
    """Run a test with a clean database environment.
    
    This fixture:
    1. Clears all database-related environment variables
    2. Yields control to the test
    3. Restores the original environment variables
    """
    # Get database environment variables
    env_keys = EnvironmentManager.get_database_env_keys()
    
    # Save current environment
    saved_env = EnvironmentManager.save_environment(env_keys)
    
    try:
        # Clear environment for test
        EnvironmentManager.clear_variables(env_keys)
        yield
    finally:
        # Restore original environment
        EnvironmentManager.restore_environment(saved_env)

@pytest.fixture
def test_db_environment():
    """Run a test with a test database environment.
    
    This fixture:
    1. Sets database environment variables for a test database
    2. Yields control to the test
    3. Restores the original environment variables
    """
    # Get database environment variables
    env_keys = EnvironmentManager.get_database_env_keys()
    
    # Save current environment
    saved_env = EnvironmentManager.save_environment(env_keys)
    
    try:
        # Set test database environment
        test_env = {
            "POSTGRES_USER": "postgres",
            "POSTGRES_PASSWORD": "postgres",
            "POSTGRES_HOST": "localhost",
            "POSTGRES_PORT": "5432",
            "POSTGRES_DB": "test_db",
            "TEST_DATABASE_URL": "postgresql://postgres:postgres@localhost:5432/test_db"
        }
        EnvironmentManager.set_variables(test_env)
        yield
    finally:
        # Restore original environment
        EnvironmentManager.restore_environment(saved_env)

@pytest.fixture
def with_env_vars():
    """Create a context manager for temporarily setting environment variables.
    
    Example:
        def test_something(with_env_vars):
            with with_env_vars({"TEST_VAR": "value"}):
                # Test code that uses TEST_VAR
    """
    def _with_env_vars(env_vars: Dict[str, str]):
        class EnvVarContext:
            def __init__(self, vars_to_set):
                self.vars_to_set = vars_to_set
                self.saved_vars = {}
                
            def __enter__(self):
                # Save current environment
                self.saved_vars = EnvironmentManager.save_environment(list(self.vars_to_set.keys()))
                # Set new environment variables
                EnvironmentManager.set_variables(self.vars_to_set)
                return self
                
            def __exit__(self, exc_type, exc_val, exc_tb):
                # Restore original environment
                EnvironmentManager.restore_environment(self.saved_vars)
                
        return EnvVarContext(env_vars)
        
    return _with_env_vars

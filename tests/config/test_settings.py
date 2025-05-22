"""Tests for settings configuration module."""

import os
from unittest.mock import patch

from local_newsifier.config.settings import Settings


class TestSettingsConfig:
    """Tests for Settings environment overrides and token validation."""

    def test_env_overrides(self):
        """DATABASE_URL and Celery URLs should use environment variables when set."""
        env = {
            "DATABASE_URL": "postgresql://env_user:env_pass@env_host:5432/env_db",
            "CELERY_BROKER_URL": "redis://broker:6379/1",
            "CELERY_RESULT_BACKEND": "redis://result:6379/2",
        }
        with patch.dict(os.environ, env):
            settings = Settings()
            assert settings.DATABASE_URL == env["DATABASE_URL"]
            assert settings.get_database_url() == env["DATABASE_URL"]
            assert settings.CELERY_BROKER_URL == env["CELERY_BROKER_URL"]
            assert settings.CELERY_RESULT_BACKEND == env["CELERY_RESULT_BACKEND"]

    def test_validate_apify_token_provided(self):
        """When APIFY_TOKEN is provided, it should be returned."""
        settings = Settings(APIFY_TOKEN="real_token")
        assert settings.validate_apify_token() == "real_token"

    def test_validate_apify_token_missing_in_test(self):
        """When token missing in tests and skipping validation, return dummy token."""
        with patch.dict(os.environ, {}, clear=False):
            settings = Settings(APIFY_TOKEN=None)
            token = settings.validate_apify_token(skip_validation_in_test=True)
            assert token == "test_dummy_token"

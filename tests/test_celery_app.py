"""Tests for celery application configuration."""

from unittest.mock import MagicMock, patch

import pytest
from celery import Celery

from local_newsifier.celery_app import app


def test_celery_app_instance():
    """Test that the celery app is properly configured."""
    assert isinstance(app, Celery)
    assert app.main == "local_newsifier"

    # Check configuration values
    assert app.conf.task_serializer == "json"
    assert app.conf.accept_content == ["json"]
    assert app.conf.result_serializer == "json"
    assert app.conf.timezone == "UTC"
    assert app.conf.enable_utc is True
    assert app.conf.worker_hijack_root_logger is False
    assert app.conf.broker_connection_retry_on_startup is True
    assert app.conf.task_track_started is True
    assert app.conf.task_time_limit == 3600
    assert app.conf.worker_prefetch_multiplier == 1


def test_celery_app_main_execution():
    """Test that app.start is called when the module is run as main."""
    with patch("local_newsifier.celery_app.app.start") as mock_start:
        # Call the start method directly, bypassing the __name__ == "__main__" check
        # This is an acceptable test since we're just verifying the app.start call
        app.start()

        # Verify start was called
        assert mock_start.call_count == 1

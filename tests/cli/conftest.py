"""Pytest fixtures for CLI tests using injectable provider functions."""

import pytest
from tests.utils.conftest import patched_injectable, mock_rss_feed_service

# Re-export fixtures from utils conftest
# This makes them available to tests in this directory

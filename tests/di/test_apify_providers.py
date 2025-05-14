"""Test for the Apify-related FastAPI Injectable providers."""

import os
import pytest
from unittest.mock import patch

from local_newsifier.di.providers import get_apify_service


def test_apify_service_test_mode_detection():
    """Test that the Apify service provider correctly detects test mode."""
    # Ensure we have a clean environment for this test
    with patch.dict(os.environ, {"PYTEST_CURRENT_TEST": "test_running"}, clear=True):
        # Test mode should be detected from PYTEST_CURRENT_TEST environment variable
        service = get_apify_service()
        assert service._test_mode is True, "Test mode should be True when running in pytest"
    
    # Now test without the environment variable
    with patch.dict(os.environ, {}, clear=True):
        service = get_apify_service()
        assert service._test_mode is False, "Test mode should be False when not in pytest"


def test_apify_service_cli_test_mode():
    """Test that the Apify CLI service provider works with different token sources."""
    from local_newsifier.di.providers import get_apify_service_cli
    
    # Test with explicit token
    service = get_apify_service_cli(token="test_token")
    assert service._token == "test_token"
    
    # Test without token (should use settings or environment)
    with patch("local_newsifier.services.apify_service.ApifyService.__init__", return_value=None) as mock_init:
        with patch.dict(os.environ, {}, clear=True):  # No PYTEST_CURRENT_TEST
            get_apify_service_cli()
            mock_init.assert_called_once_with(token=None, test_mode=False)
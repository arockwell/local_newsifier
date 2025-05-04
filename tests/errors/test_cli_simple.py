"""
Simplified tests for CLI error presentation utilities.
"""

import sys
from unittest.mock import Mock, patch

import pytest
import click
from click.testing import CliRunner

from src.local_newsifier.errors.service_errors import ServiceError
from src.local_newsifier.errors.cli import (
    get_error_message_template
)


@pytest.fixture
def cli_runner():
    """Create a Click CLI runner for testing."""
    return CliRunner()


class TestErrorMessageTemplates:
    """Tests for error message templates."""
    
    def test_get_error_message_template_default(self):
        """Test getting default error message templates."""
        # Get templates for standard error types
        network_template = get_error_message_template("test", "network")
        timeout_template = get_error_message_template("test", "timeout")
        unknown_template = get_error_message_template("test", "unknown")
        
        # Check that templates contain expected text
        assert "Network error" in network_template
        assert "Timeout error" in timeout_template
        assert "Error:" in unknown_template
    
    def test_get_error_message_template_service_specific(self):
        """Test getting service-specific error message templates."""
        # Get templates for service-specific error types
        apify_auth_template = get_error_message_template("apify", "authentication")
        rss_network_template = get_error_message_template("rss", "network")
        
        # Check that templates contain expected text
        assert "Apify authentication failed" in apify_auth_template
        assert "RSS feed connection error" in rss_network_template
    
    def test_get_error_message_template_fallback(self):
        """Test fallback to default template when service-specific not available."""
        # Get template for error type that doesn't have a service-specific template
        template = get_error_message_template("apify", "timeout")
        
        # Check that it falls back to the default template
        assert "Timeout error" in template
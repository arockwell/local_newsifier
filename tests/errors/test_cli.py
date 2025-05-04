"""
Tests for CLI error presentation utilities.
"""

import sys
from unittest.mock import Mock, patch

import pytest
import click
from click.testing import CliRunner

from src.local_newsifier.errors.service_errors import ServiceError
from src.local_newsifier.errors.cli import (
    handle_service_error_cli,
    get_error_message_template,
    EXIT_CODES
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


class TestCliErrorHandler:
    """Tests for the CLI error handler decorator."""
    
    def test_handle_service_error_cli_success(self, cli_runner):
        """Test that handle_service_error_cli passes through successful calls."""
        # Create a test CLI command
        @click.command()
        @handle_service_error_cli("test")
        @click.pass_context
        def test_command(ctx):
            """Test command that succeeds."""
            click.echo("Success")
        
        # Run the command
        result = cli_runner.invoke(test_command, obj={"verbose": False})
        
        # Check the result
        assert result.exit_code == 0
        assert "Success" in result.output
    
    def test_handle_service_error_cli_error(self, cli_runner):
        """Test that handle_service_error_cli handles ServiceError."""
        # Create a test CLI command that raises a ServiceError
        @click.command()
        @handle_service_error_cli("test")
        @click.pass_context
        def test_command(ctx):
            """Test command that fails with a ServiceError."""
            raise ServiceError(
                service="test",
                error_type="network",
                message="Test network error"
            )
        
        # Mock sys.exit to prevent actual exit
        with patch("sys.exit") as mock_exit:
            # Run the command
            result = cli_runner.invoke(test_command, obj={"verbose": False})
            
            # Check that sys.exit was called with the correct exit code
            mock_exit.assert_called_once_with(EXIT_CODES["network"])
        
        # Check the output
        assert "Network error" in result.output
        assert "Test network error" in result.output
        assert "Troubleshooting" in result.output
    
    def test_handle_service_error_cli_verbose(self, cli_runner):
        """Test that handle_service_error_cli includes debug info in verbose mode."""
        # Create a context with error details
        context = {"param": "value", "url": "https://example.com"}
        
        # Create a test CLI command that raises a ServiceError with context
        @click.command()
        @handle_service_error_cli("test")
        @click.pass_context
        def test_command(ctx):
            """Test command that fails with a ServiceError in verbose mode."""
            raise ServiceError(
                service="test",
                error_type="timeout",
                message="Test timeout error",
                context=context
            )
        
        # Mock sys.exit to prevent actual exit
        with patch("sys.exit"):
            # Run the command in verbose mode
            result = cli_runner.invoke(test_command, obj={"verbose": True})
        
        # Check the output
        assert "Timeout error" in result.output
        assert "Test timeout error" in result.output
        assert "Debug Information" in result.output
        assert "Service: test" in result.output
        assert "Error Type: timeout" in result.output
        assert "param: value" in result.output
        assert "url: https://example.com" in result.output
    
    def test_handle_service_error_cli_unhandled_exception(self, cli_runner):
        """Test that handle_service_error_cli handles unhandled exceptions."""
        # Create a test CLI command that raises an unhandled exception
        @click.command()
        @handle_service_error_cli("test")
        @click.pass_context
        def test_command(ctx):
            """Test command that fails with an unhandled exception."""
            raise ValueError("Unhandled error")
        
        # Mock sys.exit to prevent actual exit
        with patch("sys.exit") as mock_exit:
            # Run the command
            result = cli_runner.invoke(test_command, obj={"verbose": False})
            
            # Check that sys.exit was called with exit code 1
            mock_exit.assert_called_once_with(1)
        
        # Check the output
        assert "Unexpected error" in result.output
        assert "Unhandled error" in result.output
    
    def test_handle_service_error_cli_unhandled_exception_verbose(self, cli_runner):
        """Test that handle_service_error_cli includes traceback for unhandled exceptions in verbose mode."""
        # Create a test CLI command that raises an unhandled exception
        @click.command()
        @handle_service_error_cli("test")
        @click.pass_context
        def test_command(ctx):
            """Test command that fails with an unhandled exception in verbose mode."""
            raise ValueError("Unhandled error")
        
        # Mock sys.exit to prevent actual exit
        with patch("sys.exit"):
            # Run the command in verbose mode
            result = cli_runner.invoke(test_command, obj={"verbose": True})
        
        # Check the output
        assert "Unexpected error" in result.output
        assert "Unhandled error" in result.output
        assert "Traceback" in result.output
    
    def test_handle_service_error_cli_service_specific(self, cli_runner):
        """Test that handle_service_error_cli uses service-specific error messages."""
        # Create a test CLI command that raises a service-specific ServiceError
        @click.command()
        @handle_service_error_cli("apify")
        @click.pass_context
        def test_command(ctx):
            """Test command that fails with a service-specific ServiceError."""
            raise ServiceError(
                service="apify",
                error_type="authentication",
                message="Invalid API token"
            )
        
        # Mock sys.exit to prevent actual exit
        with patch("sys.exit"):
            # Run the command
            result = cli_runner.invoke(test_command, obj={"verbose": False})
        
        # Check the output
        assert "Apify authentication failed" in result.output
        assert "Invalid API token" in result.output
        assert "Check your Apify API token" in result.output
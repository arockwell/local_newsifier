"""
Tests for CLI error handling.
"""

import sys
from unittest.mock import Mock, patch

import pytest
import click
from click.testing import CliRunner

from src.local_newsifier.errors.error import ServiceError
from src.local_newsifier.errors.cli import handle_cli_errors


@pytest.fixture
def cli_runner():
    """Create a Click CLI runner for testing."""
    return CliRunner()


class TestCliErrorHandler:
    """Tests for CLI error handler."""
    
    def test_cli_success(self, cli_runner):
        """Test successful CLI command execution."""
        # Create test CLI command
        @click.command()
        @handle_cli_errors("test")
        def test_command():
            """Test command."""
            click.echo("Success")
        
        # Run command with mocked context
        with patch.object(click, 'get_current_context') as mock_ctx:
            # Configure mock context
            mock_ctx.return_value = Mock(obj={"verbose": False})
            
            # Run command
            result = cli_runner.invoke(test_command, catch_exceptions=False)
            
            # Check result
            assert result.exit_code == 0
            assert "Success" in result.output
    
    def test_cli_service_error(self, cli_runner):
        """Test CLI command with ServiceError."""
        # Create test CLI command
        @click.command()
        @handle_cli_errors("test")
        def test_command():
            """Test command."""
            # This bypasses sys.exit by using the CliRunner's exception handling
            raise ServiceError("test", "network", "Network error")
        
        # Run command with mocked context
        with patch.object(click, 'get_current_context') as mock_ctx:
            # Configure mock context
            mock_ctx.return_value = Mock(obj={"verbose": False})
            
            # Run command (catch_exceptions=True to handle sys.exit)
            result = cli_runner.invoke(test_command, catch_exceptions=True)
            
            # Check result contains error message
            assert "Network error" in result.output
            assert "Hint:" in result.output
            
            # CliRunner will convert sys.exit to a SystemExit exception
            # captured in exc_info
            assert result.exception
    
    def test_cli_verbose_mode(self, cli_runner):
        """Test CLI command in verbose mode."""
        # Create test CLI command
        @click.command()
        @handle_cli_errors("test")
        def test_command():
            """Test command."""
            error = ServiceError(
                "test", "auth", "Auth error", 
                context={"function": "test_command"}
            )
            raise error
        
        # Run command with mocked context
        with patch.object(click, 'get_current_context') as mock_ctx:
            # Configure mock context with verbose mode
            mock_ctx.return_value = Mock(obj={"verbose": True})
            
            # Run command
            result = cli_runner.invoke(test_command, catch_exceptions=True)
            
            # Check result contains debug info
            assert "Auth error" in result.output
            assert "Debug Information:" in result.output
            assert "service: test" in result.output
            assert "error_type: auth" in result.output
            assert "Context:" in result.output
            assert "function: test_command" in result.output
            
            # Verify exception was raised
            assert result.exception
    
    def test_cli_unhandled_exception(self, cli_runner):
        """Test CLI command with unhandled exception."""
        # Create test CLI command
        @click.command()
        @handle_cli_errors("test")
        def test_command():
            """Test command."""
            raise KeyError("Missing key")
        
        # Run command with mocked context
        with patch.object(click, 'get_current_context') as mock_ctx:
            # Configure mock context
            mock_ctx.return_value = Mock(obj={"verbose": False})
            
            # Run command
            result = cli_runner.invoke(test_command, catch_exceptions=True)
            
            # Check result
            assert "Unexpected error" in result.output
            assert "Missing key" in result.output
            
            # Verify exception was raised
            assert result.exception
    
    def test_cli_unhandled_exception_verbose(self, cli_runner):
        """Test CLI command with unhandled exception in verbose mode."""
        # Create test CLI command
        @click.command()
        @handle_cli_errors("test")
        def test_command():
            """Test command."""
            raise KeyError("Missing key")
        
        # Run command with mocked context
        with patch.object(click, 'get_current_context') as mock_ctx:
            # Configure mock context with verbose mode
            mock_ctx.return_value = Mock(obj={"verbose": True})
            
            # Run command
            result = cli_runner.invoke(test_command, catch_exceptions=True)
            
            # Check result contains traceback
            assert "Unexpected error" in result.output
            assert "Missing key" in result.output
            assert "Traceback" in result.output
            
            # Verify exception was raised
            assert result.exception
    
    def test_cli_service_specific(self, cli_runner):
        """Test CLI command with service-specific error message."""
        # Create test CLI command
        @click.command()
        @handle_cli_errors("apify")
        def test_command():
            """Test command."""
            raise ServiceError(
                service="apify",
                error_type="auth",
                message="Invalid API token"
            )
        
        # Run command with mocked context
        with patch.object(click, 'get_current_context') as mock_ctx:
            # Configure mock context
            mock_ctx.return_value = Mock(obj={"verbose": False})
            
            # Run command
            result = cli_runner.invoke(test_command, catch_exceptions=True)
            
            # Check output contains service-specific hint
            assert "Invalid API token" in result.output
            assert "API key is invalid" in result.output
            
            # Verify exception was raised
            assert result.exception
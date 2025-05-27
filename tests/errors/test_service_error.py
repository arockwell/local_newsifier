"""
Tests for ServiceError class and core error handling.
"""

import re
from datetime import datetime
from unittest.mock import Mock, patch

import pytest
import requests

from src.local_newsifier.errors.error import (ServiceError, _classify_error, handle_service_error,
                                              with_retry, with_timing)


class TestServiceError:
    """Tests for the ServiceError class."""

    @pytest.mark.parametrize(
        "service,error_type,message,transient",
        [
            ("apify", "network", "Network error", True),
            ("rss", "timeout", "Timeout error", True),
            ("web_scraper", "auth", "Authentication failed", False),
            ("unknown", "unknown", "Unknown error", False),
        ],
    )
    def test_service_error_init(self, service, error_type, message, transient):
        """Test ServiceError initialization with various parameters."""
        # Create a test original exception
        original = ValueError("Original error")

        # Create ServiceError
        error = ServiceError(
            service=service,
            error_type=error_type,
            message=message,
            original=original,
            context={"test": "value"},
        )

        # Check basic properties
        assert error.service == service
        assert error.error_type == error_type
        assert str(error) == f"{service}.{error_type}: {message}"
        assert isinstance(error.original, ValueError)
        assert str(error.original) == "Original error"
        assert error.context == {"test": "value"}
        assert error.transient == transient
        assert isinstance(error.timestamp, datetime)

        # Check additional properties
        assert error.full_type == f"{service}.{error_type}"
        assert error.exit_code > 0

    def test_to_dict(self):
        """Test converting ServiceError to dictionary."""
        error = ServiceError(
            service="test",
            error_type="network",
            message="Test error",
            original=ValueError("Original error"),
            context={"test": "value"},
        )

        error_dict = error.to_dict()

        assert error_dict["service"] == "test"
        assert error_dict["error_type"] == "network"
        assert error_dict["message"] == "test.network: Test error"
        assert "timestamp" in error_dict
        assert error_dict["transient"] is True
        assert error_dict["context"] == {"test": "value"}
        assert error_dict["original"] == "Original error"


class TestErrorClassifier:
    """Tests for error classification function."""

    @pytest.mark.parametrize(
        "exception,expected_type",
        [
            (requests.ConnectionError("Failed to connect"), "network"),
            (requests.Timeout("Request timed out"), "timeout"),
            (ValueError("Invalid JSON"), "parse"),  # Contains "JSON" so classified as parse
            (TypeError("Expected string"), "validation"),
            (KeyError("Missing key"), "unknown"),
        ],
    )
    def test_classify_by_exception_type(self, exception, expected_type):
        """Test classifying errors by exception type."""
        error_type, _ = _classify_error(exception, "test")
        assert error_type == expected_type

    def test_classify_http_errors(self):
        """Test classifying HTTP errors by status code."""
        # Create mock responses with different status codes
        responses = {
            401: Mock(status_code=401, request=Mock(url="https://api.example.com")),
            404: Mock(status_code=404, request=Mock(url="https://api.example.com")),
            429: Mock(status_code=429, request=Mock(url="https://api.example.com")),
            500: Mock(status_code=500, request=Mock(url="https://api.example.com")),
        }

        # Create exceptions with these responses
        exceptions = {
            status: requests.HTTPError(f"{status} Error", response=resp)
            for status, resp in responses.items()
        }

        # Expected error types
        expected_types = {401: "auth", 404: "not_found", 429: "rate_limit", 500: "server"}

        # Test each exception
        for status, exception in exceptions.items():
            error_type, _ = _classify_error(exception, "test")
            assert error_type == expected_types[status]

    def test_classify_parse_errors(self):
        """Test classifying parse errors."""
        exception = ValueError("JSON decode error: Unexpected token")
        error_type, _ = _classify_error(exception, "test")
        # Should detect it's a parse error from the message
        assert error_type == "parse"


class TestErrorHandlerDecorator:
    """Tests for the error handler decorator."""

    def test_handle_service_errors_success(self):
        """Test normal successful function execution."""

        @handle_service_error("test")
        def test_function():
            return "success"

        result = test_function()
        assert result == "success"

    def test_handle_service_errors_exception(self):
        """Test exception transformation."""

        # Create test function that raises exception
        @handle_service_error("test")
        def test_function():
            raise ValueError("Test error")

        # Call function and check for ServiceError
        with pytest.raises(ServiceError) as excinfo:
            test_function()

        # Check error details
        assert excinfo.value.service == "test"
        assert excinfo.value.error_type == "validation"
        assert "Test error" in str(excinfo.value)
        assert isinstance(excinfo.value.original, ValueError)

    def test_handle_http_error(self):
        """Test handling HTTP errors."""
        # Create mock response
        response = Mock(status_code=429)
        response.request = Mock(url="https://api.example.com")

        # Create test function with HTTP error
        @handle_service_error("test")
        def test_function():
            error = requests.HTTPError("429 Too Many Requests")
            error.response = response
            raise error

        # Call function and check for ServiceError
        with pytest.raises(ServiceError) as excinfo:
            test_function()

        # Check error details
        assert excinfo.value.service == "test"
        assert excinfo.value.error_type == "rate_limit"
        assert "429" in str(excinfo.value)
        assert excinfo.value.transient is True
        assert "status_code" in excinfo.value.context
        assert excinfo.value.context["status_code"] == 429

    def test_context_preservation(self):
        """Test context information is preserved."""

        # Create test function with arguments
        @handle_service_error("test")
        def test_function(arg1, arg2, kwarg1=None):
            raise ValueError("Test error")

        # Call function and check for context
        with pytest.raises(ServiceError) as excinfo:
            test_function("value1", "value2", kwarg1="key1")

        # Check context
        context = excinfo.value.context
        assert context["function"] == "test_function"
        assert len(context["args"]) == 2
        assert "value1" in context["args"][0]
        assert "value2" in context["args"][1]
        assert "kwarg1" in context["kwargs"]
        assert context["kwargs"]["kwarg1"] == "key1"


class TestRetryDecorator:
    """Tests for the retry decorator."""

    def test_retry_success(self):
        """Test retry on transient errors with eventual success."""
        # Counter to track attempts
        attempts = []

        # Create test function
        @with_retry(max_attempts=3)
        def test_function():
            attempts.append(1)
            if len(attempts) < 3:
                raise ServiceError("test", "network", "Network error")
            return "success"

        # Call function and check result
        result = test_function()

        # Check result and attempt count
        assert result == "success"
        assert len(attempts) == 3

    def test_no_retry_on_non_transient(self):
        """Test no retry on non-transient errors."""
        # Counter to track attempts
        attempts = []

        # Create test function
        @with_retry(max_attempts=3)
        def test_function():
            attempts.append(1)
            # Set transient=False manually
            error = ServiceError("test", "validation", "Validation error")
            error.transient = False
            raise error

        # Call function and check exception
        with pytest.raises(ServiceError):
            test_function()

        # Should only attempt once
        assert len(attempts) == 1

    def test_retry_exhaustion(self):
        """Test retry exhaustion with continued failure."""
        # Counter to track attempts
        attempts = []

        # Create test function that always fails
        @with_retry(max_attempts=3)
        def test_function():
            attempts.append(1)
            # Set transient=True manually
            error = ServiceError("test", "network", f"Network error {len(attempts)}")
            error.transient = True
            raise error

        # Call function and check exception
        with pytest.raises(ServiceError) as excinfo:
            test_function()

        # Should attempt max_attempts times
        assert len(attempts) == 3
        # Last error should be preserved
        assert "Network error 3" in str(excinfo.value)


class TestTimingDecorator:
    """Tests for the timing decorator."""

    @patch("time.time")
    @patch("logging.Logger.info")
    def test_timing_success(self, mock_log, mock_time):
        """Test timing for successful function."""
        # Mock time.time to return fixed values
        mock_time.side_effect = [0, 1.5]

        # Create test function
        @with_timing("test")
        def test_function():
            return "success"

        # Call function
        result = test_function()

        # Check result
        assert result == "success"

        # Check logging
        mock_log.assert_called_once()
        log_msg = mock_log.call_args[0][0]
        assert "test.test_function" in log_msg
        assert "succeeded" in log_msg
        assert "1.5" in log_msg

    @patch("time.time")
    @patch("logging.Logger.info")
    def test_timing_failure(self, mock_log, mock_time):
        """Test timing for failed function."""
        # Mock time.time to return fixed values
        mock_time.side_effect = [0, 2.5]

        # Create test function
        @with_timing("test")
        def test_function():
            raise ValueError("Test error")

        # Call function and expect exception
        with pytest.raises(ValueError):
            test_function()

        # Check logging
        mock_log.assert_called_once()
        log_msg = mock_log.call_args[0][0]
        assert "test.test_function" in log_msg
        assert "failed" in log_msg
        assert "2.5" in log_msg

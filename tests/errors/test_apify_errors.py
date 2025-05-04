"""Tests for Apify error handling components."""

import json
import logging
import pytest
from unittest.mock import MagicMock, patch

import requests
from apify_client.errors import ApifyApiError

from local_newsifier.errors.apify import (
    ApifyError,
    ApifyAuthError,
    ApifyRateLimitError,
    ApifyNetworkError,
    ApifyAPIError,
    ApifyActorError,
    ApifyDatasetError,
    ApifyDataProcessingError,
    parse_apify_error
)
from local_newsifier.errors.utils import (
    with_apify_error_handling,
    with_apify_retry,
    with_apify_timing,
    apply_full_apify_handling
)


class TestApifyErrorTypes:
    """Tests for Apify error type classes."""
    
    def test_base_error_initialization(self):
        """Test that the base ApifyError initializes correctly."""
        # Create a base error
        error = ApifyError(
            message="Test error",
            original_error=ValueError("Original error"),
            operation="test_operation",
            context={"param": "value"},
            status_code=400
        )
        
        # Verify properties
        assert str(error) == "test_operation: Test error"
        assert error.error_code in ("VALIDATION_ERROR", "APIFY_ERROR")
        assert error.status_code == 400
        assert error.context == {"param": "value"}
        assert isinstance(error.original_error, ValueError)
        
        # Verify to_dict method
        error_dict = error.to_dict()
        assert error_dict["message"] == "test_operation: Test error"
        assert error_dict["operation"] == "test_operation"
        assert error_dict["context"] == {"param": "value"}
    
    def test_auth_error(self):
        """Test AuthError initialization and defaults."""
        # Create with defaults
        error = ApifyAuthError()
        assert "Authentication or authorization error" in str(error)
        assert error.status_code == 401
        
        # Create with custom message
        error = ApifyAuthError(message="Invalid token")
        assert "Invalid token" in str(error)
    
    def test_rate_limit_error(self):
        """Test RateLimitError with retry information."""
        # Create with retry-after
        error = ApifyRateLimitError(retry_after=30)
        assert "retry after 30s" in str(error)
        assert error.retry_after == 30
        assert error.context["retry_after"] == 30
    
    def test_network_error(self):
        """Test NetworkError initialization."""
        orig_error = requests.exceptions.ConnectionError("Connection refused")
        error = ApifyNetworkError(
            original_error=orig_error,
            operation="connect_api"
        )
        assert "Network error" in str(error)
        assert error.original_error == orig_error
    
    def test_actor_error(self):
        """Test ActorError with actor ID."""
        error = ApifyActorError(
            actor_id="my-actor",
            status_code=404
        )
        assert "Error with Apify actor operation" in str(error)
        assert error.context["actor_id"] == "my-actor"
        assert error.status_code == 404
    
    def test_dataset_error(self):
        """Test DatasetError with dataset ID."""
        error = ApifyDatasetError(
            dataset_id="my-dataset",
            status_code=404
        )
        assert "Error with Apify dataset operation" in str(error)
        assert error.context["dataset_id"] == "my-dataset"
        assert error.status_code == 404
    
    def test_data_processing_error(self):
        """Test DataProcessingError initialization."""
        orig_error = json.JSONDecodeError("Invalid JSON", "{invalid}", 1)
        error = ApifyDataProcessingError(
            original_error=orig_error,
            operation="parse_response"
        )
        assert "Error processing Apify data" in str(error)
        assert error.original_error == orig_error


class TestApifyErrorParsing:
    """Tests for error parsing functionality."""
    
    def test_parse_connection_error(self):
        """Test parsing connection errors."""
        orig_error = requests.exceptions.ConnectionError("Failed to establish connection")
        result = parse_apify_error(
            error=orig_error,
            operation="test_operation",
            context={"test": "value"}
        )
        
        assert isinstance(result, ApifyNetworkError)
        assert "Network error" in str(result)
        assert result.original_error == orig_error
        assert result.context == {"test": "value"}
    
    def test_parse_timeout_error(self):
        """Test parsing timeout errors."""
        orig_error = requests.exceptions.Timeout("Request timed out")
        result = parse_apify_error(
            error=orig_error,
            operation="test_operation",
            context={}
        )
        
        assert isinstance(result, ApifyNetworkError)
        assert "Network error" in str(result)
    
    def test_parse_auth_error(self):
        """Test parsing authentication errors."""
        # Create mock ApifyApiError with status code 401
        response = MagicMock()
        response.status_code = 401
        orig_error = ApifyApiError("Unauthorized", response)
        orig_error.status_code = 401
        
        result = parse_apify_error(
            error=orig_error,
            operation="test_operation",
            context={}
        )
        
        assert isinstance(result, ApifyAuthError)
        assert "Authentication failed" in str(result)
        assert result.status_code == 401
    
    def test_parse_rate_limit_error(self):
        """Test parsing rate limit errors."""
        # Create mock ApifyApiError with status code 429
        response = MagicMock()
        response.status_code = 429
        response.headers = {"retry-after": "60"}
        orig_error = ApifyApiError("Too Many Requests", response)
        orig_error.status_code = 429
        orig_error.response = response
        
        result = parse_apify_error(
            error=orig_error,
            operation="test_operation",
            context={}
        )
        
        assert isinstance(result, ApifyRateLimitError)
        assert "Rate limit exceeded" in str(result)
        assert result.retry_after == 60
    
    def test_parse_actor_error(self):
        """Test parsing actor errors based on context."""
        # Create mock ApifyApiError with status code 404
        response = MagicMock()
        response.status_code = 404
        orig_error = ApifyApiError("Actor not found", response)
        orig_error.status_code = 404
        
        result = parse_apify_error(
            error=orig_error,
            operation="run_actor",
            context={"actor_id": "test-actor"}
        )
        
        assert isinstance(result, ApifyActorError)
        assert "Actor error" in str(result)
        assert result.context["actor_id"] == "test-actor"
    
    def test_parse_dataset_error(self):
        """Test parsing dataset errors based on context."""
        # Create mock ApifyApiError with status code 404
        response = MagicMock()
        response.status_code = 404
        orig_error = ApifyApiError("Dataset not found", response)
        orig_error.status_code = 404
        
        result = parse_apify_error(
            error=orig_error,
            operation="get_dataset",
            context={"dataset_id": "test-dataset"}
        )
        
        assert isinstance(result, ApifyDatasetError)
        assert "Dataset error" in str(result)
        assert result.context["dataset_id"] == "test-dataset"
    
    def test_parse_data_processing_error(self):
        """Test parsing data processing errors."""
        orig_error = ValueError("Failed to parse JSON response")
        result = parse_apify_error(
            error=orig_error,
            operation="parse_response",
            context={}
        )
        
        # Should default to base error for ValueErrors not related to parsing
        assert isinstance(result, ApifyError)
        
        # But should detect parsing errors
        orig_error = ValueError("Error parsing JSON response")
        result = parse_apify_error(
            error=orig_error,
            operation="parse_response",
            context={}
        )
        
        assert isinstance(result, ApifyDataProcessingError)
        assert "Data processing error" in str(result)


class TestErrorHandlingDecorator:
    """Tests for the error handling decorator."""
    
    def test_error_handling_no_error(self):
        """Test that the decorator passes through when no error occurs."""
        @with_apify_error_handling(operation_name="test_op")
        def test_func(param1, param2):
            return f"{param1}-{param2}"
        
        result = test_func("a", "b")
        assert result == "a-b"
    
    def test_error_handling_with_apify_api_error(self):
        """Test handling of ApifyApiError."""
        # Create mock ApifyApiError with status code 401
        response = MagicMock()
        response.status_code = 401
        api_error = ApifyApiError("Unauthorized", response)
        api_error.status_code = 401
        
        @with_apify_error_handling(operation_name="test_auth")
        def test_func():
            raise api_error
        
        # Verify the error is transformed
        with pytest.raises(ApifyAuthError) as excinfo:
            test_func()
        
        assert "Authentication failed" in str(excinfo.value)
        assert excinfo.value.original_error == api_error
    
    def test_error_handling_with_network_error(self):
        """Test handling of network errors."""
        network_error = requests.exceptions.ConnectionError("Connection refused")
        
        @with_apify_error_handling()
        def test_func():
            raise network_error
        
        # Verify the error is transformed
        with pytest.raises(ApifyNetworkError) as excinfo:
            test_func()
        
        assert "Network error" in str(excinfo.value)
        assert excinfo.value.original_error == network_error
    
    def test_error_handling_preserves_context(self):
        """Test that the decorator preserves argument context."""
        @with_apify_error_handling(include_args=True)
        def test_func(param1, param2, token=None):
            raise ValueError("Test error")
        
        # Verify context includes function arguments except token
        with pytest.raises(ApifyError) as excinfo:
            test_func("value1", "value2", token="secret")
        
        assert "param1" in excinfo.value.context
        assert excinfo.value.context["param1"] == "value1"
        assert "param2" in excinfo.value.context
        assert "token" not in excinfo.value.context  # Token should be excluded
    
    def test_error_handling_for_methods(self):
        """Test the decorator works properly with class methods."""
        class TestClass:
            @with_apify_error_handling()
            def test_method(self, param):
                raise ValueError(f"Error with {param}")
        
        instance = TestClass()
        
        with pytest.raises(ApifyError) as excinfo:
            instance.test_method("test_value")
        
        assert "Error with test_value" in str(excinfo.value)
        assert excinfo.value.context.get("param") == "test_value"


class TestRetryDecorator:
    """Tests for the retry decorator."""
    
    def test_retry_network_errors(self):
        """Test retrying on network errors."""
        mock_func = MagicMock()
        mock_func.side_effect = [
            requests.exceptions.ConnectionError("Connection refused"),
            "success"
        ]
        
        @with_apify_retry(max_attempts=2, min_wait=0.1, max_wait=0.1)
        def test_func():
            return mock_func()
        
        # Should retry once and then succeed
        result = test_func()
        assert result == "success"
        assert mock_func.call_count == 2
    
    def test_retry_rate_limit_errors(self):
        """Test retrying on rate limit errors."""
        mock_func = MagicMock()
        mock_func.side_effect = [
            ApifyRateLimitError(retry_after=0.1),
            "success"
        ]
        
        @with_apify_retry(max_attempts=2, min_wait=0.1, max_wait=0.1)
        def test_func():
            return mock_func()
        
        # Should retry once and then succeed
        result = test_func()
        assert result == "success"
        assert mock_func.call_count == 2
    
    def test_max_retries_exceeded(self):
        """Test that retries stop after max attempts."""
        mock_func = MagicMock()
        mock_func.side_effect = requests.exceptions.ConnectionError("Connection refused")
        
        @with_apify_retry(max_attempts=3, min_wait=0.1, max_wait=0.1)
        def test_func():
            return mock_func()
        
        # Should retry twice (3 total attempts) and then fail
        with pytest.raises(requests.exceptions.ConnectionError):
            test_func()
        
        assert mock_func.call_count == 3
    
    def test_retry_disabled_for_error_type(self):
        """Test that retries don't happen for non-specified error types."""
        mock_func = MagicMock()
        mock_func.side_effect = ApifyAuthError()
        
        @with_apify_retry(
            retry_network_errors=True,
            retry_rate_limit_errors=True,
            retry_other_errors=False  # Don't retry auth errors
        )
        def test_func():
            return mock_func()
        
        # Should not retry and fail immediately
        with pytest.raises(ApifyAuthError):
            test_func()
        
        assert mock_func.call_count == 1


class TestTimingDecorator:
    """Tests for the timing decorator."""
    
    def test_timing_success(self, caplog):
        """Test timing for successful operations."""
        caplog.set_level(logging.DEBUG)
        
        @with_apify_timing(operation_name="test_op")
        def test_func():
            return "success"
        
        result = test_func()
        
        assert result == "success"
        assert "Apify operation 'test_op' took" in caplog.text
    
    def test_timing_error(self, caplog):
        """Test timing for operations that raise errors."""
        caplog.set_level(logging.DEBUG)
        
        @with_apify_timing(operation_name="error_op")
        def test_func():
            raise ValueError("Test error")
        
        with pytest.raises(ValueError):
            test_func()
        
        assert "Apify operation 'error_op' failed after" in caplog.text


class TestFullErrorHandling:
    """Tests for combined error handling decorator."""
    
    def test_apply_full_handling(self):
        """Test that the full handling decorator applies all components."""
        mock_func = MagicMock()
        
        # Set up mock to succeed after one retry
        network_error = requests.exceptions.ConnectionError("Connection refused")
        mock_func.side_effect = [
            network_error,
            "success"
        ]
        
        # Apply the combined decorator
        @apply_full_apify_handling(
            operation_name="test_operation",
            max_attempts=2,
            min_wait=0.1,
            max_wait=0.1
        )
        def test_func(param):
            return mock_func(param)
        
        # Should handle the error, retry, and succeed
        result = test_func("test_value")
        
        assert result == "success"
        assert mock_func.call_count == 2
        mock_func.assert_called_with("test_value")
    
    def test_full_handling_preserves_errors(self):
        """Test that the full handling decorator preserves error transformations."""
        # Create mock ApifyApiError with status code 401
        response = MagicMock()
        response.status_code = 401
        api_error = ApifyApiError("Unauthorized", response)
        api_error.status_code = 401
        
        @apply_full_apify_handling(
            retry_other_errors=False  # Don't retry auth errors
        )
        def test_func():
            raise api_error
        
        # Should transform to ApifyAuthError but not retry
        with pytest.raises(ApifyAuthError) as excinfo:
            test_func()
        
        assert "Authentication failed" in str(excinfo.value)
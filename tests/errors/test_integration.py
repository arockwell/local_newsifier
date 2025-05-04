"""
Integration tests for the error handling framework.
"""

import json
from unittest.mock import Mock, patch

import pytest
import requests

from src.local_newsifier.errors.service_errors import ServiceError
from src.local_newsifier.errors.decorators import (
    handle_apify_errors,
    retry_apify_calls,
    time_service_calls,
    handle_apify
)


class TestServiceErrorIntegration:
    """Integration tests for ServiceError handling."""
    
    def test_error_handler_integration(self):
        """Test an end-to-end scenario with a service call that fails."""
        # Create a mock response with a 429 status code
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.raise_for_status.side_effect = requests.HTTPError(
            "429 Too Many Requests", 
            response=mock_response
        )
        
        # Create a mock requests session
        mock_session = Mock()
        mock_session.get.return_value = mock_response
        
        # Create a service function that uses requests
        @handle_apify_errors
        def fetch_data(url):
            """Fetch data from a URL."""
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        
        # Patch the requests.get function to use our mock
        with patch("requests.get", return_value=mock_response):
            # Call the function and check the exception
            with pytest.raises(ServiceError) as excinfo:
                fetch_data("https://api.example.com/data")
            
            # Check the exception
            assert excinfo.value.service == "apify"
            assert excinfo.value.error_type == "rate_limit"
            assert "429" in str(excinfo.value)
            assert excinfo.value.is_transient is True
    
    def test_combined_decorator_integration(self):
        """Test the combined decorator in an end-to-end scenario."""
        # Create a counter to track number of attempts
        attempt_counter = 0
        
        # Create a service function that fails twice then succeeds
        @handle_apify
        def fetch_data(url):
            """Fetch data from a URL with full error handling."""
            nonlocal attempt_counter
            attempt_counter += 1
            
            if attempt_counter < 3:
                # Simulate a network error for the first two attempts
                raise requests.ConnectionError("Connection failed")
            
            # Succeed on the third attempt
            return {"success": True, "data": "test data"}
        
        # Call the function
        result = fetch_data("https://api.example.com/data")
        
        # Check the result
        assert result["success"] is True
        assert result["data"] == "test data"
        # Check that it retried the correct number of times
        assert attempt_counter == 3
    
    def test_error_chain_preservation(self):
        """Test that the original error information is preserved in the service error."""
        # Create a detailed HTTP error
        original_error = requests.HTTPError(
            "404 Not Found: The requested resource was not found.",
            response=Mock(
                status_code=404,
                url="https://api.example.com/missing"
            )
        )
        
        # Create a service function that raises the HTTP error
        @handle_apify_errors
        def fetch_data():
            """Fetch data from an API."""
            raise original_error
        
        # Call the function and check the exception
        with pytest.raises(ServiceError) as excinfo:
            fetch_data()
        
        # Check the exception
        assert excinfo.value.service == "apify"
        assert excinfo.value.error_type == "not_found"
        assert excinfo.value.original == original_error
        assert "The requested resource was not found" in str(excinfo.value.original)
    
    def test_non_exception_retry(self):
        """Test retry logic with serviceError directly."""
        # Create a counter to track number of attempts
        attempt_counter = 0
        
        # Create a function that returns transient ServiceError for two attempts, then succeeds
        @retry_apify_calls
        def process_data():
            """Process data with retry logic."""
            nonlocal attempt_counter
            attempt_counter += 1
            
            if attempt_counter < 3:
                # Return a transient ServiceError for first two attempts
                raise ServiceError(
                    service="apify",
                    error_type="network",
                    message=f"Network error (attempt {attempt_counter})",
                    is_transient=True
                )
            
            # Succeed on the third attempt
            return "success"
        
        # Call the function
        result = process_data()
        
        # Check the result
        assert result == "success"
        # Check that it retried the correct number of times
        assert attempt_counter == 3
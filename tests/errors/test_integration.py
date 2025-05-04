"""
Integration tests for error handling.
"""

from unittest.mock import Mock, patch

import pytest
import requests

from src.local_newsifier.errors.error import ServiceError
from src.local_newsifier.errors.handlers import handle_apify


class TestErrorHandlingIntegration:
    """Integration tests for error handling."""
    
    def test_apify_network_error(self):
        """Test handling network errors in Apify service."""
        # Create mock service class
        class ApifyService:
            @handle_apify
            def fetch_data(self, url):
                """Fetch data from Apify API."""
                raise requests.ConnectionError("Failed to connect")
        
        # Create service and call method
        service = ApifyService()
        
        # Call method and check error
        with pytest.raises(ServiceError) as excinfo:
            service.fetch_data("https://example.com")
        
        # Check error details
        assert excinfo.value.service == "apify"
        assert excinfo.value.error_type == "network"
        assert "Failed to connect" in str(excinfo.value)
        assert excinfo.value.transient is True
    
    def test_retry_behavior(self):
        """Test retry behavior with transient errors."""
        # Create mock for counting calls
        mock_fn = Mock()
        mock_fn.side_effect = [
            requests.ConnectionError("Failed on first attempt"),
            requests.ConnectionError("Failed on second attempt"),
            "success"
        ]
        
        # Create a service method with retry
        class TestService:
            @handle_apify
            def fetch_with_retry(self):
                """Test method with retry."""
                return mock_fn()
        
        # Call method
        service = TestService()
        result = service.fetch_with_retry()
        
        # Check result and call count
        assert result == "success"
        assert mock_fn.call_count == 3
    
    def test_error_context_preservation(self):
        """Test context preservation in nested calls."""
        # Create service with nested calls
        class TestService:
            @handle_apify
            def outer_method(self, param):
                """Outer method that calls inner method."""
                return self.inner_method(param)
            
            def inner_method(self, param):
                """Inner method that raises error."""
                if param == "error":
                    # This will be a validation error
                    raise ValueError("Invalid parameter")
                return "success"
        
        # Create service and call method
        service = TestService()
        
        # Call with error parameter
        with pytest.raises(ServiceError) as excinfo:
            service.outer_method("error")
        
        # Check error details
        assert excinfo.value.service == "apify"
        assert excinfo.value.error_type == "validation"
        assert "Invalid parameter" in str(excinfo.value)
        
        # Check context has outer method info
        assert excinfo.value.context["function"] == "outer_method"
        assert "error" in str(excinfo.value.context["args"])
    
    def test_http_status_classification(self):
        """Test HTTP status code classification."""
        # Create service with different HTTP errors
        class ApiService:
            @handle_apify
            def call_api(self, status_code):
                """Call API with specified status code."""
                response = Mock(status_code=status_code)
                response.request = Mock(url="https://api.example.com")
                
                error = requests.HTTPError(f"{status_code} Error")
                error.response = response
                raise error
        
        # Create service
        service = ApiService()
        
        # Test different status codes
        status_error_map = {
            401: "auth",
            404: "not_found",
            429: "rate_limit",
            500: "server",
            503: "server"
        }
        
        # Test each status code
        for status, expected_type in status_error_map.items():
            with pytest.raises(ServiceError) as excinfo:
                service.call_api(status)
            
            # Check error type
            assert excinfo.value.error_type == expected_type
            # Check status in context
            assert excinfo.value.context["status_code"] == status
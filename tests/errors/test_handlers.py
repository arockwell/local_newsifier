"""
Tests for service handlers and combined decorators.
"""

from unittest.mock import Mock, patch

import pytest

from local_newsifier.errors.error import ServiceError
from local_newsifier.errors.handlers import (
    create_service_handler,
    handle_apify,
    handle_web_scraper
)


class TestServiceHandler:
    """Tests for service handler factory."""
    
    def test_create_service_handler(self):
        """Test creating a service handler."""
        # Create handler
        handler = create_service_handler("test")
        
        # Check it's callable
        assert callable(handler)
        
        # Create a test function
        @handler
        def test_function():
            return "success"
        
        # Check decorated function still works
        assert test_function() == "success"
    
    def test_create_service_handler_no_retry(self):
        """Test creating a service handler with no retry."""
        # Create handler without retry
        handler = create_service_handler("test", retry_attempts=None)
        
        # Create test function that raises transient error
        @handler
        def test_function():
            raise ServiceError("test", "network", "Network error")
        
        # Call function and check error
        with pytest.raises(ServiceError):
            test_function()
    
    def test_create_service_handler_parameters(self):
        """Test creating a service handler with parameters."""
        # Create a handler with retry
        handler_with_retry = create_service_handler("test", retry_attempts=3)
        
        # Create a handler without retry
        handler_without_retry = create_service_handler("test", retry_attempts=None)
        
        # Apply to test functions
        @handler_with_retry
        def test_function_with_retry():
            return "with_retry"
            
        @handler_without_retry
        def test_function_without_retry():
            return "without_retry"
        
        # Check functions still work
        assert test_function_with_retry() == "with_retry"
        assert test_function_without_retry() == "without_retry"
    
    def test_service_handler_error_handling(self):
        """Test service handler error transformation."""
        # Create test function
        @handle_apify
        def test_function():
            raise ValueError("Test error")
        
        # Call function and check error
        with pytest.raises(ServiceError) as excinfo:
            test_function()
        
        # Check error
        assert excinfo.value.service == "apify"
        assert "Test error" in str(excinfo.value)
    

# We've removed the TestErrorMessages class since get_error_message 
# doesn't exist in our new implementation. Error messages are now 
# handled by service-specific functions like get_rss_error_message.
"""
Tests for service handlers and combined decorators.
"""

from unittest.mock import Mock, patch

import pytest

from src.local_newsifier.errors.error import ServiceError
from src.local_newsifier.errors.handlers import (
    create_service_handler,
    handle_apify, 
    handle_rss,
    get_error_message
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
    
    def test_create_service_handler_no_timing(self):
        """Test creating a service handler with no timing."""
        # Mock timing decorator to verify it's not called
        with patch("src.local_newsifier.errors.handlers.with_timing") as mock_timing:
            # Create handler without timing
            handler = create_service_handler("test", include_timing=False)
            
            # Apply to test function
            @handler
            def test_function():
                return "success"
            
            # Check function still works
            assert test_function() == "success"
            
            # Verify timing decorator wasn't used
            mock_timing.assert_not_called()
    
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
    

class TestErrorMessages:
    """Tests for error message handling."""
    
    @pytest.mark.parametrize("service,error_type,expected_text", [
        # Service-specific messages
        ("apify", "auth", "API key is invalid"),
        ("rss", "network", "Could not connect to RSS feed"),
        ("web_scraper", "parse", "Could not extract content"),
        
        # Generic fallbacks
        ("unknown_service", "network", "Network connectivity issue"),
        ("apify", "timeout", "Request timed out"),
        ("rss", "unknown", "Unknown error occurred")
    ])
    def test_get_error_message(self, service, error_type, expected_text):
        """Test getting error messages for various services and types."""
        message = get_error_message(service, error_type)
        assert expected_text in message
"""
Tests for RSS-specific error handling.
"""

import pytest
from unittest.mock import Mock, patch
import requests
from xml.etree.ElementTree import ParseError

from local_newsifier.errors.error import ServiceError
from local_newsifier.errors.rss import (
    handle_rss_service, 
    handle_rss_cli,
    get_rss_error_message,
    _classify_rss_error
)
from local_newsifier.tools.rss_parser import parse_rss_feed


class TestRSSErrorHandling:
    """Tests for RSS error handling."""
    
    def test_rss_error_classification(self):
        """Test RSS-specific error classification."""
        # XML parsing error
        xml_error = ParseError("XML syntax error")
        error_type, _ = _classify_rss_error(xml_error)
        assert error_type == "xml_parse"
        
        # Feed format error
        format_error = ValueError("No entries found in feed")
        error_type, _ = _classify_rss_error(format_error)
        assert error_type == "feed_format"
        
        # URL error
        url_error = ValueError("invalid url")
        error_type, _ = _classify_rss_error(url_error)
        assert error_type == "url"
        
        # Encoding error
        encoding_error = UnicodeDecodeError("utf-8", b"", 0, 1, "invalid encoding")
        error_type, _ = _classify_rss_error(encoding_error)
        assert error_type == "encoding"
    
    def test_get_rss_error_message(self):
        """Test getting RSS-specific error messages."""
        # Check specific RSS error messages
        assert "feed may have syntax errors" in get_rss_error_message("xml_parse")
        assert "Required elements are missing" in get_rss_error_message("feed_validation")
        assert "Check the URL format" in get_rss_error_message("url")
        
        # Check generic fallback
        assert "An error occurred" in get_rss_error_message("unknown_type")
    
    @patch("requests.get")
    def test_rss_service_network_error(self, mock_get):
        """Test handling of network errors."""
        # Mock a connection error
        mock_get.side_effect = requests.ConnectionError("Failed to connect")
        
        # Call the decorated function
        with pytest.raises(ServiceError) as excinfo:
            parse_rss_feed("http://example.com/rss")
        
        # Check the error
        assert excinfo.value.service == "rss"
        assert excinfo.value.error_type == "network"
        assert "Failed to connect" in str(excinfo.value)
        assert excinfo.value.transient is True  # Network errors are transient
    
    @patch("requests.get")
    def test_rss_service_timeout_error(self, mock_get):
        """Test handling of timeout errors."""
        # Mock a timeout error
        mock_get.side_effect = requests.Timeout("Request timed out")
        
        # Call the decorated function
        with pytest.raises(ServiceError) as excinfo:
            parse_rss_feed("http://example.com/rss")
        
        # Check the error
        assert excinfo.value.service == "rss"
        assert excinfo.value.error_type == "timeout"
        assert "timed out" in str(excinfo.value)
        assert excinfo.value.transient is True  # Timeout errors are transient
    
    @patch("requests.get")
    def test_rss_service_not_found_error(self, mock_get):
        """Test handling of 404 errors."""
        # Mock a 404 response
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("404 Client Error")
        mock_get.return_value = mock_response
        
        # Call the decorated function
        with pytest.raises(ServiceError) as excinfo:
            parse_rss_feed("http://example.com/rss")
        
        # Check the error
        assert excinfo.value.service == "rss"
        assert excinfo.value.error_type == "not_found"
        assert "404" in str(excinfo.value)
        assert excinfo.value.transient is False  # Not found errors are not transient
    
    @patch("requests.get")
    def test_rss_service_xml_parse_error(self, mock_get):
        """Test handling of XML parsing errors."""
        # Mock a successful response with invalid XML
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.content = b"<invalid>xml</notclosed>"
        mock_get.return_value = mock_response
        
        # Call the decorated function
        with pytest.raises(ServiceError) as excinfo:
            parse_rss_feed("http://example.com/rss")
        
        # Check the error
        assert excinfo.value.service == "rss"
        # Error type could be xml_parse, parse, or validation based on implementation
        assert excinfo.value.error_type in ["xml_parse", "parse", "validation"]
        assert "XML" in str(excinfo.value) or "xml" in str(excinfo.value).lower()
        assert excinfo.value.transient is False  # Parse errors are not transient
    
    @patch("requests.get")
    def test_rss_service_feed_format_error(self, mock_get):
        """Test handling of feed format errors."""
        # Mock a successful response with valid XML but invalid feed format
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.content = b"<root><item>This is not a proper RSS feed</item></root>"
        mock_get.return_value = mock_response
        
        # Call the decorated function
        with pytest.raises(ServiceError) as excinfo:
            parse_rss_feed("http://example.com/rss")
        
        # Check the error
        assert excinfo.value.service == "rss"
        assert "feed_format" in excinfo.value.error_type or "validation" in excinfo.value.error_type
        assert "feed" in str(excinfo.value).lower()
        assert excinfo.value.transient is False
    
    def test_rss_decorator_function(self):
        """Test the RSS service decorator on a function."""
        @handle_rss_service
        def test_function(param):
            if param == "network":
                raise requests.ConnectionError("Network error")
            elif param == "xml":
                raise ParseError("XML error")
            elif param == "value":
                raise ValueError("Value error")
            return "success"
        
        # Test successful call
        assert test_function("success") == "success"
        
        # Test different error types
        with pytest.raises(ServiceError) as excinfo:
            test_function("network")
        assert excinfo.value.error_type == "network"
        
        with pytest.raises(ServiceError) as excinfo:
            test_function("xml")
        # Error type could be parse, xml_parse, validation, or unknown
        assert excinfo.value.error_type in ["parse", "xml_parse", "validation", "unknown"]
        
        with pytest.raises(ServiceError) as excinfo:
            test_function("value")
        assert excinfo.value.error_type == "validation"


class TestRSSCLIErrorHandling:
    """Tests for RSS CLI error handling."""
    
    @patch("click.get_current_context")
    @patch("click.secho")
    @patch("click.echo")
    def test_rss_cli_decorator(self, mock_echo, mock_secho, mock_context):
        """Test the RSS CLI decorator."""
        # Mock context
        mock_ctx = Mock()
        mock_ctx.obj = {"verbose": True}
        mock_context.return_value = mock_ctx
        
        # Create a test function with the decorator
        @handle_rss_cli
        def test_cli_function(param):
            if param == "error":
                raise ServiceError(
                    service="rss",
                    error_type="network",
                    message="Test network error",
                    context={"param": param}
                )
            return "success"
        
        # Test successful call
        assert test_cli_function("success") == "success"
        
        # Test error case
        with pytest.raises(SystemExit):
            test_cli_function("error")
        
        # Check that appropriate output was generated with the new user-friendly hint
        # The message now includes a hint from RSS_ERROR_MESSAGES
        mock_secho.assert_called_with(
            "Hint: Could not connect to RSS feed. Check the feed URL and your internet connection.",
            fg="yellow", 
            err=True
        )
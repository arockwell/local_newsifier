"""
Tests for the ServiceError class and related functionality.
"""

import re
from datetime import datetime
from unittest.mock import Mock, patch

import pytest
import requests

from src.local_newsifier.errors.service_errors import ServiceError


class TestServiceError:
    """Tests for the ServiceError class."""
    
    def test_service_error_init(self):
        """Test initializing a ServiceError."""
        error = ServiceError(
            service="test",
            error_type="network",
            message="Test error",
            original=ValueError("Original error"),
            context={"test": "value"},
            is_transient=True
        )
        
        assert error.service == "test"
        assert error.error_type == "network"
        assert str(error) == "test.network: Test error"
        assert isinstance(error.original, ValueError)
        assert str(error.original) == "Original error"
        assert error.context == {"test": "value"}
        assert error.is_transient is True
        assert isinstance(error.timestamp, datetime)
    
    def test_full_type_property(self):
        """Test the full_type property."""
        error = ServiceError(
            service="test",
            error_type="network",
            message="Test error"
        )
        
        assert error.full_type == "test.network"
    
    def test_to_dict(self):
        """Test converting a ServiceError to a dictionary."""
        original = ValueError("Original error")
        error = ServiceError(
            service="test",
            error_type="network",
            message="Test error",
            original=original,
            context={"test": "value"},
            is_transient=True
        )
        
        error_dict = error.to_dict()
        
        assert error_dict["service"] == "test"
        assert error_dict["error_type"] == "network"
        assert error_dict["full_type"] == "test.network"
        assert "message" in error_dict
        assert "timestamp" in error_dict
        assert error_dict["is_transient"] is True
        assert error_dict["context"] == {"test": "value"}
        assert error_dict["original_error"] == "Original error"
        assert error_dict["original_type"] == "ValueError"
    
    def test_to_dict_no_original(self):
        """Test converting a ServiceError with no original error to a dictionary."""
        error = ServiceError(
            service="test",
            error_type="network",
            message="Test error"
        )
        
        error_dict = error.to_dict()
        
        assert "original_error" in error_dict
        assert error_dict["original_error"] is None
        assert "original_type" in error_dict
        assert error_dict["original_type"] is None
    
    def test_repr(self):
        """Test the __repr__ method."""
        error = ServiceError(
            service="test",
            error_type="network",
            message="Test error",
            is_transient=True
        )
        
        repr_str = repr(error)
        
        assert "ServiceError" in repr_str
        assert "service='test'" in repr_str
        assert "error_type='network'" in repr_str
        assert "is_transient=True" in repr_str
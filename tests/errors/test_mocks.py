"""
Mock tools for error handling tests.

This module provides mock objects and helpers for error handling tests.
"""

import pytest
from unittest.mock import patch, Mock

from local_newsifier.errors.error import ServiceError


class MockResponse:
    """Mock requests Response object.
    
    This class provides a mock for testing HTTP responses and errors.
    """
    
    def __init__(self, status_code=200, content=None, raise_error=False, error_msg=None):
        self.status_code = status_code
        self.content = content or b"Mock response content"
        self.request = Mock()
        self.request.url = "http://example.com/mock"
        self._raise_error = raise_error
        self._error_msg = error_msg
        
    def raise_for_status(self):
        """Simulate the raise_for_status method of a requests Response."""
        if self._raise_error:
            import requests
            if 400 <= self.status_code < 500:
                if self.status_code == 404:
                    raise requests.HTTPError(f"404 Client Error: Not Found for url: {self.request.url}")
                else:
                    raise requests.HTTPError(f"{self.status_code} Client Error")
            elif 500 <= self.status_code < 600:
                raise requests.HTTPError(f"{self.status_code} Server Error")
            elif self._error_msg:
                raise requests.RequestException(self._error_msg)


@pytest.fixture
def patch_service_error_class():
    """Patch the ServiceError class to make it testable.
    
    This fixture adds an __eq__ method to ServiceError for easier assertions.
    """
    original_eq = getattr(ServiceError, "__eq__", None)
    
    def eq_method(self, other):
        if not isinstance(other, ServiceError):
            return False
        return (self.service == other.service and 
                self.error_type == other.error_type and
                str(self) == str(other))
    
    ServiceError.__eq__ = eq_method
    yield
    if original_eq:
        ServiceError.__eq__ = original_eq
    else:
        delattr(ServiceError, "__eq__")


@pytest.fixture
def expect_service_error():
    """Fixture to expect a ServiceError with specific attributes.
    
    This fixture simplifies testing for specific ServiceError types.
    """
    def _expect_error(service, error_type):
        def _check_error(error):
            return (isinstance(error, ServiceError) and
                    error.service == service and
                    error.error_type == error_type)
        return _check_error
    return _expect_error
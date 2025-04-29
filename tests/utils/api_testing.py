"""API testing utilities.

This module provides helpers for testing API endpoints with FastAPI's TestClient.
"""

from fastapi.testclient import TestClient
from typing import Dict, Any, Optional, List, Union
import json
import pytest
from datetime import datetime, timedelta

# Try to import app from the API module
try:
    from local_newsifier.api.main import app
except ImportError:
    # Create a placeholder if the app is not available
    # This allows the module to be imported even if FastAPI is not used
    from fastapi import FastAPI
    app = FastAPI()

@pytest.fixture
def api_client():
    """Provide a TestClient instance for API testing."""
    return TestClient(app)

def create_test_token(user_id: int = 1, 
                      expiration_delta: timedelta = timedelta(hours=1), 
                      secret_key: str = "test_secret") -> str:
    """Create a test JWT token for authentication.
    
    Args:
        user_id: User ID to encode in the token
        expiration_delta: Token expiration time
        secret_key: Secret key to sign the token
        
    Returns:
        JWT token string
    """
    try:
        # Try to import JWT functions
        from jose import jwt
        
        payload = {
            "sub": str(user_id),
            "exp": datetime.utcnow() + expiration_delta,
            "iat": datetime.utcnow(),
        }
        
        return jwt.encode(payload, secret_key, algorithm="HS256")
    except ImportError:
        # Return a dummy token if JWT support is not available
        return f"test_token_{user_id}"

class ApiTestHelper:
    """Helper class for API testing with common assertions."""
    
    def __init__(self, client: TestClient):
        """Initialize with a test client."""
        self.client = client
    
    def get(self, url: str, auth_token: Optional[str] = None, 
            expected_status: int = 200) -> Dict[str, Any]:
        """Make a GET request with optional authentication.
        
        Args:
            url: API endpoint URL
            auth_token: Authentication token
            expected_status: Expected HTTP status code
            
        Returns:
            JSON response or None for non-2xx responses
        """
        headers = {}
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"
            
        response = self.client.get(url, headers=headers)
        assert response.status_code == expected_status, f"Expected status {expected_status}, got {response.status_code}: {response.text}"
        
        return response.json() if response.status_code < 300 else None
    
    def post(self, url: str, data: Dict[str, Any], auth_token: Optional[str] = None,
             expected_status: int = 200) -> Dict[str, Any]:
        """Make a POST request with optional authentication.
        
        Args:
            url: API endpoint URL
            data: Data to send in the request body
            auth_token: Authentication token
            expected_status: Expected HTTP status code
            
        Returns:
            JSON response or None for non-2xx responses
        """
        headers = {}
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"
            
        response = self.client.post(url, json=data, headers=headers)
        assert response.status_code == expected_status, f"Expected status {expected_status}, got {response.status_code}: {response.text}"
        
        return response.json() if response.status_code < 300 else None
    
    def put(self, url: str, data: Dict[str, Any], auth_token: Optional[str] = None,
            expected_status: int = 200) -> Dict[str, Any]:
        """Make a PUT request with optional authentication.
        
        Args:
            url: API endpoint URL
            data: Data to send in the request body
            auth_token: Authentication token
            expected_status: Expected HTTP status code
            
        Returns:
            JSON response or None for non-2xx responses
        """
        headers = {}
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"
            
        response = self.client.put(url, json=data, headers=headers)
        assert response.status_code == expected_status, f"Expected status {expected_status}, got {response.status_code}: {response.text}"
        
        return response.json() if response.status_code < 300 else None
    
    def delete(self, url: str, auth_token: Optional[str] = None,
               expected_status: int = 204) -> None:
        """Make a DELETE request with optional authentication.
        
        Args:
            url: API endpoint URL
            auth_token: Authentication token
            expected_status: Expected HTTP status code
        """
        headers = {}
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"
            
        response = self.client.delete(url, headers=headers)
        assert response.status_code == expected_status, f"Expected status {expected_status}, got {response.status_code}: {response.text}"
    
    def assert_json_structure(self, data: Dict[str, Any], expected_keys: List[str]):
        """Assert that a JSON response has the expected structure.
        
        Args:
            data: JSON data
            expected_keys: List of keys to check
        """
        for key in expected_keys:
            assert key in data, f"Expected key '{key}' not found in response: {data}"
    
    def assert_paginated_response(self, data: Dict[str, Any], 
                                 expected_item_count: Optional[int] = None,
                                 expected_total: Optional[int] = None):
        """Assert that a response has the expected pagination structure.
        
        Args:
            data: JSON data
            expected_item_count: Expected number of items in the page
            expected_total: Expected total number of items
        """
        # Check pagination structure
        self.assert_json_structure(data, ["items", "total", "page", "size"])
        
        # Check item count if provided
        if expected_item_count is not None:
            assert len(data["items"]) == expected_item_count, f"Expected {expected_item_count} items, got {len(data['items'])}"
        
        # Check total if provided
        if expected_total is not None:
            assert data["total"] == expected_total, f"Expected total {expected_total}, got {data['total']}"

@pytest.fixture
def api_helper(api_client):
    """Provide an ApiTestHelper instance for API testing."""
    return ApiTestHelper(api_client)

@pytest.fixture
def auth_token():
    """Provide an authentication token for testing."""
    return create_test_token()

# Schema validation helpers

def assert_fields_match(data: Dict[str, Any], schema_class: Any):
    """Assert that a data object matches a schema's fields.
    
    Args:
        data: Data to validate
        schema_class: Pydantic model class
    """
    try:
        # Validate using the schema
        schema_class(**data)
    except Exception as e:
        pytest.fail(f"Data doesn't match schema: {e}")

@pytest.fixture
def schema_validator():
    """Provide a schema validation function."""
    return assert_fields_match

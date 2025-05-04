"""
Tests for database error handling functionality.
"""

import pytest
from unittest.mock import Mock, patch
from sqlalchemy.exc import IntegrityError, NoResultFound, SQLAlchemyError, DisconnectionError
from sqlalchemy.orm.exc import MultipleResultsFound

from local_newsifier.errors import ServiceError, handle_database
from local_newsifier.errors.error import _classify_error


class TestDatabaseErrorClassification:
    """Test suite for database error classification."""
    
    def test_integrity_error_classification(self):
        """Test that IntegrityError is classified correctly."""
        # Create a real IntegrityError with unique constraint message
        error = IntegrityError("statement", {}, "unique constraint violation")
        
        # Classify the error
        error_type, message = _classify_error(error, "database")
        
        # Check classification
        assert error_type == "integrity"
        assert "Unique constraint violation" in message
        
        # Foreign key constraint
        error = IntegrityError("statement", {}, "foreign key constraint violation")
        error_type, message = _classify_error(error, "database")
        assert error_type == "integrity"
        assert "Foreign key constraint violation" in message
        
        # Generic integrity error
        error = IntegrityError("statement", {}, "some other constraint")
        error_type, message = _classify_error(error, "database")
        assert error_type == "integrity"
    
    def test_not_found_error_classification(self):
        """Test that NoResultFound is classified correctly."""
        error = NoResultFound()
        error_type, message = _classify_error(error, "database")
        assert error_type == "not_found"
        assert "Record not found" in message
    
    def test_multiple_results_error_classification(self):
        """Test that MultipleResultsFound is classified correctly."""
        error = MultipleResultsFound()
        error_type, message = _classify_error(error, "database")
        assert error_type == "multiple"
        assert "Multiple records found" in message
    
    def test_connection_error_classification(self):
        """Test that connection errors are classified correctly."""
        error = DisconnectionError("connection lost")
        error_type, message = _classify_error(error, "database")
        assert error_type == "connection"
        assert "Database connection error" in message


class TestDatabaseErrorHandling:
    """Test suite for database error handling decorator."""
    
    def test_handle_database_with_integrity_error(self):
        """Test that the handle_database decorator handles IntegrityError correctly."""
        # Create a test function with the decorator
        @handle_database
        def test_func():
            raise IntegrityError("statement", {}, "unique constraint violation")
        
        # Call the function and expect a ServiceError
        with pytest.raises(ServiceError) as excinfo:
            test_func()
        
        # Check the error properties
        error = excinfo.value
        assert error.service == "database"
        assert error.error_type == "integrity"
        assert "unique constraint violation" in str(error)
    
    def test_handle_database_with_not_found_error(self):
        """Test that the handle_database decorator handles NoResultFound correctly."""
        @handle_database
        def test_func():
            raise NoResultFound()
        
        with pytest.raises(ServiceError) as excinfo:
            test_func()
        
        error = excinfo.value
        assert error.service == "database"
        assert error.error_type == "not_found"
        assert "Record not found" in str(error)
    
    def test_handle_database_preserves_context(self):
        """Test that the decorator preserves context information."""
        @handle_database
        def test_func(arg1, arg2, keyword=None):
            raise SQLAlchemyError("test error")
        
        with pytest.raises(ServiceError) as excinfo:
            test_func("value1", "value2", keyword="keyword_value")
        
        error = excinfo.value
        assert "function" in error.context
        assert error.context["function"] == "test_func"
        assert "value1" in str(error.context["args"])
        assert "keyword_value" in str(error.context["kwargs"]["keyword"])
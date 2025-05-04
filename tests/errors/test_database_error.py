"""
Tests for database error handling.
"""

import pytest
from unittest.mock import Mock, patch
from sqlalchemy.exc import IntegrityError, NoResultFound, SQLAlchemyError
from sqlalchemy.orm.exc import MultipleResultsFound

from local_newsifier.errors import ServiceError
from local_newsifier.errors.database import (
    handle_database, 
    classify_database_error,
    handle_database_error
)
from local_newsifier.crud.error_handled import ErrorHandledCRUDBase

class TestDatabaseErrors:
    """Test suite for database error handling."""
    
    def test_error_classification(self):
        """Test error classification for different database errors."""
        
        # Integrity error with unique constraint violation
        real_integrity_error = IntegrityError("statement", {}, "unique constraint violation")
        error_type, message = classify_database_error(real_integrity_error)
        assert error_type == "integrity"
        
        # No result found
        error_type, message = classify_database_error(NoResultFound())
        assert error_type == "not_found"
        
        # Multiple results found
        error_type, message = classify_database_error(MultipleResultsFound())
        assert error_type == "multiple"
        
        # Generic SQLAlchemy error
        mock_sql_error = Mock(spec=SQLAlchemyError)
        error_type, message = classify_database_error(mock_sql_error)
        assert error_type == "unknown"
    
    def test_decorator_conversion(self):
        """Test that the decorator converts exceptions to ServiceError."""
        
        @handle_database()
        def failing_function():
            """Function that raises a database error."""
            raise IntegrityError(None, None, "unique constraint violation")
        
        with pytest.raises(ServiceError) as excinfo:
            failing_function()
            
        error = excinfo.value
        assert error.service == "database"
        assert error.error_type == "integrity"
        assert "function" in error.context
        assert error.context["function"] == "failing_function"
    
    def test_error_handler_preserves_service_errors(self):
        """Test that handler doesn't rewrap ServiceError."""
        
        @handle_database_error
        def already_handled():
            """Function that raises a ServiceError."""
            raise ServiceError("database", "not_found", "Record not found")
        
        with pytest.raises(ServiceError) as excinfo:
            already_handled()
            
        error = excinfo.value
        assert error.service == "database"
        assert error.error_type == "not_found"
        assert str(error) == "database.not_found: Record not found"
    
    def test_crud_base_error_handling(self):
        """Test error handling in CRUD base class."""
        
        # Mock the CRUDBase.create method to raise an IntegrityError
        with patch('local_newsifier.crud.base.CRUDBase.create', 
                   side_effect=IntegrityError("statement", {}, "unique constraint violation")):
            
            # Create CRUD class with a mock model
            model_cls = Mock()
            crud = ErrorHandledCRUDBase(model_cls)
            
            # Mock session
            db = Mock()
            
            # Test create method raises proper ServiceError
            with pytest.raises(ServiceError) as excinfo:
                crud.create(db, obj_in={})
                
            error = excinfo.value
            assert error.service == "database"
            assert error.error_type == "integrity"
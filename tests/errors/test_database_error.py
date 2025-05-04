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
        
        # Foreign key constraint violation
        foreign_key_error = IntegrityError("statement", {}, "foreign key constraint violation")
        error_type, message = classify_database_error(foreign_key_error)
        assert error_type == "integrity"
        
        # Generic integrity error
        generic_integrity_error = IntegrityError("statement", {}, "some other constraint")
        error_type, message = classify_database_error(generic_integrity_error)
        assert error_type == "integrity"
        
        # Data error
        from sqlalchemy.exc import DataError
        data_error = DataError("statement", {}, "invalid data format")
        error_type, message = classify_database_error(data_error)
        assert error_type == "validation"
        
        # Disconnection error
        from sqlalchemy.exc import DisconnectionError
        disc_error = DisconnectionError("connection was lost")
        error_type, message = classify_database_error(disc_error)
        assert error_type == "connection"
        
        # Operational error
        from sqlalchemy.exc import OperationalError
        op_error = OperationalError("statement", {}, "operational error")
        error_type, message = classify_database_error(op_error)
        assert error_type == "operational"
        
        # Timeout error
        from sqlalchemy.exc import TimeoutError
        timeout_error = TimeoutError("statement", {}, "query timeout")
        error_type, message = classify_database_error(timeout_error)
        assert error_type == "timeout"
        
        # Invalid request error
        from sqlalchemy.exc import InvalidRequestError
        invalid_req_error = InvalidRequestError("invalid request")
        error_type, message = classify_database_error(invalid_req_error)
        assert error_type == "validation"
        
        # Programming error
        from sqlalchemy.exc import ProgrammingError
        prog_error = ProgrammingError("statement", {}, "programming error")
        error_type, message = classify_database_error(prog_error)
        assert error_type == "validation"
        
        # General database error
        from sqlalchemy.exc import DatabaseError
        db_error = DatabaseError("statement", {}, "database error")
        error_type, message = classify_database_error(db_error)
        assert error_type == "database"
        
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
        
        # Generic exception
        generic_error = Exception("generic error")
        error_type, message = classify_database_error(generic_error)
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
    
    def test_database_cli_handler(self):
        """Test the database CLI handler decorator."""
        from local_newsifier.errors.database import handle_database_cli
        from click.testing import CliRunner
        import click
        
        # Create a test CLI command with the handler
        @click.command()
        @handle_database_cli
        def test_command():
            """Test CLI command."""
            raise IntegrityError("statement", {}, "unique constraint violation")
        
        # Run the command
        runner = CliRunner()
        result = runner.invoke(test_command)
        
        # Check that the output contains the error message
        assert result.exit_code != 0
        assert "database.integrity" in result.output
        assert "Hint:" in result.output
    
    def test_get_database_error_hint(self):
        """Test retrieving database-specific error hints."""
        from local_newsifier.errors.database import get_database_error_hint
        
        # Test getting hints for different error types
        assert "database connection" in get_database_error_hint("connection")
        assert "timed out" in get_database_error_hint("timeout")
        assert "constraint" in get_database_error_hint("integrity")
        assert "not found" in get_database_error_hint("not_found")
        assert "Multiple" in get_database_error_hint("multiple")
        assert "Invalid" in get_database_error_hint("validation")
        assert "Transaction" in get_database_error_hint("transaction")
        
        # Test getting hint for unknown error type
        assert "Unknown" in get_database_error_hint("nonexistent")
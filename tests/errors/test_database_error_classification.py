"""Tests for database error classification in the error handling system."""

from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.exc import (DBAPIError, DisconnectionError, IntegrityError, InvalidRequestError,
                            OperationalError, SQLAlchemyError, StatementError, TimeoutError)
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound

from src.local_newsifier.errors.error import ServiceError, _classify_database_error
from src.local_newsifier.errors.handlers import handle_database


def create_db_error(error_class, message, optional_orig=None):
    """Helper to create SQLAlchemy errors with the appropriate attributes."""
    if error_class == OperationalError:
        # For SQLAlchemy 2.0+, create with appropriate signature
        return OperationalError(f"SQL: select 1\nDetails: {message}", {}, optional_orig)
    elif error_class == IntegrityError:
        return IntegrityError(f"SQL: insert\nDetails: {message}", {}, optional_orig)
    elif error_class == DBAPIError:
        return DBAPIError(f"SQL: select 1\nDetails: {message}", {}, optional_orig)
    elif error_class == StatementError:
        # StatementError requires 'orig' parameter in SQLAlchemy 2.0+
        exception_orig = (
            optional_orig if optional_orig is not None else Exception("Original exception")
        )
        return StatementError(message, "SELECT 1", {}, exception_orig)
    elif error_class == TimeoutError:
        return TimeoutError(message)
    elif error_class == InvalidRequestError:
        return InvalidRequestError(message, optional_orig)
    elif error_class == DisconnectionError:
        return DisconnectionError(message)
    elif error_class == NoResultFound or error_class == MultipleResultsFound:
        return error_class()
    else:
        return error_class(message)


# Test database error classification
test_cases = [
    # Error class, message, optional_orig, expected_type, expected_message_contains
    (OperationalError, "connection error", None, "connection", "connection error"),
    (OperationalError, "connection refused", None, "connection", "connection error"),
    (OperationalError, "timeout error", None, "timeout", "timeout"),
    (DisconnectionError, "connection dropped", None, "connection", "connection error"),
    (DBAPIError, "operational error", None, "connection", "operational error"),
    (IntegrityError, "unique constraint violation", None, "integrity", "constraint violation"),
    (IntegrityError, "foreign key constraint", None, "integrity", "constraint violation"),
    (IntegrityError, "general integrity", None, "integrity", "integrity error"),
    (NoResultFound, "", None, "not_found", "not found"),
    (MultipleResultsFound, "", None, "multiple", "multiple records"),
    (TimeoutError, "query timeout", None, "timeout", "timeout"),
    (StatementError, "validation error", None, "validation", "validation error"),
    (InvalidRequestError, "transaction error", None, "transaction", "transaction error"),
    (Exception, "unknown database error", None, "unknown", "unknown database error"),
]


@pytest.mark.parametrize(
    "error_class,message,optional_orig,expected_type,expected_contains", test_cases
)
def test_database_error_classification(
    error_class, message, optional_orig, expected_type, expected_contains
):
    """Test database error classification with various error types."""
    error = create_db_error(error_class, message, optional_orig)
    error_type, error_message = _classify_database_error(error)
    assert error_type == expected_type
    assert expected_contains.lower() in error_message.lower()


def test_database_error_handler_decorator():
    """Test the database error handler decorator in isolation."""

    # Test functions that raise different types of database errors
    @handle_database
    def raise_operational_error():
        raise create_db_error(OperationalError, "connection refused")

    @handle_database
    def raise_integrity_error():
        raise create_db_error(IntegrityError, "unique constraint violation")

    @handle_database
    def raise_no_result_found():
        raise NoResultFound()

    # Test operational error handling
    with pytest.raises(ServiceError) as excinfo:
        raise_operational_error()
    assert excinfo.value.service == "database"
    assert excinfo.value.error_type == "connection"
    assert "connect to the database" in str(excinfo.value)

    # Test integrity error handling
    with pytest.raises(ServiceError) as excinfo:
        raise_integrity_error()
    assert excinfo.value.service == "database"
    assert excinfo.value.error_type == "integrity"
    assert "constraint" in str(excinfo.value).lower()

    # Test not found error handling
    with pytest.raises(ServiceError) as excinfo:
        raise_no_result_found()
    assert excinfo.value.service == "database"
    assert excinfo.value.error_type == "not_found"
    assert "not found" in str(excinfo.value).lower()


@patch("src.local_newsifier.errors.error.time.sleep", MagicMock())  # Mock sleep to speed up tests
def test_retry_behavior():
    """Test retry behavior for transient database errors."""
    call_count = 0

    # Function that fails twice with a connection error, then succeeds
    @handle_database
    def function_with_retry():
        nonlocal call_count
        call_count += 1
        if call_count <= 2:
            raise create_db_error(OperationalError, "connection refused")
        return "success"

    # Should succeed on the third attempt
    result = function_with_retry()
    assert result == "success"
    assert call_count == 3

    # Reset counter
    call_count = 0

    # Function that raises a non-transient error (shouldn't retry)
    @handle_database
    def function_with_integrity_error():
        nonlocal call_count
        call_count += 1
        raise create_db_error(IntegrityError, "unique constraint violation")

    # Should fail immediately without retry
    with pytest.raises(ServiceError) as excinfo:
        function_with_integrity_error()
    assert excinfo.value.error_type == "integrity"
    assert call_count == 1  # Only called once, no retry


def test_error_message_customization():
    """Test that database errors use customized error messages."""

    # Create a function that raises a database error
    @handle_database
    def raise_connection_error():
        raise create_db_error(OperationalError, "connection refused")

    # Should use the customized error message from ERROR_MESSAGES
    with pytest.raises(ServiceError) as excinfo:
        raise_connection_error()

    # The error should contain the custom message from handlers.py
    assert "Could not connect to the database" in str(excinfo.value)


@patch("sqlalchemy.orm.Session")
def test_session_integration(mock_session_class):
    """Test error handling integration with SQLAlchemy session."""
    mock_session = MagicMock()
    mock_session_class.return_value = mock_session

    # Configure the mock to raise an exception on query execution
    mock_session.execute.side_effect = create_db_error(OperationalError, "connection refused")

    # Function that uses the session
    @handle_database
    def query_with_session(session):
        session.execute("SELECT 1")
        return True

    # Should raise a ServiceError
    with pytest.raises(ServiceError) as excinfo:
        query_with_session(mock_session)

    assert excinfo.value.service == "database"
    assert excinfo.value.error_type == "connection"
    assert mock_session.execute.called

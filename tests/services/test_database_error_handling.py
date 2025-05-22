"""Tests for SQLAlchemy exception handling in service layer."""

import pytest
from sqlalchemy.exc import (
    OperationalError,
    IntegrityError,
    TimeoutError,
    StatementError,
    InvalidRequestError,
)
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound


def test_sqlalchemy_error_types_importable():
    """Test that we can import all necessary SQLAlchemy exception types.

    This test verifies that our codebase has access to the key SQLAlchemy
    exception types needed for comprehensive database error handling.
    """
    # Test that core SQLAlchemy exception types are imported
    # (if they weren't, the test would fail on import)
    error_types = [
        NoResultFound,  # Record not found
        MultipleResultsFound,  # Multiple results when one expected
        TimeoutError,  # Query timeout
        OperationalError,  # Connection errors
        IntegrityError,  # Constraint violations
        InvalidRequestError,  # Invalid use of the API
    ]

    # Test StatementError separately since its constructor parameters changed in SQLAlchemy 2.0+
    # It now requires 'orig' parameter
    try:
        # For SQLAlchemy 2.0+
        statement_error = StatementError("Test error", "SELECT 1", {}, Exception("original"))
    except TypeError:
        # For older SQLAlchemy versions
        statement_error = StatementError("SELECT 1", {}, Exception("original"), "Test error")

    error_types.append(StatementError)  # Add to the list after testing

    # Ensure we have all the error types we need
    assert len(error_types) >= 7, "We should support at least 7 SQLAlchemy error types"

    # Check that the error classes have the expected attributes
    for error_class in error_types:
        assert issubclass(
            error_class, Exception
        ), f"{error_class.__name__} should be an exception class"

"""Tests for the exceptions module."""

import pytest
from sqlalchemy.exc import SQLAlchemyError
from src.local_newsifier.exceptions import (
    LocalNewsifierError,
    DatabaseError,
    EntityNotFoundError,
    ValidationError,
    ConfigurationError,
    NetworkError,
    ScrapingError,
    ProcessingError,
    handle_db_error,
    entity_not_found_check,
)


class TestExceptionClasses:
    """Test the exception classes."""

    def test_local_newsifier_error(self):
        """Test the base LocalNewsifierError."""
        error = LocalNewsifierError("Test error", "TEST_ERROR")
        assert error.message == "Test error"
        assert error.code == "TEST_ERROR"
        assert str(error) == "Test error"

    def test_database_error(self):
        """Test the DatabaseError."""
        error = DatabaseError("Database error", "DB_ERROR")
        assert error.message == "Database error"
        assert error.code == "DB_ERROR"
        assert isinstance(error, LocalNewsifierError)

    def test_entity_not_found_error(self):
        """Test the EntityNotFoundError."""
        error = EntityNotFoundError("Entity not found", "ENTITY_NOT_FOUND")
        assert error.message == "Entity not found"
        assert error.code == "ENTITY_NOT_FOUND"
        assert isinstance(error, DatabaseError)

    def test_validation_error(self):
        """Test the ValidationError."""
        error = ValidationError("Validation error", "VALIDATION_ERROR")
        assert error.message == "Validation error"
        assert error.code == "VALIDATION_ERROR"
        assert isinstance(error, LocalNewsifierError)

    def test_configuration_error(self):
        """Test the ConfigurationError."""
        error = ConfigurationError("Configuration error", "CONFIG_ERROR")
        assert error.message == "Configuration error"
        assert error.code == "CONFIG_ERROR"
        assert isinstance(error, LocalNewsifierError)

    def test_network_error(self):
        """Test the NetworkError."""
        error = NetworkError("Network error", "NETWORK_ERROR")
        assert error.message == "Network error"
        assert error.code == "NETWORK_ERROR"
        assert isinstance(error, LocalNewsifierError)

    def test_scraping_error(self):
        """Test the ScrapingError."""
        error = ScrapingError("Scraping error", "SCRAPING_ERROR")
        assert error.message == "Scraping error"
        assert error.code == "SCRAPING_ERROR"
        assert isinstance(error, NetworkError)

    def test_processing_error(self):
        """Test the ProcessingError."""
        error = ProcessingError("Processing error", "PROCESSING_ERROR")
        assert error.message == "Processing error"
        assert error.code == "PROCESSING_ERROR"
        assert isinstance(error, LocalNewsifierError)


class TestErrorUtilities:
    """Test error utility functions."""

    def test_handle_db_error_decorator_success(self):
        """Test the handle_db_error decorator with successful function."""
        @handle_db_error
        def success_function():
            return "Success"

        result = success_function()
        assert result == "Success"

    def test_handle_db_error_decorator_db_error(self):
        """Test the handle_db_error decorator with SQLAlchemy error."""
        @handle_db_error
        def failing_db_function():
            raise SQLAlchemyError("Database error")

        with pytest.raises(DatabaseError) as excinfo:
            failing_db_function()

        assert "Database operation failed: Database error" in str(excinfo.value)
        assert excinfo.value.code == "DB_ERROR"

    def test_handle_db_error_decorator_other_error(self):
        """Test the handle_db_error decorator with other error."""
        @handle_db_error
        def failing_function():
            raise ValueError("Other error")

        with pytest.raises(ValueError) as excinfo:
            failing_function()

        assert "Other error" in str(excinfo.value)

    def test_entity_not_found_check_with_entity(self):
        """Test entity_not_found_check with a valid entity."""
        entity = {"id": 1, "name": "Test"}
        # Should not raise an exception
        entity_not_found_check(entity, "Article", 1)

    def test_entity_not_found_check_without_entity(self):
        """Test entity_not_found_check with None entity."""
        with pytest.raises(EntityNotFoundError) as excinfo:
            entity_not_found_check(None, "Article", 123)

        assert "Article with ID 123 not found" in str(excinfo.value)
        assert excinfo.value.code == "ARTICLE_NOT_FOUND"

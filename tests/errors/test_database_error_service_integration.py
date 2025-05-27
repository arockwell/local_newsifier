"""Tests for database error handling integrated with services."""

from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm.exc import NoResultFound

from src.local_newsifier.errors.error import ServiceError
from src.local_newsifier.errors.handlers import handle_database
from tests.errors.test_database_error_classification import create_db_error


class MockArticleService:
    """Mock service class for testing database error handling."""

    def __init__(self):
        self.article_crud = MagicMock()
        self.session_factory = MagicMock()
        self.mock_session = MagicMock()

        # Configure session factory to return our mock session
        self.session_factory.return_value.__enter__.return_value = self.mock_session
        self.session_factory.return_value.__exit__.return_value = None

    @handle_database
    def get_article(self, article_id):
        """Method that might raise database errors."""
        with self.session_factory() as session:
            return self.article_crud.get(session, article_id)

    @handle_database
    def create_article(self, article_data):
        """Method that might raise integrity errors."""
        with self.session_factory() as session:
            return self.article_crud.create(session, article_data)

    @handle_database
    def get_article_with_advanced_query(self, title):
        """Method that performs a custom query."""
        with self.session_factory() as session:
            return session.execute(f"SELECT * FROM articles WHERE title = '{title}'").one()


@pytest.fixture
def mock_article_service():
    """Fixture that provides a mock article service."""
    return MockArticleService()


def test_connection_error_handling(mock_article_service):
    """Test handling of database connection errors."""
    # Configure the CRUD method to raise an OperationalError
    mock_article_service.article_crud.get.side_effect = create_db_error(
        OperationalError, "connection refused"
    )

    # Should convert to ServiceError with connection type
    with pytest.raises(ServiceError) as excinfo:
        mock_article_service.get_article(1)

    assert excinfo.value.service == "database"
    assert excinfo.value.error_type == "connection"
    assert mock_article_service.article_crud.get.called
    assert "Could not connect to the database" in str(excinfo.value)


def test_integrity_error_handling(mock_article_service):
    """Test handling of database integrity errors."""
    # Configure the CRUD method to raise an IntegrityError
    mock_article_service.article_crud.create.side_effect = create_db_error(
        IntegrityError, "unique constraint violation"
    )

    # Should convert to ServiceError with integrity type
    with pytest.raises(ServiceError) as excinfo:
        mock_article_service.create_article({"title": "Duplicate Title"})

    assert excinfo.value.service == "database"
    assert excinfo.value.error_type == "integrity"
    assert mock_article_service.article_crud.create.called
    assert "constraint violation" in str(excinfo.value).lower()


def test_not_found_error_handling(mock_article_service):
    """Test handling of database not found errors."""
    # Configure the CRUD method to raise NoResultFound
    mock_article_service.article_crud.get.side_effect = NoResultFound()

    # Should convert to ServiceError with not_found type
    with pytest.raises(ServiceError) as excinfo:
        mock_article_service.get_article(999)

    assert excinfo.value.service == "database"
    assert excinfo.value.error_type == "not_found"
    assert mock_article_service.article_crud.get.called
    assert "not found" in str(excinfo.value).lower()


def test_session_execution_error(mock_article_service):
    """Test handling of errors from session.execute."""
    # Configure the session execute method to raise an OperationalError
    mock_article_service.mock_session.execute.side_effect = create_db_error(
        OperationalError, "timeout error"
    )

    # Should convert to ServiceError with timeout type
    with pytest.raises(ServiceError) as excinfo:
        mock_article_service.get_article_with_advanced_query("Article Title")

    assert excinfo.value.service == "database"
    assert excinfo.value.error_type == "timeout"
    assert mock_article_service.mock_session.execute.called
    assert "timeout" in str(excinfo.value).lower()


@patch("src.local_newsifier.errors.error.time.sleep", MagicMock())  # Mock sleep to speed up tests
def test_service_retry_behavior(mock_article_service):
    """Test retry behavior for transient database errors in service methods."""
    # Configure the CRUD method to fail twice with a connection error, then succeed
    side_effects = [
        create_db_error(OperationalError, "connection refused"),
        create_db_error(OperationalError, "connection refused"),
        {"id": 1, "title": "Test Article"},
    ]
    mock_article_service.article_crud.get.side_effect = side_effects

    # Should retry and eventually succeed
    result = mock_article_service.get_article(1)

    # Verify the result and that the method was called multiple times
    assert result == {"id": 1, "title": "Test Article"}
    assert mock_article_service.article_crud.get.call_count == 3

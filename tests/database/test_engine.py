"""Tests for the database engine module."""

import logging
import pytest
from unittest.mock import patch, MagicMock, call

from sqlmodel import SQLModel, Session
from sqlalchemy.exc import OperationalError

from local_newsifier.database.engine import (
    get_engine,
    get_session,
    create_db_and_tables,
    transaction,
    SessionManager,
    with_session,
)


@patch("local_newsifier.database.engine.create_engine")
@patch("local_newsifier.database.engine.get_settings")
def test_get_engine_success(mock_get_settings, mock_create_engine):
    """Test successful engine creation."""
    # Arrange
    mock_settings = MagicMock()
    mock_settings.DATABASE_URL = "postgresql://user:pass@localhost/db"
    mock_settings.POSTGRES_PASSWORD = "pass"
    mock_settings.DB_POOL_SIZE = 5
    mock_settings.DB_MAX_OVERFLOW = 10
    mock_settings.DB_ECHO = False

    mock_get_settings.return_value = mock_settings

    mock_engine = MagicMock()
    mock_connection = MagicMock()
    mock_engine.connect.return_value.__enter__.return_value = mock_connection
    mock_create_engine.return_value = mock_engine

    # Act
    result = get_engine()

    # Assert
    assert result == mock_engine
    mock_create_engine.assert_called_once()
    mock_connection.execute.assert_called_once()


@patch(
    "local_newsifier.database.engine.create_engine",
    side_effect=OperationalError("statement", {}, None),
)
@patch("local_newsifier.database.engine.get_settings")
@patch("local_newsifier.database.engine.time.sleep")
def test_get_engine_retry_and_fail(mock_sleep, mock_get_settings, mock_create_engine):
    """Test engine creation with retries that eventually fail."""
    # Arrange
    mock_settings = MagicMock()
    mock_settings.DATABASE_URL = "postgresql://user:pass@localhost/db"
    mock_settings.POSTGRES_PASSWORD = "pass"
    mock_get_settings.return_value = mock_settings

    # Act
    result = get_engine(max_retries=2, retry_delay=0.1)

    # Assert
    assert result is None
    assert mock_create_engine.call_count == 3  # Initial + 2 retries
    assert mock_sleep.call_count == 2  # Called after each failed attempt except the last


@patch("local_newsifier.database.engine.get_engine")
def test_get_session_success(mock_get_engine):
    """Test successful session creation."""
    # Arrange
    mock_engine = MagicMock()
    mock_session = MagicMock()
    mock_get_engine.return_value = mock_engine

    # Use a context manager to simulate Session's behavior
    with patch("local_newsifier.database.engine.Session") as mock_session_class:
        # Configure the mock to return our mock_session when used as a context manager
        mock_session_class.return_value.__enter__.return_value = mock_session

        # Act
        session_gen = get_session()
        session = next(session_gen)

        # Assert
        assert session is mock_session


@patch("local_newsifier.database.engine.get_engine", return_value=None)
def test_get_session_no_engine(mock_get_engine):
    """Test session creation when engine is None."""
    # Act
    session_gen = get_session()
    session = next(session_gen)

    # Assert
    assert session is None


@patch("local_newsifier.database.engine.SQLModel")
@patch("local_newsifier.database.engine.get_engine")
def test_create_db_and_tables_success(mock_get_engine, mock_sqlmodel):
    """Test successful table creation."""
    # Arrange
    mock_engine = MagicMock()
    mock_get_engine.return_value = mock_engine

    # Act
    result = create_db_and_tables()

    # Assert
    assert result is True
    mock_sqlmodel.metadata.create_all.assert_called_once_with(mock_engine)


@patch("local_newsifier.database.engine.SQLModel")
@patch("local_newsifier.database.engine.get_engine")
def test_create_db_and_tables_failure(mock_get_engine, mock_sqlmodel):
    """Test table creation failure."""
    # Arrange
    mock_engine = MagicMock()
    mock_get_engine.return_value = mock_engine
    mock_sqlmodel.metadata.create_all.side_effect = Exception("Test error")

    # Act
    result = create_db_and_tables()

    # Assert
    assert result is False


def test_transaction_commit():
    """Test transaction committing on success."""
    # Arrange
    mock_session = MagicMock()

    # Act
    with transaction(mock_session):
        pass  # No exception raised

    # Assert
    mock_session.commit.assert_called_once()
    mock_session.rollback.assert_not_called()


def test_transaction_rollback():
    """Test transaction rollback on exception."""
    # Arrange
    mock_session = MagicMock()

    # Act & Assert
    with pytest.raises(ValueError):
        with transaction(mock_session):
            raise ValueError("Test error")

    mock_session.rollback.assert_called_once()
    mock_session.commit.assert_not_called()


def test_session_manager_success():
    """Test SessionManager with successful operations."""
    # Arrange
    mock_engine = MagicMock()
    mock_session = MagicMock()

    with patch("local_newsifier.database.engine.get_engine", return_value=mock_engine):
        with patch("local_newsifier.database.engine.Session", return_value=mock_session):
            # Act
            with SessionManager() as session:
                # Assert
                assert session == mock_session

    mock_session.commit.assert_called_once()
    mock_session.close.assert_called_once()


def test_session_manager_exception():
    """Test SessionManager with exception."""
    # Arrange
    mock_engine = MagicMock()
    mock_session = MagicMock()

    with patch("local_newsifier.database.engine.get_engine", return_value=mock_engine):
        with patch("local_newsifier.database.engine.Session", return_value=mock_session):
            # Act & Assert
            with pytest.raises(ValueError):
                with SessionManager() as session:
                    raise ValueError("Test error")

    mock_session.rollback.assert_called_once()
    mock_session.close.assert_called_once()


def test_session_manager_no_engine():
    """Test SessionManager when engine is None."""
    # Arrange
    with patch("local_newsifier.database.engine.get_engine", return_value=None):
        # Act
        with SessionManager() as session:
            # Assert
            assert session is None


def test_with_session_decorator_provided_session():
    """Test with_session decorator with provided session."""
    # Arrange
    mock_session = MagicMock()

    @with_session
    def test_func(session, value):
        assert session == mock_session
        return f"Value: {value}"

    # Act
    result = test_func(value="test", session=mock_session)

    # Assert
    assert result == "Value: test"


def test_with_session_decorator_new_session():
    """Test with_session decorator with new session."""
    # Arrange
    mock_session = MagicMock()

    @with_session
    def test_func(session, value):
        assert session == mock_session
        return f"Value: {value}"

    # Use context manager patch to simulate SessionManager's behavior
    with patch("local_newsifier.database.engine.SessionManager") as mock_session_manager:
        mock_session_manager.return_value.__enter__.return_value = mock_session

        # Act
        result = test_func(value="test")

        # Assert
        assert result == "Value: test"


def test_with_session_decorator_exception():
    """Test with_session decorator with exception."""
    # Arrange
    mock_session = MagicMock()

    @with_session
    def test_func(session):
        raise ValueError("Test error")

    # Act
    result = test_func(session=mock_session)

    # Assert
    assert result is None


def test_with_session_decorator_no_session():
    """Test with_session decorator when session is None."""

    # Arrange
    @with_session
    def test_func(session):
        return "Session exists" if session else "No session"

    # Use context manager patch to simulate SessionManager's behavior
    with patch("local_newsifier.database.engine.SessionManager") as mock_session_manager:
        mock_session_manager.return_value.__enter__.return_value = None

        # Act
        result = test_func()

        # Assert
        assert result is None

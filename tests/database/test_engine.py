"""Tests for database engine module."""
import contextlib
import time
from unittest.mock import MagicMock, Mock, patch, call

import pytest
from sqlmodel import SQLModel, Session, text

from local_newsifier.database.engine import (
    get_engine,
    get_session,
    transaction,
    create_db_and_tables,
    SessionManager,
    with_session,
)


class TestGetEngine:
    """Tests for get_engine function."""

    @patch("local_newsifier.database.engine.create_engine")
    @patch("local_newsifier.database.engine.get_settings")
    def test_get_engine_success(self, mock_get_settings, mock_create_engine):
        """Test successful engine creation."""
        # Set up the mocks
        mock_settings = MagicMock()
        mock_settings.DATABASE_URL = "postgresql://user:pass@localhost:5432/testdb"
        mock_settings.POSTGRES_PASSWORD = "pass"
        mock_settings.DB_POOL_SIZE = 5
        mock_settings.DB_MAX_OVERFLOW = 10
        mock_settings.DB_ECHO = False
        mock_get_settings.return_value = mock_settings

        mock_engine = MagicMock()
        mock_conn = MagicMock()
        mock_engine.connect.return_value.__enter__.return_value = mock_conn
        mock_create_engine.return_value = mock_engine

        # Call the function
        result = get_engine()

        # Verify the result
        assert result == mock_engine

        # Verify that create_engine was called with the correct arguments
        mock_create_engine.assert_called_once_with(
            str(mock_settings.DATABASE_URL),
            pool_size=mock_settings.DB_POOL_SIZE,
            max_overflow=mock_settings.DB_MAX_OVERFLOW,
            connect_args={
                "application_name": "local_newsifier",
                "connect_timeout": 10,
            },
            echo=mock_settings.DB_ECHO,
            pool_pre_ping=True,
            pool_recycle=300,
        )

        # Verify that the connection was tested - using assert_called_once() instead of assert_called_once_with()
        # because TextClause objects (from text("SELECT 1")) don't compare equal even with the same content
        mock_conn.execute.assert_called_once()

    @patch("local_newsifier.database.engine.create_engine")
    @patch("local_newsifier.database.engine.get_settings")
    def test_get_engine_not_postgresql(self, mock_get_settings, mock_create_engine):
        """Test engine creation with non-PostgreSQL URL."""
        # Set up the mocks
        mock_settings = MagicMock()
        mock_settings.DATABASE_URL = "sqlite:///test.db"
        mock_settings.POSTGRES_PASSWORD = None
        mock_settings.DB_POOL_SIZE = 5
        mock_settings.DB_MAX_OVERFLOW = 10
        mock_settings.DB_ECHO = False
        mock_get_settings.return_value = mock_settings

        mock_engine = MagicMock()
        mock_conn = MagicMock()
        mock_engine.connect.return_value.__enter__.return_value = mock_conn
        mock_create_engine.return_value = mock_engine

        # Call the function
        result = get_engine()

        # Verify the result
        assert result == mock_engine

        # Verify that create_engine was called with the correct arguments - no connect_args for SQLite
        mock_create_engine.assert_called_once_with(
            str(mock_settings.DATABASE_URL),
            pool_size=mock_settings.DB_POOL_SIZE,
            max_overflow=mock_settings.DB_MAX_OVERFLOW,
            connect_args={},  # Empty connect_args for non-PostgreSQL
            echo=mock_settings.DB_ECHO,
            pool_pre_ping=True,
            pool_recycle=300,
        )

    @patch("local_newsifier.database.engine.create_engine")
    @patch("local_newsifier.database.engine.get_settings")
    @patch("time.sleep")
    def test_get_engine_retry_success(
        self, mock_sleep, mock_get_settings, mock_create_engine
    ):
        """Test engine creation with retry."""
        # Set up the mocks
        mock_settings = MagicMock()
        mock_settings.DATABASE_URL = "postgresql://user:pass@localhost:5432/testdb"
        mock_settings.POSTGRES_PASSWORD = "pass"
        mock_settings.DB_POOL_SIZE = 5
        mock_settings.DB_MAX_OVERFLOW = 10
        mock_settings.DB_ECHO = False
        mock_get_settings.return_value = mock_settings

        # First attempt fails, second succeeds
        mock_engine_fail = MagicMock()
        mock_engine_fail.connect.side_effect = Exception("Connection failed")
        
        mock_engine_success = MagicMock()
        mock_conn = MagicMock()
        mock_engine_success.connect.return_value.__enter__.return_value = mock_conn
        
        mock_create_engine.side_effect = [mock_engine_fail, mock_engine_success]

        # Call the function
        result = get_engine()

        # Verify the result
        assert result == mock_engine_success

        # Verify that create_engine was called twice
        assert mock_create_engine.call_count == 2
        
        # Verify that sleep was called once with retry_delay
        mock_sleep.assert_called_once_with(2)

    @patch("local_newsifier.database.engine.create_engine")
    @patch("local_newsifier.database.engine.get_settings")
    @patch("time.sleep")
    def test_get_engine_all_attempts_fail(
        self, mock_sleep, mock_get_settings, mock_create_engine
    ):
        """Test engine creation with all attempts failing."""
        # Set up the mocks
        mock_settings = MagicMock()
        mock_settings.DATABASE_URL = "postgresql://user:pass@localhost:5432/testdb"
        mock_settings.POSTGRES_PASSWORD = "pass"
        mock_get_settings.return_value = mock_settings

        # All attempts fail
        mock_create_engine.side_effect = Exception("Connection failed")

        # Call the function with 2 retries
        result = get_engine(max_retries=2, retry_delay=1)

        # Verify the result is None
        assert result is None

        # Verify that create_engine was called 3 times (initial + 2 retries)
        assert mock_create_engine.call_count == 3
        
        # Verify that sleep was called twice with retry_delay
        assert mock_sleep.call_count == 2
        mock_sleep.assert_has_calls([call(1), call(1)])

    @patch("local_newsifier.database.engine.create_engine")
    def test_get_engine_with_custom_url(self, mock_create_engine):
        """Test engine creation with custom URL."""
        # Set up the mocks
        custom_url = "sqlite:///custom.db"
        mock_engine = MagicMock()
        mock_conn = MagicMock()
        mock_engine.connect.return_value.__enter__.return_value = mock_conn
        mock_create_engine.return_value = mock_engine

        # Call the function with custom URL
        result = get_engine(url=custom_url)

        # Verify the result
        assert result == mock_engine
        
        # Verify that get_settings was not called (we're not using the patch here)
        assert "get_settings" not in mock_create_engine.mock_calls


class TestGetSession:
    """Tests for get_session function."""

    @patch("local_newsifier.database.engine.get_engine")
    @patch("local_newsifier.database.engine.Session")
    def test_get_session_success(self, mock_session_class, mock_get_engine):
        """Test successful session creation."""
        # Set up the mocks
        mock_engine = MagicMock()
        mock_get_engine.return_value = mock_engine
        
        mock_session = MagicMock()
        mock_session_context = MagicMock()
        mock_session_context.__enter__.return_value = mock_session
        mock_session_class.return_value = mock_session_context

        # Call the function
        session_gen = get_session()
        session = next(session_gen)

        # Verify the result
        assert session == mock_session

        # Verify that Session was called with the engine
        mock_session_class.assert_called_once_with(mock_engine)

    @patch("local_newsifier.database.engine.get_engine")
    def test_get_session_engine_none(self, mock_get_engine):
        """Test session creation with engine None."""
        # Set up the mock to return None
        mock_get_engine.return_value = None

        # Call the function
        session_gen = get_session()
        session = next(session_gen)

        # Verify the result is None
        assert session is None

    @patch("local_newsifier.database.engine.get_engine")
    @patch("local_newsifier.database.engine.Session")
    def test_get_session_exception(self, mock_session_class, mock_get_engine):
        """Test session creation with exception."""
        # Set up the mocks
        mock_engine = MagicMock()
        mock_get_engine.return_value = mock_engine
        
        # Session raises an exception
        mock_session_class.side_effect = Exception("Session error")

        # Call the function
        session_gen = get_session()
        session = next(session_gen)

        # Verify the result is None
        assert session is None


class TestTransaction:
    """Tests for transaction context manager."""

    def test_transaction_success(self):
        """Test successful transaction."""
        # Set up the mock
        mock_session = MagicMock()
        
        # Call the function
        with transaction(mock_session):
            pass
        
        # Verify that commit was called
        mock_session.commit.assert_called_once()
        mock_session.rollback.assert_not_called()

    def test_transaction_exception(self):
        """Test transaction with exception."""
        # Set up the mock
        mock_session = MagicMock()
        
        # Call the function with an exception
        with pytest.raises(ValueError):
            with transaction(mock_session):
                raise ValueError("Test exception")
        
        # Verify that rollback was called
        mock_session.rollback.assert_called_once()
        mock_session.commit.assert_not_called()


class TestCreateDbAndTables:
    """Tests for create_db_and_tables function."""

    @patch("local_newsifier.database.engine.SQLModel.metadata.create_all")
    @patch("local_newsifier.database.engine.get_engine")
    def test_create_db_and_tables_with_engine(
        self, mock_get_engine, mock_create_all
    ):
        """Test table creation with provided engine."""
        # Set up the mock
        mock_engine = MagicMock()
        
        # Call the function
        result = create_db_and_tables(engine=mock_engine)
        
        # Verify the result
        assert result is True
        
        # Verify that create_all was called with the engine
        mock_create_all.assert_called_once_with(mock_engine)
        
        # Verify that get_engine was not called
        mock_get_engine.assert_not_called()

    @patch("local_newsifier.database.engine.SQLModel.metadata.create_all")
    @patch("local_newsifier.database.engine.get_engine")
    def test_create_db_and_tables_without_engine(
        self, mock_get_engine, mock_create_all
    ):
        """Test table creation without provided engine."""
        # Set up the mock
        mock_engine = MagicMock()
        mock_get_engine.return_value = mock_engine
        
        # Call the function
        result = create_db_and_tables()
        
        # Verify the result
        assert result is True
        
        # Verify that get_engine was called
        mock_get_engine.assert_called_once()
        
        # Verify that create_all was called with the engine
        mock_create_all.assert_called_once_with(mock_engine)

    @patch("local_newsifier.database.engine.get_engine")
    def test_create_db_and_tables_get_engine_fails(self, mock_get_engine):
        """Test table creation with get_engine failing."""
        # Set up the mock to raise an exception
        mock_get_engine.side_effect = Exception("Engine error")
        
        # Call the function
        result = create_db_and_tables()
        
        # Verify the result
        assert result is False

    @patch("local_newsifier.database.engine.SQLModel.metadata.create_all")
    @patch("local_newsifier.database.engine.get_engine")
    def test_create_db_and_tables_create_all_fails(
        self, mock_get_engine, mock_create_all
    ):
        """Test table creation with create_all failing."""
        # Set up the mocks
        mock_engine = MagicMock()
        mock_get_engine.return_value = mock_engine
        
        # Make create_all raise an exception
        mock_create_all.side_effect = Exception("Create all error")
        
        # Call the function
        result = create_db_and_tables()
        
        # Verify the result
        assert result is False


class TestSessionManager:
    """Tests for SessionManager class."""

    @patch("local_newsifier.database.engine.get_engine")
    @patch("local_newsifier.database.engine.Session")
    def test_session_manager_success(self, mock_session_class, mock_get_engine):
        """Test successful session management."""
        # Set up the mocks
        mock_engine = MagicMock()
        mock_get_engine.return_value = mock_engine
        
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        # Call the function
        with SessionManager() as session:
            # Verify that the session is correct
            assert session == mock_session
            
        # Verify that commit and close were called
        mock_session.commit.assert_called_once()
        mock_session.close.assert_called_once()
        mock_session.rollback.assert_not_called()

    @patch("local_newsifier.database.engine.get_engine")
    @patch("local_newsifier.database.engine.Session")
    def test_session_manager_exception(self, mock_session_class, mock_get_engine):
        """Test session management with exception."""
        # Set up the mocks
        mock_engine = MagicMock()
        mock_get_engine.return_value = mock_engine
        
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session

        # Call the function with an exception
        with pytest.raises(ValueError):
            with SessionManager() as session:
                raise ValueError("Test exception")
            
        # Verify that rollback and close were called
        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()
        mock_session.commit.assert_not_called()

    @patch("local_newsifier.database.engine.get_engine")
    def test_session_manager_get_engine_none(self, mock_get_engine):
        """Test session management with engine None."""
        # Set up the mock to return None
        mock_get_engine.return_value = None

        # Call the function
        with SessionManager() as session:
            # Verify that the session is None
            assert session is None

    @patch("local_newsifier.database.engine.get_engine")
    @patch("local_newsifier.database.engine.Session")
    def test_session_manager_session_exception(
        self, mock_session_class, mock_get_engine
    ):
        """Test session management with Session exception."""
        # Set up the mocks
        mock_engine = MagicMock()
        mock_get_engine.return_value = mock_engine
        
        # Session raises an exception
        mock_session_class.side_effect = Exception("Session error")

        # Call the function
        with SessionManager() as session:
            # Verify that the session is None
            assert session is None


class TestWithSession:
    """Tests for with_session decorator."""

    def test_with_session_provided_session(self):
        """Test with_session with provided session."""
        # Set up the test function
        @with_session
        def test_func(session, arg1, arg2=None):
            return f"session: {session}, arg1: {arg1}, arg2: {arg2}"
        
        # Set up the mock session
        mock_session = MagicMock()
        
        # Call the function with a provided session
        result = test_func(session=mock_session, arg1="test", arg2="value")
        
        # Verify the result
        assert result == f"session: {mock_session}, arg1: test, arg2: value"

    @patch("local_newsifier.database.engine.SessionManager")
    def test_with_session_new_session(self, mock_session_manager_class):
        """Test with_session with new session."""
        # Set up the test function
        @with_session
        def test_func(session, arg1, arg2=None):
            return f"session: {session}, arg1: {arg1}, arg2: {arg2}"
        
        # Set up the mocks
        mock_session = MagicMock()
        mock_context = MagicMock()
        mock_context.__enter__.return_value = mock_session
        mock_session_manager_class.return_value = mock_context
        
        # Call the function without providing a session
        result = test_func(arg1="test", arg2="value")
        
        # Verify the result
        assert result == f"session: {mock_session}, arg1: test, arg2: value"
        
        # Verify that SessionManager was called
        mock_session_manager_class.assert_called_once()

    @patch("local_newsifier.database.engine.SessionManager")
    def test_with_session_new_session_exception(self, mock_session_manager_class):
        """Test with_session with new session and exception."""
        # Set up the test function
        @with_session
        def test_func(session, arg1, arg2=None):
            raise ValueError("Test exception")
        
        # Set up the mocks
        mock_session = MagicMock()
        mock_context = MagicMock()
        mock_context.__enter__.return_value = mock_session
        mock_session_manager_class.return_value = mock_context
        
        # Call the function without providing a session
        result = test_func(arg1="test", arg2="value")
        
        # Verify the result is None (exception was caught)
        assert result is None

    def test_with_session_provided_session_exception(self):
        """Test with_session with provided session and exception."""
        # Set up the test function
        @with_session
        def test_func(session, arg1, arg2=None):
            raise ValueError("Test exception")
        
        # Set up the mock session
        mock_session = MagicMock()
        
        # Call the function with a provided session
        result = test_func(session=mock_session, arg1="test", arg2="value")
        
        # Verify the result is None (exception was caught)
        assert result is None

    @patch("local_newsifier.database.engine.SessionManager")
    def test_with_session_no_session_from_manager(self, mock_session_manager_class):
        """Test with_session when SessionManager returns None."""
        # Set up the test function
        @with_session
        def test_func(session, arg1, arg2=None):
            return f"session: {session}, arg1: {arg1}, arg2: {arg2}"
        
        # Set up the mocks to return None
        mock_context = MagicMock()
        mock_context.__enter__.return_value = None
        mock_session_manager_class.return_value = mock_context
        
        # Call the function without providing a session
        result = test_func(arg1="test", arg2="value")
        
        # Verify the result is None
        assert result is None

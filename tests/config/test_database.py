"""Tests for database configuration module."""

from unittest.mock import MagicMock, patch

import pytest
from sqlmodel import Session

from local_newsifier.config.database import (
    get_database,
    get_database_settings,
    get_db_session,
)
from local_newsifier.database.engine import get_engine, get_session, transaction


class TestDatabaseConfig:
    """Tests for database configuration module."""

    def test_get_session(self):
        """Test get_session generator."""
        with patch("local_newsifier.database.engine.get_engine") as mock_get_engine:
            mock_engine = MagicMock()
            mock_get_engine.return_value = mock_engine

            with Session(mock_engine) as mock_session:
                mock_engine.connect.return_value = MagicMock()
                # Use a list to capture the yielded session
                yielded_session = None

                # Create a generator
                session_gen = get_session()

                # Get the yielded session
                try:
                    yielded_session = next(session_gen)
                except StopIteration:
                    pass  # This should not happen

                # Verify we got a session
                assert yielded_session is not None

            # Verify engine was created
            mock_get_engine.assert_called_once()

    def test_transaction_commit(self):
        """Test transaction context manager with successful commit."""
        # Mock session
        mock_session = MagicMock()

        # Use transaction context manager
        with transaction(mock_session):
            # Simulate database operations
            pass

        # Verify commit was called
        mock_session.commit.assert_called_once()
        mock_session.rollback.assert_not_called()

    def test_transaction_rollback(self):
        """Test transaction context manager with error causing rollback."""
        # Mock session
        mock_session = MagicMock()

        # Use transaction context manager with exception
        with pytest.raises(ValueError):
            with transaction(mock_session):
                # Simulate database operations that fail
                raise ValueError("Test error")

        # Verify rollback was called
        mock_session.rollback.assert_called_once()
        mock_session.commit.assert_not_called()

    @patch("local_newsifier.config.database.get_settings")
    def test_get_database_settings(self, mock_get_settings):
        """Test getting database settings instance."""
        # Mock settings
        mock_settings = MagicMock()
        mock_settings.POSTGRES_USER = "testuser"
        mock_settings.POSTGRES_PASSWORD = "testpass"
        mock_settings.POSTGRES_HOST = "testhost"
        mock_settings.POSTGRES_PORT = "5432"
        mock_settings.POSTGRES_DB = "testdb"
        mock_settings.DATABASE_URL = (
            "postgresql://testuser:testpass@testhost:5432/testdb"
        )
        mock_get_settings.return_value = mock_settings

        # Get database settings
        settings = get_database_settings()

        # Verify settings
        assert settings.POSTGRES_USER == "testuser"
        assert settings.POSTGRES_PASSWORD == "testpass"
        assert settings.POSTGRES_HOST == "testhost"
        assert settings.POSTGRES_PORT == "5432"
        assert settings.POSTGRES_DB == "testdb"
        assert (
            settings.DATABASE_URL
            == "postgresql://testuser:testpass@testhost:5432/testdb"
        )
        assert (
            settings.get_database_url()
            == "postgresql://testuser:testpass@testhost:5432/testdb"
        )

    @patch("local_newsifier.database.engine.get_engine")
    @patch("local_newsifier.config.database.get_settings")
    def test_get_database(self, mock_get_settings, mock_get_engine):
        """Test getting database engine instance."""
        # Mock settings
        mock_settings = MagicMock()
        mock_settings.DATABASE_URL = (
            "postgresql://testuser:testpass@testhost:5432/testdb"
        )
        mock_get_settings.return_value = mock_settings

        # Mock engine
        mock_engine = MagicMock()
        mock_get_engine.return_value = mock_engine

        # Get database engine
        engine = get_database()

        # Verify engine
        assert engine == mock_engine
        mock_get_engine.assert_called_once_with(
            "postgresql://testuser:testpass@testhost:5432/testdb"
        )

    @patch("local_newsifier.config.database.get_database")
    def test_get_db_session(self, mock_get_database):
        """Test getting database session."""
        # Mock engine
        mock_engine = MagicMock()
        mock_get_database.return_value = mock_engine

        # Get session
        session = get_db_session()

        # Verify session
        assert isinstance(session, Session)
        mock_get_database.assert_called_once()
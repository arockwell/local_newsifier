"""Tests for database configuration module."""

import pytest
from unittest.mock import MagicMock, patch

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from local_newsifier.config.database import (
    get_db, transaction, get_database_settings, get_database, get_db_session
)


class TestDatabaseConfig:
    """Tests for database configuration module."""

    def test_get_db(self):
        """Test get_db session generator."""
        session = next(get_db())
        assert isinstance(session, Session)
        session.close()

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

    def test_transaction_sqlalchemy_error(self):
        """Test transaction context manager with SQLAlchemy error."""
        # Mock session
        mock_session = MagicMock()
        
        # Use transaction context manager with SQLAlchemy exception
        with pytest.raises(SQLAlchemyError):
            with transaction(mock_session):
                # Simulate database operations that fail with SQLAlchemy error
                raise SQLAlchemyError("Database error")
        
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
        mock_settings.DATABASE_URL = "postgresql://testuser:testpass@testhost:5432/testdb"
        mock_get_settings.return_value = mock_settings
        
        # Get database settings
        settings = get_database_settings()
        
        # Verify settings
        assert settings.POSTGRES_USER == "testuser"
        assert settings.POSTGRES_PASSWORD == "testpass"
        assert settings.POSTGRES_HOST == "testhost"
        assert settings.POSTGRES_PORT == "5432"
        assert settings.POSTGRES_DB == "testdb"
        assert settings.DATABASE_URL == "postgresql://testuser:testpass@testhost:5432/testdb"
        assert settings.get_database_url() == "postgresql://testuser:testpass@testhost:5432/testdb"

    @patch("local_newsifier.config.database.init_db")
    @patch("local_newsifier.config.database.get_settings")
    def test_get_database(self, mock_get_settings, mock_init_db):
        """Test getting database engine instance."""
        # Mock settings
        mock_settings = MagicMock()
        mock_settings.DATABASE_URL = "postgresql://testuser:testpass@testhost:5432/testdb"
        mock_get_settings.return_value = mock_settings
        
        # Mock engine
        mock_engine = MagicMock()
        mock_init_db.return_value = mock_engine
        
        # Get database engine
        engine = get_database()
        
        # Verify engine
        assert engine == mock_engine
        mock_init_db.assert_called_once_with("postgresql://testuser:testpass@testhost:5432/testdb")

    @patch("local_newsifier.config.database.sessionmaker")
    @patch("local_newsifier.config.database.get_database")
    def test_get_db_session(self, mock_get_database, mock_sessionmaker):
        """Test getting database session factory."""
        # Mock engine
        mock_engine = MagicMock()
        mock_get_database.return_value = mock_engine
        
        # Mock session factory
        mock_session_factory = MagicMock()
        mock_sessionmaker.return_value = mock_session_factory
        
        # Get session factory
        session_factory = get_db_session()
        
        # Verify session factory
        assert session_factory == mock_session_factory
        mock_get_database.assert_called_once()
        mock_sessionmaker.assert_called_once_with(bind=mock_engine)
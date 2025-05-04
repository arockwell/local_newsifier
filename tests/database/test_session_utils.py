"""Tests for the standardized database session management utilities."""

import pytest
from unittest.mock import MagicMock, patch

from sqlmodel import Session

from local_newsifier.database.session_utils import get_db_session, with_db_session


class TestSessionUtils:
    """Test class for session utilities."""

    def test_get_db_session(self, mocker):
        """Test that get_db_session gets a session from the container."""
        # Mock the container
        mock_container = MagicMock()
        mock_session_factory = MagicMock()
        mock_container.get.return_value = mock_session_factory
        
        # Mock the session context manager
        mock_session_ctx = MagicMock()
        mock_session = MagicMock(spec=Session)
        mock_session_ctx.__enter__.return_value = mock_session
        mock_session_factory.return_value = mock_session_ctx
        
        # Call get_db_session
        with get_db_session(container=mock_container) as session:
            # Verify the session is the mock session
            assert session is mock_session
            
        # Verify the container was used correctly
        mock_container.get.assert_called_once_with("session_factory")
        mock_session_factory.assert_called_once()
        mock_session_ctx.__enter__.assert_called_once()
        mock_session_ctx.__exit__.assert_called_once()

    def test_with_db_session_decorator_with_session(self, mocker):
        """Test that with_db_session uses a provided session."""
        # Create a mock session
        mock_session = MagicMock(spec=Session)
        
        # Define a decorated function
        @with_db_session
        def test_func(session=None):
            return session
        
        # Call the function with the mock session
        result = test_func(session=mock_session)
        
        # Verify the session is the mock session
        assert result is mock_session

    def test_with_db_session_decorator_without_session(self, mocker):
        """Test that with_db_session creates a session if none is provided."""
        # Mock get_db_session
        mock_session = MagicMock(spec=Session)
        mock_session_ctx = MagicMock()
        mock_session_ctx.__enter__.return_value = mock_session
        
        mocker.patch(
            'local_newsifier.database.session_utils.get_db_session',
            return_value=mock_session_ctx
        )
        
        # Define a decorated function
        @with_db_session
        def test_func(session=None):
            return session
        
        # Call the function without a session
        result = test_func()
        
        # Verify the session is the mock session
        assert result is mock_session
        mock_session_ctx.__enter__.assert_called_once()
        mock_session_ctx.__exit__.assert_called_once()

    def test_with_db_session_decorator_with_container(self, mocker):
        """Test that with_db_session passes the container to get_db_session."""
        # Mock get_db_session
        mock_get_db_session = mocker.patch(
            'local_newsifier.database.session_utils.get_db_session',
            return_value=MagicMock()
        )
        
        # Create a mock container
        mock_container = MagicMock()
        
        # Define a decorated function with container
        @with_db_session(container=mock_container)
        def test_func(session=None):
            return session
        
        # Call the function without a session
        test_func()
        
        # Verify get_db_session was called with the container
        mock_get_db_session.assert_called_once_with(container=mock_container)

    def test_with_db_session_decorator_error_handling(self, mocker):
        """Test that with_db_session handles errors correctly."""
        # Mock get_db_session to raise an exception
        mock_get_db_session = mocker.patch(
            'local_newsifier.database.session_utils.get_db_session',
            side_effect=Exception("Test exception")
        )
        
        # Mock logger
        mock_logger = mocker.patch('local_newsifier.database.session_utils.logger')
        
        # Define a decorated function
        @with_db_session
        def test_func(session=None):
            return session
        
        # Call the function without a session
        result = test_func()
        
        # Verify the result is None and the error was logged
        assert result is None
        mock_logger.exception.assert_called_once()
        assert "Error in with_db_session" in mock_logger.exception.call_args[0][0]

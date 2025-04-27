"""Tests for API dependencies."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from sqlmodel import Session

from local_newsifier.api.dependencies import get_session, get_article_service, get_rss_feed_service


def test_get_session_yield():
    """Test that get_session yields a database session."""
    # Create a mock session factory and session
    mock_session = Mock(spec=Session)
    mock_manager = MagicMock()  # Use MagicMock for magic methods
    mock_manager.__enter__.return_value = mock_session
    
    # Create a mock for container
    with patch("local_newsifier.api.dependencies.container") as mock_container:
        # Set up the mock container to return None for session_factory
        # This will cause the fallback to SessionManager
        mock_container.get.return_value = None
        
        # Then mock SessionManager
        with patch("local_newsifier.api.dependencies.SessionManager", autospec=True) as MockSessionManager:
            # Set up the SessionManager mock
            MockSessionManager.return_value = mock_manager
            
            # Get the session from the generator
            session_generator = get_session()
            session = next(session_generator)
            
            # Verify the session is what we expect
            assert session is mock_session
            assert mock_container.get.called
            assert mock_container.get.call_args[0][0] == "session_factory"
            assert MockSessionManager.called


def test_get_session_from_container():
    """Test that get_session uses the session factory from the container when available."""
    # Create a mock session factory and session
    mock_session = Mock(spec=Session)
    mock_session_factory = Mock()
    mock_manager = MagicMock()  # Use MagicMock for magic methods
    mock_manager.__enter__.return_value = mock_session
    mock_session_factory.return_value = mock_manager
    
    # Create a mock for container
    with patch("local_newsifier.api.dependencies.container") as mock_container:
        # Set up the mock container to return our session factory
        mock_container.get.return_value = mock_session_factory
        
        # Get the session from the generator
        session_generator = get_session()
        session = next(session_generator)
        
        # Verify the session is what we expect
        assert session is mock_session
        assert mock_container.get.called
        assert mock_container.get.call_args[0][0] == "session_factory"
        assert mock_session_factory.called


def test_get_session_context_manager():
    """Test that the session context manager is used correctly."""
    # Use MagicMock instead which doesn't have the attribute restrictions
    with patch("local_newsifier.api.dependencies.container") as mock_container:
        # Set up container to return None
        mock_container.get.return_value = None
        
        with patch("local_newsifier.api.dependencies.SessionManager") as MockSessionManager:
            # Create a mock session and context manager
            mock_session = MagicMock(spec=Session)
            mock_manager = MagicMock()
            mock_manager.__enter__.return_value = mock_session
            MockSessionManager.return_value = mock_manager
            
            # Use the generator
            session_generator = get_session()
            _ = next(session_generator)
            
            # Try to exhaust the generator to trigger the cleanup
            try:
                next(session_generator)
            except StopIteration:
                pass
            
            # Verify context manager was used correctly
            assert mock_manager.__enter__.called


def test_get_article_service():
    """Test that get_article_service returns the service from the container."""
    mock_service = Mock()
    
    with patch("local_newsifier.api.dependencies.container") as mock_container:
        # Set up the mock container to return our mock service
        mock_container.get.return_value = mock_service
        
        # Get the service
        service = get_article_service()
        
        # Verify the service is what we expect
        assert service is mock_service
        assert mock_container.get.called
        assert mock_container.get.call_args[0][0] == "article_service"


def test_get_rss_feed_service():
    """Test that get_rss_feed_service returns the service from the container."""
    mock_service = Mock()
    
    with patch("local_newsifier.api.dependencies.container") as mock_container:
        # Set up the mock container to return our mock service
        mock_container.get.return_value = mock_service
        
        # Get the service
        service = get_rss_feed_service()
        
        # Verify the service is what we expect
        assert service is mock_service
        assert mock_container.get.called
        assert mock_container.get.call_args[0][0] == "rss_feed_service"

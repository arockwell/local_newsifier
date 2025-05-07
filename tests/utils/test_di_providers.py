"""Tests for the DI provider functions."""

import pytest
from unittest.mock import MagicMock, patch, Mock
from typing import Annotated, Generator, Any

from fastapi import Depends
from sqlmodel import Session

# Import providers to test
from local_newsifier.di.providers import (
    get_session, get_article_crud, get_entity_crud, get_entity_relationship_crud,
    get_rss_feed_crud, get_web_scraper_tool, get_entity_extractor, 
    get_entity_resolver, get_rss_parser, get_article_service, get_entity_service,
    get_rss_feed_service
)

# Mock the injectable decorator
patch('local_newsifier.di.providers.injectable', lambda **kwargs: lambda x: x).start()


def test_get_session_provides_and_closes():
    """Test that get_session provides a session and closes it when done."""
    # Arrange
    mock_session = MagicMock(spec=Session)
    mock_db_session_gen = MagicMock()
    mock_db_session_gen.__next__ = MagicMock(return_value=mock_session)
    
    # Act
    with patch('local_newsifier.database.engine.get_session', 
               return_value=mock_db_session_gen):
        # Create generator and get session
        session_gen = get_session()
        session = next(session_gen)
        
        # Assert session is returned
        assert session is mock_session
        
        # Close the session (exhaust generator)
        try:
            next(session_gen)
        except StopIteration:
            pass
    
    # Assert that session is closed
    mock_session.close.assert_called_once()


def test_get_article_crud():
    """Test the article CRUD provider."""
    # Arrange
    mock_crud = MagicMock()
    
    # Act
    with patch('local_newsifier.di.providers.article', mock_crud):
        result = get_article_crud()
    
    # Assert
    assert result is mock_crud


def test_get_entity_crud():
    """Test the entity CRUD provider."""
    # Arrange
    mock_crud = MagicMock()
    
    # Act
    with patch('local_newsifier.di.providers.entity', mock_crud):
        result = get_entity_crud()
    
    # Assert
    assert result is mock_crud


def test_get_entity_relationship_crud():
    """Test the entity relationship CRUD provider."""
    # Arrange
    mock_crud = MagicMock()
    
    # Act
    with patch('local_newsifier.di.providers.entity_relationship', mock_crud):
        result = get_entity_relationship_crud()
    
    # Assert
    assert result is mock_crud


def test_get_rss_feed_crud():
    """Test the RSS feed CRUD provider."""
    # Arrange
    mock_crud = MagicMock()
    
    # Act
    with patch('local_newsifier.di.providers.rss_feed', mock_crud):
        result = get_rss_feed_crud()
    
    # Assert
    assert result is mock_crud


def test_get_web_scraper_tool():
    """Test the web scraper tool provider."""
    # Arrange
    mock_tool_class = MagicMock()
    mock_tool = MagicMock()
    mock_tool_class.return_value = mock_tool
    
    # Act
    with patch('local_newsifier.di.providers.WebScraperTool', mock_tool_class):
        result = get_web_scraper_tool()
    
    # Assert
    assert result is mock_tool
    mock_tool_class.assert_called_once()


def test_get_entity_extractor():
    """Test the entity extractor provider."""
    # Arrange
    mock_tool_class = MagicMock()
    mock_tool = MagicMock()
    mock_tool_class.return_value = mock_tool
    
    # Act
    with patch('local_newsifier.di.providers.EntityExtractor', mock_tool_class):
        result = get_entity_extractor()
    
    # Assert
    assert result is mock_tool
    mock_tool_class.assert_called_once()


def test_get_entity_resolver():
    """Test the entity resolver provider."""
    # Arrange
    mock_tool_class = MagicMock()
    mock_tool = MagicMock()
    mock_tool_class.return_value = mock_tool
    
    # Act
    with patch('local_newsifier.di.providers.EntityResolver', mock_tool_class):
        result = get_entity_resolver()
    
    # Assert
    assert result is mock_tool
    mock_tool_class.assert_called_once()


def test_get_rss_parser():
    """Test the RSS parser provider."""
    # Arrange
    mock_tool_class = MagicMock()
    mock_tool = MagicMock()
    mock_tool_class.return_value = mock_tool
    
    # Act
    with patch('local_newsifier.di.providers.RSSParser', mock_tool_class):
        result = get_rss_parser()
    
    # Assert
    assert result is mock_tool
    mock_tool_class.assert_called_once()


def test_get_article_service():
    """Test the article service provider."""
    # Arrange
    mock_article_crud = MagicMock()
    mock_entity_crud = MagicMock()
    mock_session = MagicMock()
    
    mock_service_class = MagicMock()
    mock_service = MagicMock()
    mock_service_class.return_value = mock_service
    
    # Act
    with patch('local_newsifier.di.providers.ArticleService', mock_service_class):
        result = get_article_service(
            article_crud=mock_article_crud,
            entity_crud=mock_entity_crud,
            session=mock_session
        )
    
    # Assert
    assert result is mock_service
    mock_service_class.assert_called_once_with(
        article_crud=mock_article_crud,
        entity_crud=mock_entity_crud,
        session_factory=Any  # Lambda cannot be directly compared
    )
    
    # Verify the session factory works
    session_factory = mock_service_class.call_args[1]['session_factory']
    assert session_factory() is mock_session


def test_get_entity_service():
    """Test the entity service provider."""
    # Arrange
    mock_entity_crud = MagicMock()
    mock_entity_relationship_crud = MagicMock()
    mock_session = MagicMock()
    
    mock_service_class = MagicMock()
    mock_service = MagicMock()
    mock_service_class.return_value = mock_service
    
    # Act
    with patch('local_newsifier.di.providers.EntityService', mock_service_class):
        result = get_entity_service(
            entity_crud=mock_entity_crud,
            entity_relationship_crud=mock_entity_relationship_crud,
            session=mock_session
        )
    
    # Assert
    assert result is mock_service
    mock_service_class.assert_called_once_with(
        entity_crud=mock_entity_crud,
        entity_relationship_crud=mock_entity_relationship_crud,
        session_factory=Any  # Lambda cannot be directly compared
    )
    
    # Verify the session factory works
    session_factory = mock_service_class.call_args[1]['session_factory']
    assert session_factory() is mock_session


def test_get_rss_feed_service():
    """Test the RSS feed service provider."""
    # Arrange
    mock_rss_feed_crud = MagicMock()
    mock_rss_parser = MagicMock()
    mock_article_service = MagicMock()
    mock_session = MagicMock()
    
    mock_service_class = MagicMock()
    mock_service = MagicMock()
    mock_service_class.return_value = mock_service
    
    # Act
    with patch('local_newsifier.di.providers.RSSFeedService', mock_service_class):
        result = get_rss_feed_service(
            rss_feed_crud=mock_rss_feed_crud,
            rss_parser=mock_rss_parser,
            article_service=mock_article_service,
            session=mock_session
        )
    
    # Assert
    assert result is mock_service
    mock_service_class.assert_called_once_with(
        rss_feed_crud=mock_rss_feed_crud,
        rss_parser=mock_rss_parser,
        article_service=mock_article_service,
        session_factory=Any  # Lambda cannot be directly compared
    )
    
    # Verify the session factory works
    session_factory = mock_service_class.call_args[1]['session_factory']
    assert session_factory() is mock_session


# Test a simplified service provider mechanism

def test_simplified_provider_pattern():
    """Test that the provider pattern works correctly."""
    # Import and patch the article service provider
    from local_newsifier.di.providers import get_article_service
    
    # Arrange
    mock_article_crud = MagicMock()
    mock_entity_crud = MagicMock()
    mock_session = MagicMock()
    
    mock_service_class = MagicMock()
    mock_service = MagicMock()
    mock_service_class.return_value = mock_service
    
    # Act
    with patch('local_newsifier.di.providers.ArticleService', mock_service_class):
        result = get_article_service(
            article_crud=mock_article_crud,
            entity_crud=mock_entity_crud,
            session=mock_session
        )
    
    # Assert
    assert result is mock_service
    mock_service_class.assert_called_once_with(
        article_crud=mock_article_crud,
        entity_crud=mock_entity_crud,
        session_factory=Any
    )
    
    # Verify the session factory works correctly
    session_factory = mock_service_class.call_args[1]['session_factory']
    assert callable(session_factory)
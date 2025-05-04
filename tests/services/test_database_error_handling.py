"""Tests for database error handling in services."""

import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from sqlalchemy.exc import OperationalError, IntegrityError
from local_newsifier.services.article_service import ArticleService
from local_newsifier.errors.error import ServiceError


def test_article_service_database_error_handling():
    """Test that database errors are properly handled in ArticleService."""
    # Mock dependencies
    article_crud = MagicMock()
    analysis_result_crud = MagicMock()
    session_factory = MagicMock()
    
    # Create ArticleService with mocked dependencies
    service = ArticleService(
        article_crud=article_crud,
        analysis_result_crud=analysis_result_crud,
        session_factory=session_factory
    )
    
    # Mock a database connection error
    mock_session = MagicMock()
    session_factory.return_value.__enter__.return_value = mock_session
    article_crud.get.side_effect = OperationalError(
        statement="SELECT * FROM articles", 
        params={}, 
        orig=Exception("connection error")
    )
    
    # Test that the error is properly handled and classified
    with pytest.raises(ServiceError) as exc_info:
        service.get_article(article_id=1)
    
    # Verify the error was properly classified
    assert exc_info.value.error_type == "connection"
    assert "database" in exc_info.value.service
    
    # Test with an integrity error
    article_crud.get.side_effect = IntegrityError(
        statement="INSERT INTO articles", 
        params={}, 
        orig=Exception("integrity error")
    )
    
    # Test that the error is properly handled and classified
    with pytest.raises(ServiceError) as exc_info:
        service.get_article(article_id=1)
    
    # Verify the error was properly classified
    assert exc_info.value.error_type == "integrity"
    assert "database" in exc_info.value.service


def test_create_article_from_rss_entry_error_handling():
    """Test error handling for create_article_from_rss_entry method."""
    # Mock dependencies
    article_crud = MagicMock()
    analysis_result_crud = MagicMock()
    session_factory = MagicMock()
    
    # Create ArticleService with mocked dependencies
    service = ArticleService(
        article_crud=article_crud,
        analysis_result_crud=analysis_result_crud,
        session_factory=session_factory
    )
    
    # Mock a database constraint error
    mock_session = MagicMock()
    session_factory.return_value.__enter__.return_value = mock_session
    article_crud.create.side_effect = IntegrityError(
        statement="INSERT INTO articles (url) VALUES ('http://example.com')", 
        params={}, 
        orig=Exception("duplicate key value violates unique constraint")
    )
    
    # Test method with error handling
    with pytest.raises(ServiceError) as exc_info:
        service.create_article_from_rss_entry({
            "title": "Test Article",
            "link": "http://example.com",
            "published": datetime.now(timezone.utc).isoformat(),
            "summary": "Test content"
        })
    
    # Verify error classification
    assert exc_info.value.error_type == "integrity"
    assert "database" in exc_info.value.service
    
    # Verify error message contains helpful information
    assert "constraint" in str(exc_info.value)
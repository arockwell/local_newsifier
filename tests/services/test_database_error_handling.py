"""Tests for database error handling in service layer."""

import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy.exc import (
    OperationalError, 
    IntegrityError,
    TimeoutError, 
    StatementError,
    InvalidRequestError
)
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

from local_newsifier.services.article_service import ArticleService
from local_newsifier.errors.error import ServiceError


def test_article_service_database_error_handling():
    """Test that the article service properly handles database errors."""
    # Mock dependencies
    article_crud = MagicMock()
    analysis_result_crud = MagicMock()
    session_factory = MagicMock()
    
    # Create a service with mocked dependencies
    service = ArticleService(
        article_crud=article_crud,
        analysis_result_crud=analysis_result_crud,
        session_factory=session_factory
    )
    
    # Mock session
    mock_session = MagicMock()
    session_factory.return_value.__enter__.return_value = mock_session
    
    # Test connection error
    article_crud.get.side_effect = OperationalError(
        statement="SELECT * FROM articles", 
        params={}, 
        orig=Exception("connection error")
    )
    
    with pytest.raises(ServiceError) as exc_info:
        service.get_article(article_id=1)
    
    error = exc_info.value
    assert error.service == "database"
    assert error.error_type == "connection"
    
    # Test integrity error
    article_crud.get.side_effect = IntegrityError(
        statement="INSERT INTO articles", 
        params={}, 
        orig=Exception("integrity error")
    )
    
    with pytest.raises(ServiceError) as exc_info:
        service.get_article(article_id=1)
    
    error = exc_info.value
    assert error.service == "database"
    assert error.error_type == "integrity"


def test_database_error_classification():
    """Test classification of various database error types."""
    # Mock dependencies
    article_crud = MagicMock()
    analysis_result_crud = MagicMock()
    session_factory = MagicMock()
    
    # Create a service with mocked dependencies
    service = ArticleService(
        article_crud=article_crud,
        analysis_result_crud=analysis_result_crud,
        session_factory=session_factory
    )
    
    # Mock session
    mock_session = MagicMock()
    session_factory.return_value.__enter__.return_value = mock_session
    
    # Test various error types
    test_cases = [
        # (exception, expected_error_type)
        (NoResultFound(), "not_found"),
        (MultipleResultsFound(), "multiple"),
        (TimeoutError("query timeout"), "timeout"),
        (StatementError("statement error", {}, None), "validation"),
        (InvalidRequestError("invalid request"), "transaction"),
    ]
    
    for exception, expected_type in test_cases:
        article_crud.get.side_effect = exception
        
        with pytest.raises(ServiceError) as exc_info:
            service.get_article(article_id=1)
        
        error = exc_info.value
        assert error.service == "database"
        assert error.error_type == expected_type, f"Expected {expected_type} for {type(exception).__name__}"


@patch('local_newsifier.errors.error.with_retry')
def test_retry_behavior(mock_with_retry):
    """Test that transient database errors are retried."""
    # Setup mock retry decorator that just returns the original function
    mock_with_retry.return_value = lambda f: f
    
    # Mock dependencies
    article_crud = MagicMock()
    analysis_result_crud = MagicMock()
    session_factory = MagicMock()
    
    # Create a service with mocked dependencies
    service = ArticleService(
        article_crud=article_crud,
        analysis_result_crud=analysis_result_crud,
        session_factory=session_factory
    )
    
    # Mock session
    mock_session = MagicMock()
    session_factory.return_value.__enter__.return_value = mock_session
    
    # Create a connection error (should be retried)
    article_crud.get.side_effect = OperationalError(
        statement="SELECT * FROM articles", 
        params={}, 
        orig=Exception("connection error")
    )
    
    # Should fail even with mocked retry
    with pytest.raises(ServiceError):
        service.get_article(article_id=1)
    
    # Verify that with_retry was called with retry_attempts=3 (default)
    mock_with_retry.assert_called_with(3)
"""Tests for database error handling in service layer."""

import pytest
from unittest.mock import MagicMock
from sqlalchemy.exc import OperationalError, IntegrityError

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
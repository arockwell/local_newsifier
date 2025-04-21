"""Tests for the EntityService."""

import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch

def test_process_article_entities():
    """Test the complete article entity processing flow using new tools."""
    # Arrange
    # Mock the new refactored tools
    mock_entity_extractor = MagicMock()
    mock_entity_extractor.extract_entities.return_value = [
            {
                "text": "John Doe", 
                "type": "PERSON", 
                "context": "John Doe visited the city.",
                "start_char": 0,
                "end_char": 8
            }
    ]
    
    mock_context_analyzer = MagicMock()
    mock_context_analyzer.analyze_context.return_value = {
        "sentiment": {"score": 0.5, "category": "positive"},
        "framing": {"category": "neutral"}
    }
    
    mock_entity_resolver = MagicMock()
    mock_entity_resolver.resolve_entity.return_value = {
        "name": "John Doe",
        "entity_type": "PERSON",
        "is_new": True,
        "confidence": 1.0,
        "original_text": "John Doe"
    }
    
    # Mock CRUD operations
    mock_entity_crud = MagicMock()
    mock_entity_crud.create.return_value = MagicMock(id=1)
    
    mock_canonical_entity_crud = MagicMock()
    mock_canonical_entity_crud.get_all.return_value = []
    mock_canonical_entity_crud.create.return_value = MagicMock(id=1)
    mock_canonical_entity_crud.create.return_value.name = "John Doe"
    
    mock_entity_mention_context_crud = MagicMock()
    mock_entity_profile_crud = MagicMock()
    
    # Mock session factory
    mock_session = MagicMock()
    mock_session_factory = MagicMock(return_value=MagicMock(__enter__=MagicMock(return_value=mock_session), __exit__=MagicMock()))
    
    # Create the service with mocks
    from local_newsifier.services.entity_service import EntityService
    service = EntityService(
        entity_crud=mock_entity_crud,
        canonical_entity_crud=mock_canonical_entity_crud,
        entity_mention_context_crud=mock_entity_mention_context_crud,
        entity_profile_crud=mock_entity_profile_crud,
        entity_extractor=mock_entity_extractor,
        context_analyzer=mock_context_analyzer,
        entity_resolver=mock_entity_resolver,
        session_factory=mock_session_factory
    )
    
    # Act
    result = service.process_article_entities(
        article_id=1,
        content="John Doe visited the city.",
        title="Test Article",
        published_at=datetime(2025, 1, 1)
    )
    
    # Assert
    # Verify tools were called correctly
    mock_entity_extractor.extract_entities.assert_called_once_with("John Doe visited the city.")
    mock_context_analyzer.analyze_context.assert_called_once_with("John Doe visited the city.")
    mock_entity_resolver.resolve_entity.assert_called_once()
    
    # Verify CRUD operations
    mock_canonical_entity_crud.get_all.assert_called_once()
    mock_canonical_entity_crud.create.assert_called_once()
    mock_entity_crud.create.assert_called_once()
    mock_entity_mention_context_crud.create.assert_called_once()
    
    # Verify result
    assert len(result) == 1
    assert result[0]["original_text"] == "John Doe"
    assert result[0]["canonical_name"] == "John Doe"
    assert result[0]["sentiment_score"] == 0.5

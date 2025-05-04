"""Test for handling empty content in EntityService."""

from unittest.mock import MagicMock, patch
from datetime import datetime

def test_process_article_with_empty_content():
    """Test handling of empty content."""
    # Arrange
    # Mock the entity extractor to return empty list for empty content
    mock_entity_extractor = MagicMock()
    mock_entity_extractor.extract_entities.return_value = []
    
    # Mock other dependencies
    mock_context_analyzer = MagicMock()
    mock_entity_resolver = MagicMock()
    
    mock_entity_crud = MagicMock()
    mock_canonical_entity_crud = MagicMock()
    mock_canonical_entity_crud.get_all.return_value = []
    
    mock_entity_mention_context_crud = MagicMock()
    mock_entity_profile_crud = MagicMock()
    mock_article_crud = MagicMock()
    
    # Mock session for container
    mock_session = MagicMock()
    mock_session_context = MagicMock()
    mock_session_context.__enter__ = MagicMock(return_value=mock_session)
    mock_session_context.__exit__ = MagicMock(return_value=None)
    
    # Create container mock
    mock_container = MagicMock()
    mock_container.get.return_value = mock_session_context
    
    # Create the service with mocks
    with patch('local_newsifier.database.session_utils.get_db_session', return_value=mock_session_context):
        from local_newsifier.services.entity_service import EntityService
        service = EntityService(
            entity_crud=mock_entity_crud,
            canonical_entity_crud=mock_canonical_entity_crud,
            entity_mention_context_crud=mock_entity_mention_context_crud,
            entity_profile_crud=mock_entity_profile_crud,
            article_crud=mock_article_crud,
            entity_extractor=mock_entity_extractor,
            context_analyzer=mock_context_analyzer,
            entity_resolver=mock_entity_resolver,
            container=mock_container
        )
        
        # Act
        # Test with empty content
        result = service.process_article_entities(
            article_id=1,
            content="",
            title="Empty Article",
            published_at=datetime(2025, 1, 1)
        )
        
        # Assert
        # Verify entity extractor was called with empty string
        mock_entity_extractor.extract_entities.assert_called_once_with("")
        
        # Verify no other processing occurred
        mock_context_analyzer.analyze_context.assert_not_called()
        mock_entity_resolver.resolve_entity.assert_not_called()
        mock_entity_crud.create.assert_not_called()
        mock_entity_mention_context_crud.create.assert_not_called()
        
        # Verify empty result
        assert len(result) == 0

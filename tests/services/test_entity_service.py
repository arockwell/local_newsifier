"""Unit tests for the EntityService."""

import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from local_newsifier.database.session_manager import SessionManager
from local_newsifier.services.entity_service import EntityService
from local_newsifier.models.entity_tracking import CanonicalEntity


class TestEntityService:
    """Test cases for the EntityService."""
    
    def test_init(self):
        """Test EntityService initialization."""
        # Test with a provided session manager
        session_manager = SessionManager()
        service = EntityService(session_manager=session_manager)
        assert service.session_manager == session_manager
        
        # Test with default session manager
        with patch('local_newsifier.services.entity_service.get_session_manager') as mock_get_sm:
            mock_session_manager = MagicMock()
            mock_get_sm.return_value = mock_session_manager
            service = EntityService()
            assert service.session_manager == mock_session_manager
    
    def test_resolve_entity_existing(self):
        """Test entity resolution with an existing entity."""
        # Arrange
        mock_session = MagicMock()
        mock_session_manager = MagicMock()
        mock_session_manager.session.return_value.__enter__.return_value = mock_session
        
        mock_canonical_entity_crud = MagicMock()
        mock_canonical_entity = MagicMock()
        mock_canonical_entity.dict.return_value = {
            'id': 1, 
            'name': 'Joe Biden', 
            'entity_type': 'PERSON'
        }
        mock_canonical_entity_crud.get_by_name.return_value = mock_canonical_entity
        
        # Act
        with patch('local_newsifier.services.entity_service.canonical_entity_crud', 
                  mock_canonical_entity_crud):
            service = EntityService(session_manager=mock_session_manager)
            result = service.resolve_entity('Joe Biden', 'PERSON')
        
        # Assert
        mock_canonical_entity_crud.get_by_name.assert_called_once_with(
            mock_session, name='Joe Biden', entity_type='PERSON'
        )
        assert result == {'id': 1, 'name': 'Joe Biden', 'entity_type': 'PERSON'}
    
    def test_resolve_entity_new(self):
        """Test entity resolution with a new entity."""
        # Arrange
        mock_session = MagicMock()
        mock_session_manager = MagicMock()
        mock_session_manager.session.return_value.__enter__.return_value = mock_session
        
        mock_canonical_entity_crud = MagicMock()
        mock_canonical_entity_crud.get_by_name.return_value = None
        
        mock_new_entity = MagicMock()
        mock_new_entity.dict.return_value = {
            'id': 1, 
            'name': 'New Person', 
            'entity_type': 'PERSON'
        }
        mock_canonical_entity_crud.create.return_value = mock_new_entity
        
        # Act
        with patch('local_newsifier.services.entity_service.canonical_entity_crud', 
                  mock_canonical_entity_crud):
            with patch('local_newsifier.services.entity_service.CanonicalEntity') as mock_entity_class:
                mock_entity_class.return_value = MagicMock()
                
                service = EntityService(session_manager=mock_session_manager)
                result = service.resolve_entity('New Person', 'PERSON')
        
        # Assert
        mock_canonical_entity_crud.get_by_name.assert_called_once_with(
            mock_session, name='New Person', entity_type='PERSON'
        )
        mock_canonical_entity_crud.create.assert_called_once()
        assert result == {'id': 1, 'name': 'New Person', 'entity_type': 'PERSON'}
    
    def test_track_entity(self):
        """Test tracking an entity."""
        # Arrange
        mock_session = MagicMock()
        mock_session_manager = MagicMock()
        mock_session_manager.session.return_value.__enter__.return_value = mock_session
        
        # Mock entity_service.resolve_entity to return a canonical entity
        mock_resolve_entity = {
            'id': 1, 
            'name': 'Joe Biden', 
            'entity_type': 'PERSON'
        }
        
        # Mock entity_crud.create
        mock_entity = MagicMock()
        mock_entity.id = 2
        mock_entity_crud = MagicMock()
        mock_entity_crud.create.return_value = mock_entity
        
        # Mock context crud
        mock_context_crud = MagicMock()
        
        # Mock the service's _update_entity_profile method
        mock_update_profile = MagicMock()
        
        # Act
        with patch('local_newsifier.services.entity_service.entity_crud', mock_entity_crud):
            with patch('local_newsifier.services.entity_service.entity_mention_context_crud', mock_context_crud):
                service = EntityService(session_manager=mock_session_manager)
                service.resolve_entity = MagicMock(return_value=mock_resolve_entity)
                service._update_entity_profile = mock_update_profile
                
                now = datetime.now(timezone.utc)
                result = service.track_entity(
                    article_id=123,
                    entity_text='Joe Biden',
                    entity_type='PERSON',
                    context_text='President Joe Biden spoke today.',
                    sentiment_score=0.2,
                    framing_category='political',
                    published_at=now
                )
        
        # Assert
        service.resolve_entity.assert_called_once_with('Joe Biden', 'PERSON')
        mock_entity_crud.create.assert_called_once()
        mock_context_crud.create.assert_called_once()
        mock_update_profile.assert_called_once_with(
            session=mock_session,
            canonical_entity_id=1,
            entity_text='Joe Biden',
            context_text='President Joe Biden spoke today.',
            sentiment_score=0.2,
            framing_category='political',
            published_at=now
        )
        
        assert result['entity_id'] == 2
        assert result['canonical_entity_id'] == 1
        assert result['original_text'] == 'Joe Biden'
        assert result['canonical_name'] == 'Joe Biden'
        assert result['context'] == 'President Joe Biden spoke today.'

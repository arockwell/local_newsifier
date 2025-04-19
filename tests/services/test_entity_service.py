"""Unit tests for the EntityService."""

import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from local_newsifier.database.session_manager import SessionManager
from local_newsifier.services.entity_service import EntityService
from local_newsifier.models.entity_tracking import CanonicalEntity


class TestEntityService:
    """Test cases for EntityService."""
    
    def test_init(self):
        """Test EntityService initialization."""
        # Test with a provided session manager
        session_manager = SessionManager()
        
        with patch('local_newsifier.services.entity_service.spacy.load') as mock_load:
            mock_nlp = MagicMock()
            mock_load.return_value = mock_nlp
            
            service = EntityService(session_manager=session_manager)
            assert service.session_manager == session_manager
            assert service.nlp == mock_nlp
        
        # Test with default session manager
        with patch('local_newsifier.services.entity_service.get_session_manager') as mock_get_sm:
            with patch('local_newsifier.services.entity_service.spacy.load') as mock_load:
                mock_session_manager = MagicMock()
                mock_get_sm.return_value = mock_session_manager
                mock_nlp = MagicMock()
                mock_load.return_value = mock_nlp
                
                service = EntityService()
                assert service.session_manager == mock_session_manager
                assert service.nlp == mock_nlp
    
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
    
    def test_get_entity_timeline(self):
        """Test getting entity timeline."""
        # Arrange
        mock_session = MagicMock()
        mock_session_manager = MagicMock()
        mock_session_manager.session.return_value.__enter__.return_value = mock_session
        
        mock_canonical_entity_crud = MagicMock()
        expected_timeline = [
            {
                'date': '2025-04-15',
                'article_id': 1,
                'article_title': 'Article 1',
                'sentiment_score': 0.3
            },
            {
                'date': '2025-04-16',
                'article_id': 2,
                'article_title': 'Article 2',
                'sentiment_score': -0.2
            }
        ]
        mock_canonical_entity_crud.get_entity_timeline.return_value = expected_timeline
        
        # Act
        with patch('local_newsifier.services.entity_service.canonical_entity_crud', 
                  mock_canonical_entity_crud):
            service = EntityService(session_manager=mock_session_manager)
            start_date = datetime(2025, 4, 15, tzinfo=timezone.utc)
            end_date = datetime(2025, 4, 20, tzinfo=timezone.utc)
            result = service.get_entity_timeline(
                entity_id=1,
                start_date=start_date,
                end_date=end_date
            )
        
        # Assert
        mock_canonical_entity_crud.get_entity_timeline.assert_called_once_with(
            mock_session,
            entity_id=1,
            start_date=start_date,
            end_date=end_date
        )
        assert result == expected_timeline
    
    def test_get_entity_sentiment_trend(self):
        """Test getting entity sentiment trend."""
        # Arrange
        mock_session = MagicMock()
        mock_session_manager = MagicMock()
        mock_session_manager.session.return_value.__enter__.return_value = mock_session
        
        mock_entity_mention_context_crud = MagicMock()
        expected_trend = [
            {
                'date': '2025-04-15',
                'average_sentiment': 0.3,
                'mention_count': 5
            },
            {
                'date': '2025-04-16',
                'average_sentiment': -0.2,
                'mention_count': 3
            }
        ]
        mock_entity_mention_context_crud.get_sentiment_trend.return_value = expected_trend
        
        # Act
        with patch('local_newsifier.services.entity_service.entity_mention_context_crud', 
                  mock_entity_mention_context_crud):
            service = EntityService(session_manager=mock_session_manager)
            start_date = datetime(2025, 4, 15, tzinfo=timezone.utc)
            end_date = datetime(2025, 4, 20, tzinfo=timezone.utc)
            result = service.get_entity_sentiment_trend(
                entity_id=1,
                start_date=start_date,
                end_date=end_date
            )
        
        # Assert
        mock_entity_mention_context_crud.get_sentiment_trend.assert_called_once_with(
            mock_session,
            entity_id=1,
            start_date=start_date,
            end_date=end_date
        )
        assert result == expected_trend
    
    def test_update_entity_profile_new(self):
        """Test updating entity profile when no profile exists."""
        # Arrange
        mock_session = MagicMock()
        mock_session_manager = MagicMock()
        
        mock_entity_profile_crud = MagicMock()
        mock_entity_profile_crud.get_by_entity.return_value = None
        
        # Act
        with patch('local_newsifier.services.entity_service.entity_profile_crud', 
                  mock_entity_profile_crud):
            with patch('local_newsifier.services.entity_service.EntityProfile') as mock_entity_profile:
                service = EntityService(session_manager=mock_session_manager)
                publish_date = datetime(2025, 4, 15, tzinfo=timezone.utc)
                
                service._update_entity_profile(
                    session=mock_session,
                    canonical_entity_id=1,
                    entity_text='Joe Biden',
                    context_text='President Joe Biden spoke today.',
                    sentiment_score=0.2,
                    framing_category='political',
                    published_at=publish_date
                )
        
        # Assert
        mock_entity_profile_crud.get_by_entity.assert_called_once_with(
            mock_session, entity_id=1
        )
        mock_entity_profile_crud.create.assert_called_once()
        
        # Verify that the EntityProfile was created with the correct data
        _, kwargs = mock_entity_profile.call_args
        profile_metadata = kwargs.get('profile_metadata', {})
        
        assert kwargs.get('canonical_entity_id') == 1
        assert kwargs.get('profile_type') == 'summary'
        assert 'Entity Joe Biden has been mentioned once.' in kwargs.get('content', '')
        assert profile_metadata.get('mention_count') == 1
        assert profile_metadata.get('contexts') == ['President Joe Biden spoke today.']
        assert profile_metadata.get('temporal_data') == {'2025-04-15': 1}
        assert profile_metadata.get('sentiment_scores', {}).get('latest') == 0.2
        assert profile_metadata.get('sentiment_scores', {}).get('average') == 0.2
        assert profile_metadata.get('framing_categories', {}).get('latest') == 'political'
        assert profile_metadata.get('framing_categories', {}).get('history') == ['political']
    
    def test_update_entity_profile_existing(self):
        """Test updating entity profile when a profile already exists."""
        # Arrange
        mock_session = MagicMock()
        mock_session_manager = MagicMock()
        
        mock_entity_profile_crud = MagicMock()
        mock_current_profile = MagicMock()
        mock_current_profile.profile_metadata = {
            'mention_count': 5,
            'contexts': ['Previous context 1', 'Previous context 2'],
            'temporal_data': {'2025-04-14': 2, '2025-04-15': 3},
            'sentiment_scores': {
                'latest': 0.1,
                'average': 0.15
            },
            'framing_categories': {
                'latest': 'economic',
                'history': ['economic', 'political', 'economic']
            }
        }
        mock_entity_profile_crud.get_by_entity.return_value = mock_current_profile
        
        # Act
        with patch('local_newsifier.services.entity_service.entity_profile_crud', 
                  mock_entity_profile_crud):
            with patch('local_newsifier.services.entity_service.EntityProfile') as mock_entity_profile:
                service = EntityService(session_manager=mock_session_manager)
                publish_date = datetime(2025, 4, 16, tzinfo=timezone.utc)
                
                service._update_entity_profile(
                    session=mock_session,
                    canonical_entity_id=1,
                    entity_text='Joe Biden',
                    context_text='President Joe Biden announced a new policy.',
                    sentiment_score=0.3,
                    framing_category='political',
                    published_at=publish_date
                )
        
        # Assert
        mock_entity_profile_crud.get_by_entity.assert_called_once_with(
            mock_session, entity_id=1
        )
        mock_entity_profile_crud.update_or_create.assert_called_once()
        
        # Verify that the EntityProfile was updated with the correct data
        _, kwargs = mock_entity_profile.call_args
        profile_metadata = kwargs.get('profile_metadata', {})
        
        assert kwargs.get('canonical_entity_id') == 1
        assert kwargs.get('profile_type') == 'summary'
        assert 'Entity Joe Biden has been mentioned 6 times.' in kwargs.get('content', '')
        assert profile_metadata.get('mention_count') == 6
        assert 'President Joe Biden announced a new policy.' in profile_metadata.get('contexts', [])
        assert profile_metadata.get('temporal_data', {}).get('2025-04-16') == 1
        assert profile_metadata.get('sentiment_scores', {}).get('latest') == 0.3
        # Average should be (0.15 + 0.3) / 2 = 0.225
        assert profile_metadata.get('sentiment_scores', {}).get('average') == 0.225
        assert profile_metadata.get('framing_categories', {}).get('latest') == 'political'
        assert 'political' in profile_metadata.get('framing_categories', {}).get('history', [])
        
    def test_process_article(self):
        """Test processing an article to extract and track entities."""
        # Arrange
        mock_session_manager = MagicMock()
        
        # Create mock service with mocked NLP
        with patch('local_newsifier.services.entity_service.spacy.load') as mock_load:
            # Mock spaCy functionality
            mock_nlp = MagicMock()
            mock_doc = MagicMock()
            mock_ent1 = MagicMock()
            mock_ent2 = MagicMock()
            mock_sent1 = MagicMock()
            mock_sent2 = MagicMock()
            
            # Setup first entity
            mock_ent1.label_ = "PERSON"
            mock_ent1.text = "Joe Biden"
            mock_ent1.sent = mock_sent1
            mock_sent1.text = "President Joe Biden spoke today."
            
            # Setup second entity
            mock_ent2.label_ = "PERSON"
            mock_ent2.text = "Kamala Harris"
            mock_ent2.sent = mock_sent2
            mock_sent2.text = "Vice President Kamala Harris attended the meeting."
            
            # Set up the document with entities
            mock_doc.ents = [mock_ent1, mock_ent2]
            mock_nlp.return_value = mock_doc
            mock_nlp.meta = {"name": "en_core_web_lg"}
            mock_load.return_value = mock_nlp
            
            # Create service and mock internal methods
            service = EntityService(session_manager=mock_session_manager)
            service.track_entity = MagicMock(side_effect=[
                # Result for Biden
                {
                    "entity_id": 1,
                    "canonical_entity_id": 101,
                    "original_text": "Joe Biden",
                    "canonical_name": "Joe Biden",
                    "context": "President Joe Biden spoke today."
                },
                # Result for Harris
                {
                    "entity_id": 2,
                    "canonical_entity_id": 102,
                    "original_text": "Kamala Harris",
                    "canonical_name": "Kamala Harris",
                    "context": "Vice President Kamala Harris attended the meeting."
                }
            ])
            
            # Mock context analyzer
            with patch('local_newsifier.tools.context_analyzer.ContextAnalyzer') as mock_ctx:
                mock_analyzer = MagicMock()
                mock_analyzer.analyze_context.side_effect = [
                    # Result for Biden
                    {
                        "sentiment": {"score": 0.5},
                        "framing": {"category": "leadership"}
                    },
                    # Result for Harris
                    {
                        "sentiment": {"score": 0.3},
                        "framing": {"category": "political"}
                    }
                ]
                mock_ctx.return_value = mock_analyzer
                
                # Act
                result = service.process_article(
                    article_id=1,
                    content="President Joe Biden spoke today. Vice President Kamala Harris attended the meeting.",
                    title="White House Meeting",
                    published_at=datetime.now(timezone.utc)
                )
        
        # Assert
        assert len(result) == 2
        assert result[0]["canonical_name"] == "Joe Biden"
        assert result[0]["sentiment_score"] == 0.5
        assert result[0]["framing_category"] == "leadership"
        assert result[1]["canonical_name"] == "Kamala Harris"
        assert result[1]["sentiment_score"] == 0.3
        assert result[1]["framing_category"] == "political"
        assert service.track_entity.call_count == 2

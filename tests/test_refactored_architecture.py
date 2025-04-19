"""Integration test for the refactored architecture."""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone

from local_newsifier.core.factory import ToolFactory, ServiceFactory
from local_newsifier.database.session_manager import get_session_manager
from local_newsifier.services.entity_service import EntityService
from local_newsifier.tools.entity_tracker_v2 import EntityTracker
from local_newsifier.flows.entity_tracking_flow_v2 import EntityTrackingFlow


class TestRefactoredArchitecture:
    """Test cases for the refactored architecture."""
    
    def test_factory_creates_components(self):
        """Test that factories correctly create components with dependencies."""
        # Get session manager
        session_manager = get_session_manager()
        
        # Create entity service
        entity_service = ServiceFactory.create_entity_service(
            session_manager=session_manager
        )
        assert isinstance(entity_service, EntityService)
        assert entity_service.session_manager == session_manager
        
        # Create entity tracker
        entity_tracker = ToolFactory.create_entity_tracker(
            session_manager=session_manager,
            entity_service=entity_service
        )
        assert isinstance(entity_tracker, EntityTracker)
        assert entity_tracker.session_manager == session_manager
        assert entity_tracker.entity_service == entity_service
        
        # Create entity tracking flow
        flow = EntityTrackingFlow(
            session_manager=session_manager,
            entity_tracker=entity_tracker
        )
        assert flow.session_manager == session_manager
        assert flow.entity_tracker == entity_tracker
    
    @patch('local_newsifier.services.entity_service.canonical_entity_crud')
    def test_entity_resolution(self, mock_canonical_entity_crud):
        """Test entity resolution through the service layer."""
        # Set up mock
        mock_entity = MagicMock()
        mock_entity.dict.return_value = {"id": 1, "name": "Joe Biden", "entity_type": "PERSON"}
        mock_canonical_entity_crud.get_by_name.return_value = mock_entity
        
        # Create service
        entity_service = EntityService()
        
        # Resolve entity
        result = entity_service.resolve_entity("Joe Biden", "PERSON")
        
        # Verify
        assert result == {"id": 1, "name": "Joe Biden", "entity_type": "PERSON"}
        mock_canonical_entity_crud.get_by_name.assert_called_once()
    
    @patch('local_newsifier.tools.entity_tracker_v2.EntityService')
    def test_entity_tracker_uses_service(self, mock_entity_service_class):
        """Test that entity tracker delegates to the service."""
        # Set up mock service
        mock_service = MagicMock()
        mock_service.track_entity.return_value = {
            "entity_id": 1,
            "canonical_entity_id": 2,
            "original_text": "Joe Biden",
            "canonical_name": "Joe Biden",
            "context": "President Joe Biden spoke today."
        }
        mock_entity_service_class.return_value = mock_service
        
        # Create tracker with mock service injected
        tracker = EntityTracker(entity_service=mock_service)
        
        # Process article with minimal content (just to test the interaction)
        with patch('local_newsifier.tools.entity_tracker_v2.spacy.load') as mock_load:
            # Mock minimal spaCy functionality for test
            mock_nlp = MagicMock()
            mock_doc = MagicMock()
            mock_ent = MagicMock()
            mock_sent = MagicMock()
            
            mock_ent.label_ = "PERSON"
            mock_ent.text = "Joe Biden"
            mock_ent.sent = mock_sent
            mock_sent.text = "President Joe Biden spoke today."
            mock_doc.ents = [mock_ent]
            mock_nlp.return_value = mock_doc
            mock_load.return_value = mock_nlp
            
            # Process article
            with patch('local_newsifier.tools.entity_tracker_v2.ContextAnalyzer') as mock_ctx_analyzer:
                mock_analyzer = MagicMock()
                mock_analyzer.analyze_context.return_value = {
                    "sentiment": {"score": 0.5},
                    "framing": {"category": "leadership"}
                }
                mock_ctx_analyzer.return_value = mock_analyzer
                
                result = tracker.process_article(
                    article_id=1,
                    content="President Joe Biden spoke today.",
                    title="Biden Speech",
                    published_at=datetime.now(timezone.utc)
                )
        
        # Verify service was called correctly
        assert len(result) == 1
        assert result[0]["canonical_name"] == "Joe Biden"
        mock_service.track_entity.assert_called_once()

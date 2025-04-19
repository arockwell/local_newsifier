"""Integration test for the refactored architecture."""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone

from local_newsifier.core.factory import ToolFactory, ServiceFactory
from local_newsifier.database.session_manager import get_session_manager
from local_newsifier.services.entity_service import EntityService
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
        
        # Create entity tracking flow
        flow = EntityTrackingFlow(
            session_manager=session_manager,
            entity_service=entity_service
        )
        assert flow.session_manager == session_manager
        assert flow.entity_service == entity_service
    
    @patch('local_newsifier.services.entity_service.canonical_entity_crud')
    def test_entity_resolution(self, mock_canonical_entity_crud):
        """Test entity resolution through the service layer."""
        # Set up mock
        mock_entity = MagicMock()
        mock_entity.dict.return_value = {"id": 1, "name": "Joe Biden", "entity_type": "PERSON"}
        mock_canonical_entity_crud.get_by_name.return_value = mock_entity
        
        # Create service with mocked spacy
        with patch('local_newsifier.services.entity_service.spacy.load'):
            entity_service = EntityService()
        
            # Resolve entity
            result = entity_service.resolve_entity("Joe Biden", "PERSON")
        
            # Verify
            assert result == {"id": 1, "name": "Joe Biden", "entity_type": "PERSON"}
            mock_canonical_entity_crud.get_by_name.assert_called_once()
    
    def test_entity_service_process_article(self):
        """Test that entity service can process an article."""
        # Create mock service
        with patch('local_newsifier.services.entity_service.spacy.load') as mock_load:
            # Mock spaCy functionality
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
            mock_nlp.meta = {"name": "en_core_web_lg"}
            mock_load.return_value = mock_nlp
            
            # Setup mocks for needed dependencies
            with patch('local_newsifier.services.entity_service.ContextAnalyzer') as mock_ctx_analyzer:
                with patch('local_newsifier.tools.context_analyzer.ContextAnalyzer') as mock_ctx_analyzer2:
                    mock_analyzer = MagicMock()
                    mock_analyzer.analyze_context.return_value = {
                        "sentiment": {"score": 0.5},
                        "framing": {"category": "leadership"}
                    }
                    mock_ctx_analyzer.return_value = mock_analyzer
                    mock_ctx_analyzer2.return_value = mock_analyzer
                    
                    # Mock entity service methods
                    entity_service = EntityService()
                    entity_service.track_entity = MagicMock(return_value={
                        "entity_id": 1,
                        "canonical_entity_id": 2,
                        "original_text": "Joe Biden",
                        "canonical_name": "Joe Biden",
                        "context": "President Joe Biden spoke today."
                    })
                    
                    # Process article
                    result = entity_service.process_article(
                        article_id=1,
                        content="President Joe Biden spoke today.",
                        title="Biden Speech",
                        published_at=datetime.now(timezone.utc)
                    )
        
        # Verify
        assert len(result) == 1
        assert result[0]["canonical_name"] == "Joe Biden"
        entity_service.track_entity.assert_called_once()

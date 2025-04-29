"""Test for entity relationship analysis in EntityService."""

from unittest.mock import MagicMock, patch
from datetime import datetime, timezone
from local_newsifier.models.state import EntityRelationshipState, TrackingStatus

def test_entity_relationship_with_complex_network():
    """Test identification of complex entity relationships."""
    # Arrange
    # Mock canonical entity CRUD
    mock_canonical_entity_crud = MagicMock()
    
    # Create a mock entity
    mock_entity = MagicMock(
        id=1, 
        name="Apple Inc.", 
        entity_type="ORGANIZATION"
    )
    mock_canonical_entity_crud.get.return_value = mock_entity
    
    # Create mock articles mentioning this entity
    mock_article1 = MagicMock(id=101)
    mock_article2 = MagicMock(id=102)
    mock_article3 = MagicMock(id=103)
    mock_canonical_entity_crud.get_articles_mentioning_entity.return_value = [
        mock_article1, mock_article2, mock_article3
    ]
    
    # Mock entity CRUD to return different entities for each article
    mock_entity_crud = MagicMock()
    # Article 1: Apple and Microsoft
    # Article 2: Apple, Microsoft, and Google
    # Article 3: Apple and Samsung
    mock_entity_crud.get_by_article.side_effect = [
        [
            MagicMock(text="Apple Inc.", entity_type="ORGANIZATION"),
            MagicMock(text="Microsoft", entity_type="ORGANIZATION")
        ],
        [
            MagicMock(text="Apple Inc.", entity_type="ORGANIZATION"),
            MagicMock(text="Microsoft", entity_type="ORGANIZATION"),
            MagicMock(text="Google", entity_type="ORGANIZATION")
        ],
        [
            MagicMock(text="Apple Inc.", entity_type="ORGANIZATION"),
            MagicMock(text="Samsung", entity_type="ORGANIZATION")
        ]
    ]
    
    # Mock canonical entity retrieval for co-occurring entities
    mock_canonical_entity_crud.get_by_name.side_effect = [
        MagicMock(id=2, name="Microsoft", entity_type="ORGANIZATION"),  # Article 1
        mock_entity,  # Article 1 - Apple (skipped)
        MagicMock(id=2, name="Microsoft", entity_type="ORGANIZATION"),  # Article 2
        mock_entity,  # Article 2 - Apple (skipped)
        MagicMock(id=3, name="Google", entity_type="ORGANIZATION"),     # Article 2
        MagicMock(id=4, name="Samsung", entity_type="ORGANIZATION"),    # Article 3
        mock_entity   # Article 3 - Apple (skipped)
    ]
    
    # Mock other dependencies
    mock_entity_mention_context_crud = MagicMock()
    mock_entity_profile_crud = MagicMock()
    mock_article_crud = MagicMock()
    
    mock_entity_extractor = MagicMock()
    mock_context_analyzer = MagicMock()
    mock_entity_resolver = MagicMock()
    
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
        
        # Create relationship state
        state = EntityRelationshipState(entity_id=1, days=30)
        
        # Act
        result_state = service.find_entity_relationships(state)
    
    # Assert
    # Verify success
    assert result_state.status == TrackingStatus.SUCCESS
    
    # Verify relationships data
    assert "relationship_data" in result_state.__dict__
    assert "relationships" in result_state.relationship_data
    
    # We should have 3 relationships (Microsoft, Google, Samsung)
    assert len(result_state.relationship_data["relationships"]) == 3
    
    # Microsoft should be first (appeared in 2 articles)
    assert "Microsoft" in str(result_state.relationship_data["relationships"][0]["entity_name"])
    assert result_state.relationship_data["relationships"][0]["co_occurrence_count"] == 2
    
    # Google and Samsung should each appear in 1 article
    google_relationship = next(r for r in result_state.relationship_data["relationships"] 
                           if "Google" in str(r["entity_name"]))
    assert google_relationship["co_occurrence_count"] == 1
    
    samsung_relationship = next(r for r in result_state.relationship_data["relationships"] 
                            if "Samsung" in str(r["entity_name"]))
    assert samsung_relationship["co_occurrence_count"] == 1

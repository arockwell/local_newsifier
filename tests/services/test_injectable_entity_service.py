"""Tests for the injectable entity service."""

import datetime
import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timezone

from local_newsifier.models.state import EntityTrackingState, TrackingStatus
from local_newsifier.services.injectable_entity_service import InjectableEntityService


def test_process_article_entities(patch_injectable_dependencies):
    """Test processing article entities with injectable dependencies."""
    # Get the mocks from the fixture
    mocks = patch_injectable_dependencies
    
    # Create the service - dependencies will be injected via monkeypatched providers
    service = InjectableEntityService(
        entity_crud=mocks["entity_crud"],
        canonical_entity_crud=mocks["canonical_entity_crud"],
        entity_mention_context_crud=mocks["entity_mention_context_crud"],
        entity_profile_crud=mocks["entity_profile_crud"],
        article_crud=mocks["article_crud"],
        entity_extractor=mocks["entity_extractor"],
        context_analyzer=mocks["context_analyzer"],
        entity_resolver=mocks["entity_resolver"],
        session=mocks["session"],
    )
    
    # Call the method under test
    result = service.process_article_entities(
        article_id=1,
        content="This is a test article about Test Entity.",
        title="Test Article",
        published_at=datetime.now(timezone.utc)
    )
    
    # Assertions
    assert len(result) == 1
    assert result[0]["original_text"] == "Test Entity"
    assert result[0]["canonical_name"] == "Test Entity"
    assert result[0]["canonical_id"] == 1
    
    # Verify mock calls
    mocks["entity_extractor"].extract_entities.assert_called_once()
    mocks["context_analyzer"].analyze_context.assert_called_once()
    mocks["entity_resolver"].resolve_entity.assert_called_once()
    mocks["canonical_entity_crud"].get_all.assert_called_once()
    mocks["entity_crud"].create.assert_called_once()
    mocks["entity_mention_context_crud"].create.assert_called_once()


def test_process_article_with_state(patch_injectable_dependencies):
    """Test processing an article with state tracking."""
    # Get the mocks from the fixture
    mocks = patch_injectable_dependencies
    
    # Create the service - dependencies will be injected via monkeypatched providers
    service = InjectableEntityService(
        entity_crud=mocks["entity_crud"],
        canonical_entity_crud=mocks["canonical_entity_crud"],
        entity_mention_context_crud=mocks["entity_mention_context_crud"],
        entity_profile_crud=mocks["entity_profile_crud"],
        article_crud=mocks["article_crud"],
        entity_extractor=mocks["entity_extractor"],
        context_analyzer=mocks["context_analyzer"],
        entity_resolver=mocks["entity_resolver"],
        session=mocks["session"],
    )
    
    # Create a state object
    state = EntityTrackingState(
        article_id=1,
        content="This is a test article about Test Entity.",
        title="Test Article",
        published_at=datetime.now(timezone.utc)
    )
    
    # Call the method under test
    result = service.process_article_with_state(state)
    
    # Assertions
    assert result.status == TrackingStatus.SUCCESS
    assert len(result.entities) == 1
    assert result.entities[0]["original_text"] == "Test Entity"
    assert result.entities[0]["canonical_name"] == "Test Entity"
    
    # Verify mock calls
    mocks["entity_extractor"].extract_entities.assert_called_once()
    mocks["article_crud"].update_status.assert_called_once_with(
        mocks["session"], article_id=1, status="entity_tracked"
    )


def test_process_articles_batch(patch_injectable_dependencies):
    """Test processing a batch of articles."""
    # Get the mocks from the fixture
    mocks = patch_injectable_dependencies
    
    # Setup additional mock responses
    mock_article = Mock(
        id=1, 
        content="Test content", 
        title="Test title", 
        url="https://example.com",
        published_at=datetime.now(timezone.utc)
    )
    mocks["article_crud"].get_by_status.return_value = [mock_article]
    
    # Create the service - dependencies will be injected via monkeypatched providers
    service = InjectableEntityService(
        entity_crud=mocks["entity_crud"],
        canonical_entity_crud=mocks["canonical_entity_crud"],
        entity_mention_context_crud=mocks["entity_mention_context_crud"],
        entity_profile_crud=mocks["entity_profile_crud"],
        article_crud=mocks["article_crud"],
        entity_extractor=mocks["entity_extractor"],
        context_analyzer=mocks["context_analyzer"],
        entity_resolver=mocks["entity_resolver"],
        session=mocks["session"],
    )
    
    # Create a batch state
    from local_newsifier.models.state import EntityBatchTrackingState
    state = EntityBatchTrackingState(status_filter="new")
    
    # Call the method under test
    result = service.process_articles_batch(state)
    
    # Assertions
    assert result.status == TrackingStatus.SUCCESS
    assert result.total_articles == 1
    assert result.error_count == 0
    assert len(result.processed_articles) == 1
    
    # Verify mock calls
    mocks["article_crud"].get_by_status.assert_called_once_with(mocks["session"], status="new")
    mocks["entity_extractor"].extract_entities.assert_called_once()
    mocks["article_crud"].update_status.assert_called_with(
        mocks["session"], article_id=1, status="entity_tracked"
    )